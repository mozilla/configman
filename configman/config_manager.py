# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function

import six
import sys
import os
import collections
import inspect
import os.path
import contextlib
import functools
import warnings

#==============================================================================
# for convenience define some external symbols here - some client modules may
# import these symbols from here rather than their origin definition location.
# PyFlakes may erroneously flag some of these as unused
from configman.commandline import (
    command_line
)
from configman.converters import (
    to_string_converters,
    to_str
)
from configman.config_exceptions import (
    NotAnOptionError,
)
from configman.config_file_future_proxy import (
    ConfigFileFutureProxy
)
from configman.def_sources import (
    setup_definitions,
)
from configman.dotdict import (
    DotDict,
    DotDictWithAcquisition,
)
from configman.environment import (
    environment
)
from configman.namespace import (
    Namespace
)
from configman.option import (
    Option,
    Aggregation
)

# RequiredConfig is not used directly in this file, but made available as
# a type to be imported from this module
from configman.required_config import (
    RequiredConfig
)
from configman.value_sources import (
    config_filename_from_commandline,
    wrap_with_value_source_api,
    dispatch_request_to_write,
    file_extension_dispatch,
    type_handler_dispatch
)


#==============================================================================
class ConfigurationManager(object):

    #--------------------------------------------------------------------------
    def __init__(
        self,
        definition_source=None,
        values_source_list=None,
        argv_source=None,
        #use_config_files=True,
        use_auto_help=True,
        use_admin_controls=True,
        quit_after_admin=True,
        options_banned_from_help=None,
        app_name='',
        app_version='',
        app_description='',
        config_pathname='.',
        config_optional=True,
        value_source_object_hook=DotDict,
    ):
        """create and initialize a configman object.

        parameters:
          definition_source - a namespace or list of namespaces from which
                              configman is to fetch the definitions of the
                              configuration parameters.
          values_source_list - (optional) a hierarchical list of sources for
                               values for the configuration parameters.
                               As values are copied from these sources,
                               conficting values are resolved with sources
                               on the right getting preference over sources on
                               the left.
          argv_source - if the values_source_list contains a commandline
                        source, this value is an alternative source for
                        actual command line arguments.  Useful for testing or
                        preprocessing command line arguments.
          use_auto_help - set to True if configman is to automatically set up
                          help output for command line invocations.
          use_admin_controls - configman can add command line flags that it
                               interprets independently of the app defined
                               arguments.  True enables this capability, while,
                               False supresses it.
          quit_after_admin - if True and admin controls are enabled and used,
                             call sys.exit to end the app.  This is useful to
                             stop the app from running if all that was done
                             was to write a config file or stop after help.
          options_banned_from_help - a list of strings that will censor the
                                     output of help to prevent specified
                                    options from being listed in the help
                                    output.  This is useful for hiding debug
                                    or secret command line arguments.
          app_name - assigns a name to the app.  This is used in help output
                     and as a default basename for config files.
          app_version - assigns a version for the app used help output.
          app_description - assigns a description for the app to be used in
                            the help output.
          config_pathname - a hard coded path to the directory of or the full
                            path and name of the configuration file.
          config_optional - a boolean indicating if a missing default config
                            file is optional.  Note: this is only for the
                            default config file.  If a config file is specified
                            on the commandline, it _must_ exist.
          value_source_object_hook - a class used for the internal
                                     representation of a value source.
                                     This is used to enable any special
                                     processing, like key translations.
                            """

        # instead of allowing mutables as default keyword argument values...
        if definition_source is None:
            definition_source_list = []
        elif (
            isinstance(definition_source, collections.Sequence) and
            not isinstance(definition_source, (six.binary_type, six.text_type))
        ):
            definition_source_list = list(definition_source)
        else:
            if isinstance(definition_source, (six.binary_type, six.text_type)):
                definition_source = to_str(definition_source)
            definition_source_list = [definition_source]

        if argv_source is None:
            self.argv_source = sys.argv[1:]
            self.app_invocation_name = sys.argv[0]
        else:
            self.argv_source = argv_source
            self.app_invocation_name = app_name
        if options_banned_from_help is None:
            options_banned_from_help = ['application']
        self.config_pathname = config_pathname
        self.config_optional = config_optional
        self.use_auto_help = use_auto_help

        self.value_source_object_hook = value_source_object_hook

        self.app_name = app_name
        self.app_version = app_version
        self.app_description = app_description

        self.args = []  # extra commandline arguments that are not switches
                        # will be stored here.

        self._config = None  # eventual container for DOM-like config object

        self.option_definitions = Namespace()
        self.definition_source_list = definition_source_list

        command_line_value_source = command_line
        if values_source_list is None:
            # nothing set, assume defaults
            if use_admin_controls:
                values_source_list = (
                    ConfigFileFutureProxy,
                    environment,
                    command_line_value_source
                )
            else:
                values_source_list = (
                    environment,
                    command_line_value_source
                )
        # determine which command_line facility to use for help
        if self.use_auto_help:
            # we need to iterate through all of our value sources looking for
            # one that can interact with the user on the commandline.
            for a_value_source in values_source_list:
                if inspect.ismodule(a_value_source):
                    handler = \
                        type_handler_dispatch[a_value_source][0].ValueSource
                    try:
                        # if a value source is able to handle the command line
                        # it will have defined 'command_line_value_source' as
                        # true.  Not all values sources may have this attribute
                        if handler.command_line_value_source:
                            handler._setup_auto_help(self)
                            break
                    except AttributeError:
                        # not a commandline source because it doesn't have
                        # the 'command_line_value_source' OR it doesn't have
                        # a method that allows it to setup a help system.
                        # this is OK, we can ignore it and move on until we
                        # find an appropriate source.
                        pass
                else:
                    # While not actually necessary to have implemented, this
                    # is the case where the value source is not a module.
                    # So we know nothing about its interface.  We cannot even
                    # try to use it as a commandline value source.
                    pass

        admin_tasks_done = False
        self.keys_blocked_from_output = [
            'help',
            'admin.conf',
            'admin.dump_conf',
            'admin.print_conf',
            'admin.strict',
            'admin.expose_secrets',
        ]
        self.options_banned_from_help = options_banned_from_help

        if use_admin_controls:
            admin_options = self._setup_admin_options(values_source_list)
            self.definition_source_list.append(admin_options)

        # iterate through the option definitions to create the nested dict
        # hierarchy of all the options called 'option_definitions'
        for a_definition_source in self.definition_source_list:
            try:
                safe_copy_of_def_source = a_definition_source.safe_copy()
            except AttributeError:
                # apparently, the definition source was not in the form of a
                # Namespace object.  This isn't a show stopper, but we don't
                # know how to make a copy of this object safely: we know from
                # experience that the stock copy.copy method leads to grief
                # as many sub-objects within an option definition source can
                # not be copied that way (classes, for example).
                # The only action we can take is to trust and continue with the
                # original copy of the definition source.
                safe_copy_of_def_source = a_definition_source
            setup_definitions(
                safe_copy_of_def_source,
                self.option_definitions
            )

        if use_admin_controls:
            # the name of the config file needs to be loaded from the command
            # line prior to processing the rest of the command line options.
            config_filename = config_filename_from_commandline(self)
            if (
                config_filename
                and ConfigFileFutureProxy in values_source_list
            ):
                self.option_definitions.admin.conf.default = config_filename

        self.values_source_list = wrap_with_value_source_api(
            values_source_list,
            self
        )

        known_keys = self._overlay_expand()
        self._check_for_mismatches(known_keys)

        # the app_name, app_version and app_description are to come from
        # if 'application' option if it is present. If it is not present,
        # get the app_name,et al, from parameters passed into the constructor.
        # if those are empty, set app_name, et al, to empty strings
        try:
            app_option = self._get_option('application')
            self.app_name = getattr(app_option.value, 'app_name', '')
            self.app_version = getattr(app_option.value, 'app_version', '')
            self.app_description = getattr(
                app_option.value,
                'app_description',
                ''
            )
        except NotAnOptionError:
            # there is no 'application' option, continue to use the
            # 'app_name' from the parameters passed in, if they exist.
            pass

        try:
            if use_auto_help and self._get_option('help').value:
                self.output_summary()
                admin_tasks_done = True
        except NotAnOptionError:
            # the current command-line implementation already has a help
            # mechanism of its own that doesn't require the use of a
            # option in configman.  This error is ignorable
            pass

        # keys that end with a "$" are called "blocked_by_suffix".
        # This means that these options are not to be written out to
        # configuration files.
        keys_blocked_by_suffix = [
            key
            for key in self.option_definitions.keys_breadth_first()
            if key.endswith('$')
        ]
        self.keys_blocked_from_output.extend(keys_blocked_by_suffix)

        if use_admin_controls and self._get_option('admin.print_conf').value:
            self.print_conf()
            admin_tasks_done = True

        if use_admin_controls and self._get_option('admin.dump_conf').value:
            self.dump_conf()
            admin_tasks_done = True

        if quit_after_admin and admin_tasks_done:
            sys.exit()

    #--------------------------------------------------------------------------
    @contextlib.contextmanager
    def context(self, mapping_class=DotDictWithAcquisition):
        """return a config as a context that calls close on every item when
        it goes out of scope"""
        config = None
        try:
            config = self.get_config(mapping_class=mapping_class)
            yield config
        finally:
            if config:
                self._walk_and_close(config)

    #--------------------------------------------------------------------------
    def get_config(self, mapping_class=DotDictWithAcquisition):
        config = self._generate_config(mapping_class)
        if self._aggregate(self.option_definitions, config, config):
            # state changed, must regenerate
            return self._generate_config(mapping_class)
        else:
            return config

    #--------------------------------------------------------------------------
    def output_summary(self, output_stream=sys.stdout):
        """outputs a usage tip and the list of acceptable commands.
        This is useful as the output of the 'help' option.

        parameters:
            output_stream - an open file-like object suitable for use as the
                            target of a print function
        """
        if self.app_name or self.app_description:
            print('Application: ', end='', file=output_stream)
        if self.app_name:
            print(self.app_name, self.app_version, file=output_stream)
        if self.app_description:
            print(self.app_description, file=output_stream)
        if self.app_name or self.app_description:
            print('', file=output_stream)

        names_list = self.get_option_names()
        print(
            "usage:\n%s [OPTIONS]... " % self.app_invocation_name,
            end='', file=output_stream
        )
        bracket_count = 0
        # this section prints the non-switch command line arguments
        for key in names_list:
            an_option = self.option_definitions[key]
            if an_option.is_argument:
                if an_option.default is None:
                    # there's no option, assume the user must set this
                    print(an_option.name, end='', file=output_stream)
                elif (
                    inspect.isclass(an_option.value)
                    or inspect.ismodule(an_option.value)
                ):
                    # this is already set and it could have expanded, most
                    # likely this is a case where a sub-command has been
                    # loaded and we're looking to show the help for it.
                    # display show it as a constant already provided rather
                    # than as an option the user must provide
                    print(an_option.default, end='', file=output_stream)
                else:
                    # this is an argument that the user may alternatively
                    # provide
                    print("[ %s" % an_option.name, end='', file=output_stream)
                    bracket_count += 1
        print(']' * bracket_count, '\n', file=output_stream)

        names_list.sort()
        if names_list:
            print('OPTIONS:', file=output_stream)

        pad = ' ' * 4

        for name in names_list:
            if name in self.options_banned_from_help:
                continue
            option = self._get_option(name)

            line = ' ' * 2  # always start with 2 spaces
            if option.short_form:
                line += '-%s, ' % option.short_form
            line += '--%s' % name
            line += '\n'

            doc = option.doc if option.doc is not None else ''
            if doc:
                line += '%s%s\n' % (pad, doc)
            try:
                value = option.value
                type_of_value = type(value)
                converter_function = to_string_converters[type_of_value]
                default = converter_function(value)
            except KeyError:
                default = option.value
            if default is not None:
                if (
                    (option.secret or 'password' in name.lower()) and
                    not self.option_definitions.admin.expose_secrets.default
                ):
                    default = '*********'
                if name not in ('help',):
                    # don't bother with certain dead obvious ones
                    line += '%s(default: %s)\n' % (pad, default)

            print(line, file=output_stream)

    #--------------------------------------------------------------------------
    def print_conf(self):
        """write a config file to the pathname specified in the parameter.  The
        file extention determines the type of file written and must match a
        registered type.

        parameters:
            config_pathname - the full path and filename of the target config
                               file."""

        config_file_type = self._get_option('admin.print_conf').value

        @contextlib.contextmanager
        def stdout_opener():
            yield sys.stdout

        skip_keys = [
            k for (k, v)
            in six.iteritems(self.option_definitions)
            if isinstance(v, Option) and v.exclude_from_print_conf
        ]
        self.write_conf(config_file_type, stdout_opener, skip_keys=skip_keys)

    #--------------------------------------------------------------------------
    def dump_conf(self, config_pathname=None):
        """write a config file to the pathname specified in the parameter.  The
        file extention determines the type of file written and must match a
        registered type.

        parameters:
            config_pathname - the full path and filename of the target config
                               file."""

        if not config_pathname:
            config_pathname = self._get_option('admin.dump_conf').value

        opener = functools.partial(open, config_pathname, 'w')
        config_file_type = os.path.splitext(config_pathname)[1][1:]

        skip_keys = [
            k for (k, v)
            in six.iteritems(self.option_definitions)
            if isinstance(v, Option) and v.exclude_from_dump_conf
        ]

        self.write_conf(config_file_type, opener, skip_keys=skip_keys)

    #--------------------------------------------------------------------------
    def write_conf(self, config_file_type, opener, skip_keys=None):
        """write a configuration file to a file-like object.

        parameters:
            config_file_type - a string containing a registered file type OR
                               a for_XXX module from the value_source
                               package.  Passing in an string that is
                               unregistered will result in a KeyError
            opener - a callable object or function that returns a file like
                     object that works as a context in a with statement."""

        blocked_keys = self.keys_blocked_from_output
        if skip_keys:
            blocked_keys.extend(skip_keys)

        if blocked_keys:
            option_defs = self.option_definitions.safe_copy()
            for a_blocked_key in blocked_keys:
                try:
                    del option_defs[a_blocked_key]
                except (AttributeError, KeyError):
                    # okay that key isn't here
                    pass
            # remove empty namespaces
            all_keys = [k for k in
                        option_defs.keys_breadth_first(include_dicts=True)]
            for key in all_keys:
                candidate = option_defs[key]
                if (isinstance(candidate, Namespace) and not len(candidate)):
                    del option_defs[key]
        else:
            option_defs = self.option_definitions

        # find all of the secret options and overwrite their values with
        # '*' * 16
        if not self.option_definitions.admin.expose_secrets.default:
            for a_key in option_defs.keys_breadth_first():
                an_option = option_defs[a_key]
                if (
                    (not a_key.startswith('admin'))
                    and isinstance(an_option, Option)
                    and an_option.secret
                ):
                    # force the option to be a string of *
                    option_defs[a_key].value = '*' * 16
                    option_defs[a_key].from_string_converter = str

        dispatch_request_to_write(config_file_type, option_defs, opener)

    #--------------------------------------------------------------------------
    def log_config(self, logger):
        """write out the current configuration to a log-like object.

        parameters:
            logger - a object that implements a method called 'info' with the
                     same semantics as the call to 'logger.info'"""

        logger.info("app_name: %s", self.app_name)
        logger.info("app_version: %s", self.app_version)
        logger.info("current configuration:")
        config = [(key, self.option_definitions[key].value)
                  for key in self.option_definitions.keys_breadth_first()
                  if key not in self.keys_blocked_from_output]
        config.sort()
        for key, val in config:
            if (
                self.option_definitions[key].secret
                or 'password' in key.lower()
            ):
                logger.info('%s: *********', key)
            else:
                try:
                    logger.info('%s: %s', key,
                                to_string_converters[type(key)](val))
                except KeyError:
                    logger.info('%s: %s', key, val)

    #--------------------------------------------------------------------------
    def get_option_names(self):
        """returns a list of fully qualified option names.

        returns:
            a list of strings representing the Options in the source Namespace
            list.  Each item will be fully qualified with dot delimited
            Namespace names.
        """
        return [x for x in self.option_definitions.keys_breadth_first()
                if isinstance(self.option_definitions[x], Option)]

    #--------------------------------------------------------------------------
    def _create_reference_value_options(self, keys, finished_keys):
        """this method steps through the option definitions looking for
        alt paths.  On finding one, it creates the 'reference_value_from' links
        within the option definitions and populates it with copied options."""
        # a set of known reference_value_from_links
        set_of_reference_value_option_names = set()
        for key in keys:
            if key in finished_keys:
                continue
            an_option = self.option_definitions[key]
            if an_option.reference_value_from:

                fully_qualified_reference_name = '.'.join((
                    an_option.reference_value_from,
                    an_option.name
                ))
                if fully_qualified_reference_name in keys:
                    continue  # this referenced value has already been defined
                              # no need to repeat it - skip on to the next key
                reference_option = an_option.copy()
                reference_option.reference_value_from = None
                reference_option.name = fully_qualified_reference_name
                # wait, aren't we setting a fully qualified dotted name into
                # the name field?  Yes, 'add_option' below sees that
                # full pathname and does the right thing with it to ensure
                # that the reference_option is created within the
                # correct namespace
                set_of_reference_value_option_names.add(
                    fully_qualified_reference_name
                )
                self.option_definitions.add_option(reference_option)

        for a_reference_value_option_name in set_of_reference_value_option_names:
            for x in range(a_reference_value_option_name.count('.')):
                namespace_path = \
                    a_reference_value_option_name.rsplit('.', x + 1)[0]
                self.option_definitions[namespace_path].ref_value_namespace()

        return set_of_reference_value_option_names

    #--------------------------------------------------------------------------
    def _overlay_expand(self):
        """This method overlays each of the value sources onto the default
        in each of the defined options.  It does so using a breadth first
        iteration, overlaying and expanding each level of the tree in turn.
        As soon as no changes were made to any level, the loop breaks and the
        work is done.  The actual action of the overlay is to take the value
        from the source and copy into the 'default' member of each Option
        object.

        "expansion" means converting an option value into its real type from
        string. The conversion is accomplished by simply calling the
        'set_value' method of the Option object.  If the resultant type has its
        own configuration options, bring those into the current namespace and
        then proceed to overlay/expand those.
        """
        new_keys_have_been_discovered = True  # loop control, False breaks loop
        finished_keys = set()
        all_reference_values = {}

        while new_keys_have_been_discovered:  # loop until nothing more is done
            # names_of_all_exsting_options holds a list of all keys in the
            # option definitons in breadth first order using this form:
            # [ 'x', 'y', 'z', 'x.a', 'x.b', 'z.a', 'z.b', 'x.a.j', 'x.a.k',
            # 'x.b.h']
            names_of_all_exsting_options = [
                x for x
                in self.option_definitions.keys_breadth_first()
                if isinstance(self.option_definitions[x], Option)
            ]
            new_keys_have_been_discovered = False  # setup to break loop

            # create alternate paths options
            set_of_reference_value_option_names = \
                self._create_reference_value_options(
                    names_of_all_exsting_options,
                    finished_keys
                )

            for a_ref_option_name in set_of_reference_value_option_names:
                if a_ref_option_name not in all_reference_values:
                    all_reference_values[a_ref_option_name] = []

            all_keys = list(set_of_reference_value_option_names) \
                + names_of_all_exsting_options

            # previous versions of this method pulled the values from the
            # values sources deeper within the following nested loops.
            # that was not necessary and caused a lot of redundant work.
            # the 'values_from_all_sources' now holds all the the values
            # from each of the value sources.
            values_from_all_sources = [
                a_value_source.get_values(
                    self,  # pass in the config_manager itself
                    True,  # ignore mismatches
                    self.value_source_object_hook  # build with this class
                )
                for a_value_source in self.values_source_list
            ]

            # overlay process:
            # fetch all the default values from the value sources before
            # applying the from string conversions

            for key in all_keys:
                if key in finished_keys:
                    continue
                #if not isinstance(an_option, Option):
                #   continue  # aggregations and other types are ignored
                # loop through all the value sources looking for values
                # that match this current key.
                if self.option_definitions[key].reference_value_from:
                    reference_value_from = (
                        self.option_definitions[key].reference_value_from
                    )
                    top_key = key.split('.')[-1]
                    self.option_definitions[key].default = (
                        self.option_definitions[reference_value_from]
                        [top_key].default
                    )
                    all_reference_values[
                        '.'.join((reference_value_from, top_key))
                    ].append(
                        key
                    )

                an_option = self.option_definitions[key]
                if key in all_reference_values:
                    # make sure that this value gets propagated to keys
                    # even if the keys have already been overlaid
                    finished_keys -= set(
                        all_reference_values[key]
                    )

                for val_src_dict in values_from_all_sources:
                    try:

                        # overlay the default with the new value from
                        # the value source.  This assignment may come
                        # via acquisition, so the key given may not have
                        # been an exact match for what was returned.
                        an_option.has_changed = (
                            an_option.default != val_src_dict[key]
                        )
                        an_option.default = val_src_dict[key]
                        if key in all_reference_values:
                            # make sure that this value gets propagated to keys
                            # even if the keys have already been overlaid
                            finished_keys -= set(
                                all_reference_values[key]
                            )
                    except KeyError as x:
                        pass  # okay, that source doesn't have this value

            # expansion process:
            # step through all the keys converting them to their proper
            # types and bringing in any new keys in the process
            for key in all_keys:
                if key in finished_keys:
                    continue
                # mark this key as having been seen and processed
                finished_keys.add(key)
                an_option = self.option_definitions[key]
                #if not isinstance(an_option, Option):
                #    continue  # aggregations, namespaces are ignored
                # apply the from string conversion to make the real value
                an_option.set_value(an_option.default)
                # new values have been seen, don't let loop break
                new_keys_have_been_discovered = True
                try:
                    try:
                        # try to fetch new requirements from this value
                        new_requirements = \
                            an_option.value.get_required_config()
                    except (AttributeError, KeyError):
                        new_requirements = getattr(
                            an_option.value,
                            'required_config',
                            None
                        )
                    # make sure what we got as new_req is actually a
                    # Mapping of some sort
                    if not isinstance(new_requirements, collections.Mapping):
                        # we didn't get a mapping, perhaps the option value
                        # was a Mock object - in any case we can't try to
                        # interpret 'new_req' as a configman requirement
                        # collection.  We must abandon processing this
                        # option further
                        continue
                    if not isinstance(new_requirements, Namespace):
                        new_requirements = Namespace(
                            initializer=new_requirements
                        )
                    # get the parent namespace
                    current_namespace = self.option_definitions.parent(key)
                    if current_namespace is None:
                        # we're at the top level, use the base namespace
                        current_namespace = self.option_definitions
                    if current_namespace._reference_value_from:
                        # don't expand things that are in reference value
                        # namespaces, they will be populated by expanding the
                        # targets
                        continue
                    # some new Options to be brought in may have already been
                    # seen and in the finished_keys set.  They must be reset
                    # as unfinished so that a new default doesn't permanently
                    # overwrite any of the values already placed by the
                    # overlays.  So we've got to remove those keys from the
                    # finished keys list.
                    # Before we can do that however, we need the fully
                    # qualified names for the new keys.
                    qualified_parent_name_list = key.rsplit('.', 1)
                    if len(qualified_parent_name_list) > 1:
                        qualified_parent_name = qualified_parent_name_list[0]
                    else:
                        qualified_parent_name = ''

                    finished_keys = finished_keys.difference(
                        '.'.join((qualified_parent_name, ref_option_name))
                        for ref_option_name in new_requirements
                    )
                    # add the new Options to the namespace
                    new_namespace = new_requirements.safe_copy(
                        an_option.reference_value_from
                    )

                    for new_key in new_namespace.keys_breadth_first():
                        if new_key not in current_namespace:
                            current_namespace[new_key] = new_namespace[new_key]
                except AttributeError as x:
                    # there are apparently no new Options to bring in from
                    # this option's value
                    pass
        return finished_keys

    #--------------------------------------------------------------------------
    def _check_for_mismatches(self, known_keys):
        """check for bad options from value sources"""
        for a_value_source in self.values_source_list:
            try:
                if a_value_source.always_ignore_mismatches:
                    continue
            except AttributeError:
                # ok, this values source doesn't have the concept
                # always igoring mismatches, we won't tolerate mismatches
                pass
            # we want to fetch the keys from the value sources so that we can
            # check for mismatches.  Commandline value sources, are different,
            # we never want to allow unmatched keys from the command line.
            # By detecting if this value source is a command line source, we
            # can employ the command line's own mismatch detection.  The
            # boolean 'allow_mismatches' controls application of the tollerance
            # for mismatches.
            if hasattr(a_value_source, 'command_line_value_source'):
                allow_mismatches = False
            else:
                allow_mismatches = True
            # make a set of all the keys from a value source in the form
            # of strings like this: 'x.y.z'
            value_source_mapping = a_value_source.get_values(
                self,
                allow_mismatches,
                self.value_source_object_hook
            )
            value_source_keys_set = set([
                k for k in
                DotDict(value_source_mapping).keys_breadth_first()
            ])
            # make a set of the keys that didn't match any of the known
            # keys in the requirements
            unmatched_keys = value_source_keys_set.difference(known_keys)
            # some of the unmatched keys may actually be ok because the were
            # used during acquisition.
            # remove keys of the form 'y.z' if they match a known key of the
            # form 'x.y.z'
            for key in unmatched_keys.copy():
                key_is_okay = six.moves.reduce(
                    lambda x, y: x or y,
                    (known_key.endswith(key) for known_key in known_keys)
                )
                if key_is_okay:
                    unmatched_keys.remove(key)
            # anything left in the unmatched_key set is a badly formed key.
            # issue a warning
            if unmatched_keys:
                if self.option_definitions.admin.strict.default:
                    # raise hell...
                    if len(unmatched_keys) > 1:
                        raise NotAnOptionError(
                            "%s are not valid Options" % unmatched_keys
                        )
                    elif len(unmatched_keys) == 1:
                        raise NotAnOptionError(
                            "%s is not a valid Option" % unmatched_keys.pop()
                        )
                else:
                    warnings.warn(
                        'Invalid options: %s' % ', '.join(sorted(unmatched_keys))
                    )

    #--------------------------------------------------------------------------
    @staticmethod
    def _walk_and_close(a_dict):
        for val in six.itervalues(a_dict):
            if isinstance(val, collections.Mapping):
                ConfigurationManager._walk_and_close(val)
            try:
                if hasattr(val, 'close') and not inspect.isclass(val):
                    val.close()
            except KeyError:
                # py3 will sometimes hit KeyError from the hasattr()
                pass

    #--------------------------------------------------------------------------
    def _generate_config(self, mapping_class):
        """This routine generates a copy of the DotDict based config"""
        config = mapping_class()
        self._walk_config_copy_values(
            self.option_definitions,
            config,
            mapping_class
        )
        return config

    #--------------------------------------------------------------------------
    def _setup_auto_help(self):
        help_option = Option(name='help', doc='print this', default=False)
        self.definition_source_list.append({'help': help_option})

    #--------------------------------------------------------------------------
    def _get_config_pathname(self):
        if os.path.isdir(self.config_pathname):
            # we've got a path with no file name at the end
            # use the appname as the file name and default to an 'ini'
            # config file type
            if self.app_name:
                return os.path.join(
                    self.config_pathname,
                    '%s.ini' % self.app_name
                )
            else:
                # there is no app_name yet
                # we'll decline to return anything
                return None
        return self.config_pathname

    #--------------------------------------------------------------------------
    def _setup_admin_options(self, values_source_list):
        base_namespace = Namespace()
        base_namespace.admin = admin = Namespace()
        admin.add_option(
            name='print_conf',
            default=None,
            doc='write current config to stdout (%s)'
                % ', '.join(file_extension_dispatch.keys())
        )
        admin.add_option(
            name='dump_conf',
            default='',
            doc='a pathname to which to write the current config',
        )
        admin.add_option(
            name='strict',
            default=False,
            doc='mismatched options generate exceptions rather'
                ' than just warnings'
        )
        admin.add_option(
            name='expose_secrets',
            default=False,
            doc='should options marked secret get written out or hidden?'
        )
        # only offer the config file admin options if they've been requested in
        # the values source list
        if ConfigFileFutureProxy in values_source_list:
            default_config_pathname = self._get_config_pathname()
            admin.add_option(
                name='conf',
                default=default_config_pathname,
                doc='the pathname of the config file (path/filename)',
            )
        return base_namespace

    #--------------------------------------------------------------------------
    def _walk_config_copy_values(self, source, destination, mapping_class):
        for key, val in source.items():
            if key.endswith('$'):
                continue
            value_type = type(val)
            if isinstance(val, Option) or isinstance(val, Aggregation):
                destination[key] = val.value
            elif value_type == Namespace:
                destination[key] = d = mapping_class()
                self._walk_config_copy_values(val, d, mapping_class)

    #--------------------------------------------------------------------------
    def _aggregate(self, source, base_namespace, local_namespace):
        aggregates_found = False
        for key, val in source.items():
            if isinstance(val, Namespace):
                new_aggregates_found = self._aggregate(
                    val,
                    base_namespace,
                    local_namespace[key]
                )
                aggregates_found = new_aggregates_found or aggregates_found
            elif isinstance(val, Aggregation):
                val.aggregate(base_namespace, local_namespace, self.args)
                aggregates_found = True
            # skip Options, we're only dealing with Aggregations
        return aggregates_found

    #--------------------------------------------------------------------------
    @staticmethod
    def _option_sort(x_tuple):
        key, val = x_tuple
        if isinstance(val, Namespace):
            return 'zzzzzzzzzzz%s' % key
        else:
            return key

    #--------------------------------------------------------------------------
    def _get_option(self, name):
        try:
            return self.option_definitions[name]
        except KeyError:
            raise NotAnOptionError('%s is not a known option name' % name)

    #--------------------------------------------------------------------------
    def _get_options(self, source=None, options=None, prefix=''):
        return [
            (key, self.option_definitions[key])
            for key in self.option_definitions.keys_breadth_first()
        ]
