# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is configman
#
# The Initial Developer of the Original Code is
# Mozilla Foundation
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#    K Lars Lohn, lars@mozilla.com
#    Peter Bengtsson, peterbe@mozilla.com
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

import sys
import os
import collections
import inspect
import os.path
import contextlib
import functools

import configman as cm
import converters as conv
import config_exceptions as exc
import value_sources
import def_sources

#==============================================================================
# for convenience define some external symbols here
from option import Option, Aggregation
from dotdict import DotDict, DotDictWithAcquisition
from namespace import Namespace
from config_file_future_proxy import ConfigFileFutureProxy
from required_config import RequiredConfig


#==============================================================================
class ConfigurationManager(object):

    #--------------------------------------------------------------------------
    def __init__(self,
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
                            on the commandline, it _must_ exsist."""
        # instead of allowing mutables as default keyword argument values...
        if definition_source is None:
            definition_source_list = []
        elif (isinstance(definition_source, collections.Sequence) and
              not isinstance(definition_source, basestring)):
            definition_source_list = list(definition_source)
        else:
            definition_source_list = [definition_source]

        if argv_source is None:
            argv_source = sys.argv[1:]
        if options_banned_from_help is None:
            options_banned_from_help = ['application']
        self.config_pathname = config_pathname
        self.config_optional = config_optional

        self.app_name = app_name
        self.app_version = app_version
        self.app_description = app_description

        self.args = []  # extra commandline arguments that are not switches
                        # will be stored here.

        self._config = None  # eventual container for DOM-like config object

        self.argv_source = argv_source
        self.option_definitions = Namespace()
        self.definition_source_list = definition_source_list

        if values_source_list is None:
            # nothing set, assume defaults
            if use_admin_controls:
                values_source_list = (cm.ConfigFileFutureProxy,
                                      cm.environment,
                                      cm.command_line)
            else:
                values_source_list = (cm.environment,
                                      cm.command_line)

        admin_tasks_done = False
        self.admin_controls_list = ['help',
                                    'admin.conf',
                                    'admin.dump_conf',
                                    'admin.print_conf',
                                    ]
        self.options_banned_from_help = options_banned_from_help

        if use_auto_help:
            self._setup_auto_help()
        if use_admin_controls:
            admin_options = self._setup_admin_options(values_source_list)
            self.definition_source_list.append(admin_options)

        # iterate through the option definitions to create the nested dict
        # hierarchy of all the options called 'option_definitions'
        for a_definition_source in self.definition_source_list:
            def_sources.setup_definitions(a_definition_source,
                                          self.option_definitions)

        if use_admin_controls:
            # the name of the config file needs to be loaded from the command
            # line prior to processing the rest of the command line options.
            config_filename = \
                value_sources.config_filename_from_commandline(self)
            if (config_filename
                and cm.ConfigFileFutureProxy in values_source_list
                ):
                self.option_definitions.admin.conf.default = config_filename

        self.values_source_list = value_sources.wrap(
            values_source_list,
            self
        )

        self._overlay_expand()

        # the app_name, app_version and app_description are to come from
        # if 'application' option if it is present. If it is not present,
        # get the app_name,et al, from parameters passed into the constructor.
        # if those are empty, set app_name, et al, to empty strings
        try:
            app_option = self._get_option('application')
            self.app_name = getattr(app_option.value, 'app_name', '')
            self.app_version = getattr(app_option.value, 'app_version', '')
            self.app_description = getattr(app_option.value,
                                           'app_description', '')
        except exc.NotAnOptionError:
            # there is no 'application' option, continue to use the
            # 'app_name' from the parameters passed in, if they exist.
            pass


        if use_auto_help and self._get_option('help').value:
            self.output_summary()
            admin_tasks_done = True

        if (use_admin_controls
            and self._get_option('admin.print_conf').value):
            self.print_conf()
            admin_tasks_done = True

        if (use_admin_controls
            and self._get_option('admin.dump_conf').value):
            self.dump_conf()
            admin_tasks_done = True

        if quit_after_admin and admin_tasks_done:
            sys.exit()

    #--------------------------------------------------------------------------
    @contextlib.contextmanager
    def context(self):
        """return a config as a context that calls close on every item when
        it goes out of scope"""
        config = None
        try:
            config = self.get_config()
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
    def output_summary(self,
                       output_stream=sys.stdout,
                       block_password=True):
        """outputs a usage tip and the list of acceptable commands.
        This is useful as the output of the 'help' option.

        parameters:
            output_stream - an open file-like object suitable for use as the
                            target of a print statement
            block_password - a boolean driving the use of a string of * in
                             place of the value for any object containing the
                             substring 'passowrd'
        """
        if self.app_name or self.app_description:
            print >> output_stream, 'Application:',
        if self.app_name:
            print >> output_stream, self.app_name, self.app_version
        if self.app_description:
            print >> output_stream, self.app_description
        if self.app_name or self.app_description:
            print >> output_stream, ''

        names_list = self.get_option_names()
        names_list.sort()
        if names_list:
            print >> output_stream, 'Options:'

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
                converter_function = conv.to_string_converters[type_of_value]
                default = converter_function(value)
            except KeyError:
                default = option.value
            if default is not None:
                if 'password' in name.lower():
                    default = '*********'
                if name not in ('help',):
                    # don't bother with certain dead obvious ones
                    line += '%s(default: %s)\n' % (pad, default)

            print >> output_stream, line

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

        skip_keys = [k for (k, v)
                     in self.option_definitions.iteritems()
                     if isinstance(v, Option) and v.exclude_from_print_conf]
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

        skip_keys = [k for (k, v)
                     in self.option_definitions.iteritems()
                     if isinstance(v, Option) and v.exclude_from_dump_conf]

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

        blocked_keys = self.admin_controls_list
        if skip_keys:
            blocked_keys.extend(skip_keys)

        option_iterator = functools.partial(self._walk_config,
                                       blocked_keys=blocked_keys)

        value_sources.write(config_file_type,
                            option_iterator,
                            opener)

    #--------------------------------------------------------------------------
    def log_config(self, logger):
        """write out the current configuration to a log-like object.

        parameters:
            logger - a object that implements a method called 'info' with the
                     same semantics as the call to 'logger.info'"""

        logger.info("app_name: %s", self.app_name)
        logger.info("app_version: %s", self.app_version)
        logger.info("current configuration:")
        config = [(qkey, val.value) for qkey, key, val in
                                    self._walk_config(self.option_definitions)
                                    if qkey not in self.admin_controls_list
                                       and not isinstance(val, Namespace)]
        config.sort()
        for key, val in config:
            if 'password' in key.lower():
                logger.info('%s: *********', key)
            else:
                try:
                    logger.info('%s: %s', key,
                                conv.to_string_converters[type(key)](val))
                except KeyError:
                    logger.info('%s: %s', key, val)

    #--------------------------------------------------------------------------
    def get_option_names(self, source=None, names=None, prefix=''):
        """returns a list of fully qualified option names.

        parameters:
            source - a sequence of Namespace of Options, usually not specified,
                     If not specified, the function will default to using the
                     internal list of Option definitions.
            names - a list to start with for appending the lsit Option names.
                    If ommited, the function will start with an empty list.

        returns:
            a list of strings representing the Options in the source Namespace
            list.  Each item will be fully qualified with dot delimited
            Namespace names.
        """
        if source is None:
            source = self.option_definitions
        if names is None:
            names = []
        for key, val in source.items():
            if isinstance(val, Namespace):
                new_prefix = '%s%s.' % (prefix, key)
                self.get_option_names(val, names, new_prefix)
            elif isinstance(val, Option):
                names.append("%s%s" % (prefix, key))
            # skip aggregations, we want only Options
        return names

    #--------------------------------------------------------------------------
    def _overlay_expand(self):
        """This method overlays each of the value sources onto the default
        in each of the defined options.  It does so using a breadth first
        iteration, overlaying and expanding each level of the tree in turn.
        As soon as no changes were made to any level, the loop breaks and the
        work is done.

        "expansion" means converting an option value into its real type from
        string. If the resultant type has its own configuration options, bring
        those into the current namespace and then proceed to overlay/expand
        those.
        """
        keys_have_been_processed = True  # loop control, False breaks the loop
        processed_keys = set()  # a set of keys that have been expanded

        while keys_have_been_processed:  # loop until nothing more is done
            # keys holds a list of all keys in the option definitons in
            # breadth first order using this form: [ 'x', 'y', 'z', 'x.a',
            # 'x.b', 'z.a', 'z.b', 'x.a.j', 'x.a.k', 'x.b.h']
            keys = [x for x in self.option_definitions.keys_breadth_first()]
            keys_have_been_processed = False  # setup to break loop

            # overlay process:
            # fetch all the default values from the value sources before
            # applying the from string conversions
            for key in keys:
                if key not in processed_keys:  # skip all keys previously seen
                    # loop through all the value sources looking for values
                    # that match this current key.
                    for a_value_source in self.values_source_list:
                        try:
                            # get all the option values from this value source
                            val_src_dict = a_value_source.get_values(
                                self,
                                True
                            )
                            # make sure it is in the form of a DotDict
                            if not isinstance(val_src_dict, DotDict):
                                val_src_dict = DotDict(val_src_dict)
                            # get the Option for this key
                            opt = self.option_definitions[key]
                            # overlay the default with the new value from
                            # the value source
                            opt.default = val_src_dict[key]
                        except KeyError:
                            pass  # okay, that source doesn't have this value

            # expansion process:
            # step through all the keys converting them to their proper
            # types and bringing in any new keys in the process
            for key in keys:
                if key not in processed_keys:  # skip all keys previously seen
                    an_option = self.option_definitions[key]
                    if isinstance(an_option, Aggregation):
                        continue  # aggregations are ignored
                    # apply the from string conversion to make the real value
                    an_option.set_value(an_option.default)
                    # mark this key as having been seen an processed
                    processed_keys.add(key)
                    # new values have been seen, don't let loop break
                    keys_have_been_processed = True
                    try:
                        # try to fetch new requirements from this value
                        new_req = an_option.value.get_required_config()
                        # get the parent namespace
                        current_namespace = self.option_definitions.parent(key)
                        if current_namespace is None:
                            # we're at the top level, use the base namespace
                            current_namespace = self.option_definitions
                        # add the new Options to the namespace
                        current_namespace.update(new_req.safe_copy())
                    except AttributeError, x:
                        # there are apparently no new Options to bring in from
                        # this option's value
                        pass

        # check for bad options from value sources:
        for a_value_source in self.values_source_list:
            try:
                if a_value_source.always_ignore_mismatches:
                    continue
            except AttributeError:
                # ok, this values source doesn't have the concept
                pass
            value_source_mapping = a_value_source.get_values(self, True)
            value_source_keys_set = set([
                k for k in
                DotDict(value_source_mapping).keys_breadth_first()
            ])
            unmatched_keys = value_source_keys_set.difference(processed_keys)
            if unmatched_keys:
                if len(unmatched_keys) > 1:
                    raise exc.NotAnOptionError(
                        "%s are not valid Options" % unmatched_keys
                    )
                else:
                    raise exc.NotAnOptionError(
                        "%s is not a valid Option" % unmatched_keys.pop()
                    )

    #--------------------------------------------------------------------------
    @staticmethod
    def _walk_and_close(a_dict):
        for val in a_dict.itervalues():
            if isinstance(val, collections.Mapping):
                ConfigurationManager._walk_and_close(val)
            if hasattr(val, 'close') and not inspect.isclass(val):
                val.close()

    #--------------------------------------------------------------------------
    def _generate_config(self, mapping_class):
        """This routine generates a copy of the DotDict based config"""
        config = mapping_class()
        self._walk_config_copy_values(self.option_definitions,
                                      config,
                                      mapping_class)
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
                return os.path.join(self.config_pathname,
                                    '%s.ini' % self.app_name)
            else:
                # there is no app_name yet
                # we'll punt and use 'config'
                return None
        return self.config_pathname

    #--------------------------------------------------------------------------
    def _setup_admin_options(self, values_source_list):
        base_namespace = Namespace()
        base_namespace.admin = admin = Namespace()
        admin.add_option(name='print_conf',
                         default=None,
                         doc='write current config to stdout (%s)'
                             % ', '.join(
                              value_sources.file_extension_dispatch.keys())
                         )
        admin.add_option(name='dump_conf',
                         default='',
                         doc='a pathname to which to write the current config',
                         )
        # only offer the config file admin options if they've been requested in
        # the values source list
        if ConfigFileFutureProxy in values_source_list:
            default_config_pathname = self._get_config_pathname()
            admin.add_option(name='conf',
                             default=default_config_pathname,
                             doc='the pathname of the config file '
                                 '(path/filename)',
                             )
        return base_namespace

    #--------------------------------------------------------------------------
    def _walk_config_copy_values(self, source, destination, mapping_class):
        for key, val in source.items():
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
                new_aggregates_found = self._aggregate(val,
                                                       base_namespace,
                                                       local_namespace[key])
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
    @staticmethod
    def _block_password(qkey, key, value, block_password=True):
        if block_password and 'password' in key.lower():
            value = '*********'
        return qkey, key, value

    #--------------------------------------------------------------------------
    def _walk_config(self, source=None, prefix='', blocked_keys=(),
                    block_password=False):
        if source == None:
            source = self.option_definitions
        options_list = source.items()
        options_list.sort(key=ConfigurationManager._option_sort)
        for key, val in options_list:
            qualified_key = '%s%s' % (prefix, key)
            if qualified_key in blocked_keys:
                continue
            if isinstance(val, Option):
                yield self._block_password(qualified_key, key, val,
                                          block_password)
            if isinstance(val, Aggregation):
                yield qualified_key, key, val
            elif isinstance(val, Namespace):
                if qualified_key == 'admin':
                    continue
                yield qualified_key, key, val
                new_prefix = '%s%s.' % (prefix, key)
                for xqkey, xkey, xval in self._walk_config(val,
                                                          new_prefix,
                                                          blocked_keys,
                                                          block_password):
                    yield xqkey, xkey, xval

    #--------------------------------------------------------------------------
    def _get_option(self, name):
        source = self.option_definitions
        try:
            for sub_name in name.split('.'):
                candidate = source[sub_name]
                if isinstance(candidate, Option):
                    return candidate
                else:
                    source = candidate
        except KeyError:
            pass  # we need to raise the exception below in either case
                  # of a key error or execution falling through the loop
        raise exc.NotAnOptionError('%s is not a known option name' % name)

    #--------------------------------------------------------------------------
    def _get_options(self, source=None, options=None, prefix=''):
        if source is None:
            source = self.option_definitions
        if options is None:
            options = []
        for key, val in source.items():
            if isinstance(val, Namespace):
                new_prefix = '%s%s.' % (prefix, key)
                self._get_options(val, options, new_prefix)
            else:
                options.append(("%s%s" % (prefix, key), val))
        return options
