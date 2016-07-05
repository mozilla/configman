# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""this module introduces support for argparse as a data definition source
for configman.  Rather than write using configman's data definition language,
programs can instead use the familiar argparse method."""
from __future__ import absolute_import, division, print_function

import argparse
import inspect
from os import environ
from functools import partial
import six

from configman.namespace import Namespace
from configman.config_file_future_proxy import ConfigFileFutureProxy
from configman.dotdict import (
    DotDict,
    iteritems_breadth_first,
    create_key_translating_dot_dict
)
from configman.converters import (
    str_to_instance_of_type_converters,
    str_to_list,
    boolean_converter,
    to_str,
    CannotConvertError
)


#-----------------------------------------------------------------------------
# horrors
# argparse is not very friendly toward extension in this manner.  In order to
# fully exploit argparse, it is necessary to reach inside it to examine some
# of its internal structures that are not intended for external use.  These
# invasive methods are restricted to read-only.
#------------------------------------------------------------------------------
def find_action_name_by_value(registry, target_action_instance):
    """the association of a name of an action class with a human readable
    string is exposed externally only at the time of argument definitions.
    This routine, when given a reference to argparse's internal action
    registry and an action, will find that action and return the name under
    which it was registered.
    """
    target_type = type(target_action_instance)
    for key, value in six.iteritems(registry['action']):
        if value is target_type:
            if key is None:
                return 'store'
            return key
    return None


#------------------------------------------------------------------------------
def get_args_and_values(parser, an_action):
    """this rountine attempts to reconstruct the kwargs that were used in the
    creation of an action object"""
    args = inspect.getargspec(an_action.__class__.__init__).args
    kwargs = dict(
        (an_attr, getattr(an_action, an_attr))
        for an_attr in args
        if (
            an_attr not in ('self', 'required')
            and getattr(an_action, an_attr) is not None
        )
    )
    action_name = find_action_name_by_value(
        parser._optionals._registries,
        an_action
    )
    if 'required' in kwargs:
        del kwargs['required']
    kwargs['action'] = action_name
    if 'option_strings' in kwargs:
        args = tuple(kwargs['option_strings'])
        del kwargs['option_strings']
    else:
        args = ()
    return args, kwargs


#==============================================================================
class SubparserFromStringConverter(object):
    """this class serves as both a repository of namespace sets corresponding
    with subparsers, and a from string converer. It is used in configman as the
    from_string_converter for the Option that corresponds with the subparser
    argparse action.  Once configman as assigned the final value to the
    subparser, it leaves an instance of the SebparserValue class as the default
    for the subparser configman option.  A deriviative of a string, this class
    also contains the configman required config corresponding to the actions
    of the subparsers."""
    #--------------------------------------------------------------------------
    def __init__(self):
        self.namespaces = {}

    #--------------------------------------------------------------------------
    def add_namespace(self, name, a_namespace):
        """as we build up argparse, the actions that define a subparser are
        translated into configman options.  Each of those options must be
        tagged with the value of the subparse to which they correspond."""
        # save a local copy of the namespace
        self.namespaces[name] = a_namespace
        # iterate through the namespace branding each of the options with the
        # name of the subparser to which they belong
        for k in a_namespace.keys_breadth_first():
            an_option = a_namespace[k]
            if not an_option.foreign_data:
                an_option.foreign_data = DotDict()
            an_option.foreign_data['argparse.owning_subparser_name'] = name

    #--------------------------------------------------------------------------
    def __call__(self, subparser_name):
        """As an instance of this class must serve as a from_string_converter,
        it must behave like a function.  This method gives an instance of this
        class function semantics"""
        #======================================================================
        class SubparserValue(str):
            """Instances of this class/closure serve as the value given out as
            the final value of the subparser configman option.  It is a string,
            that also has a 'get_required_config' method that can bring in the
            the arguments defined in the subparser in the local namespace.
            The mechanism works in the same manner that configman normally does
            expansion of dynamically loaded classes."""
            required_config = Namespace()
            try:
                # define the class dynamically, giving it the required_config
                # that corresponds with the confiman options defined for the
                # subparser of the same name.
                required_config = self.namespaces[subparser_name]
            except KeyError:
                raise CannotConvertError(
                    '%s is not a known sub-command' % subparser_name
                )

            #------------------------------------------------------------------
            def __new__(cls):
                """deriving from string is tricky business.  You cannot set the
                value in an __init__ method because strings are immutable and
                __init__ time is too late.  The 'new' method is the only chance
                to properly set the value."""
                obj = str.__new__(cls, subparser_name)
                return obj

            #------------------------------------------------------------------
            def get_required_config(self):
                return self.required_config

            #------------------------------------------------------------------
            def to_str(self):
                return subparser_name
        # instantiate the class and return it.  It will be assigned as the
        # value for the configman option corresponding with the subparser
        return SubparserValue()


#==============================================================================
class ConfigmanSubParsersAction(argparse._SubParsersAction):
    """this is a derivation of the argpares _SubParsersAction action.  We
    require its use over the default _SubParsersAction because we need to
    preserve the original args & kwargs that created it.  They will be used
    in a later phase of configman to perfectly reproduce the object without
    having to resort to a copy."""
    #--------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        self.original_args = args
        self.original_kwargs = kwargs
        super(ConfigmanSubParsersAction, self).__init__(*args, **kwargs)

    #--------------------------------------------------------------------------
    def add_parser(self, *args, **kwargs):
        """each time a subparser action is used to create a new parser object
        we must save the original args & kwargs.  In a later phase of
        configman, we'll need to reproduce the subparsers exactly without
        resorting to copying.  We save the args & kwargs in the 'foreign_data'
        section of the configman option that corresponds with the subparser
        action."""
        command_name = args[0]
        new_kwargs = kwargs.copy()
        new_kwargs['configman_subparsers_option'] = self._configman_option
        new_kwargs['subparser_name'] = command_name
        subparsers = self._configman_option.foreign_data.argparse.subparsers
        a_subparser = super(ConfigmanSubParsersAction, self).add_parser(
            *args,
            **new_kwargs
        )
        subparsers[command_name] = DotDict({
            "args": args,
            "kwargs": new_kwargs,
            "subparser": a_subparser
        })
        return a_subparser

    #--------------------------------------------------------------------------
    def add_configman_option(self, an_option):
        self._configman_option = an_option


#==============================================================================
class ArgumentParser(argparse.ArgumentParser):
    """this subclass of the standard argparse parser to be used as a drop in
    replacement for argparse.ArgumentParser.  It hijacks the standard
    parsing methods and hands off to configman.  Configman then calls back
    to the standard argparse base class to actually do the work, intercepting
    the final output do its overlay magic. The final result is not an
    argparse Namespace object, but a configman DotDict.  This means that it
    is functionlly equivalent to the argparse Namespace with the additional
    benefit of being compliant with the collections.Mapping abstract base
    class."""
    #--------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        self.original_args = args
        self.original_kwargs = kwargs.copy()
        self.version = kwargs.get("version")  # py3 argparse doesn't define
        kwargs['add_help'] = False  # stop help, reintroduce it later
        self.subparser_name = kwargs.pop('subparser_name', None)
        self.configman_subparsers_option = kwargs.pop(
            'configman_subparsers_option',
            None
        )
        super(ArgumentParser, self).__init__(*args, **kwargs)
        self.value_source_list = [environ, ConfigFileFutureProxy, argparse]
        self.required_config = Namespace()

    #--------------------------------------------------------------------------
    def get_required_config(self):
        """because of the exsistance of subparsers, the configman options
        that correspond with argparse arguments are not a constant.  We need
        to produce a copy of the namespace rather than the actual embedded
        namespace."""
        required_config = Namespace()
        # add current options to a copy of required config
        for k, v in iteritems_breadth_first(self.required_config):
            required_config[k] = v
        # get any option found in any subparsers
        try:
            subparser_namespaces = (
                self.configman_subparsers_option.foreign_data
                .argparse.subprocessor_from_string_converter
            )
            subparsers = (
                self._argparse_subparsers._configman_option.foreign_data
                .argparse.subparsers
            )
            # each subparser needs to have its configman options set up
            # in the subparser's configman option.  This routine copies
            # the required_config of each subparser into the
            # SubparserFromStringConverter defined above.
            for subparser_name, subparser_data in six.iteritems(subparsers):
                subparser_namespaces.add_namespace(
                    subparser_name,
                    subparser_data.subparser.get_required_config()
                )
        except AttributeError:
            # there is no subparser
            pass
        return required_config

    #--------------------------------------------------------------------------
    def add_argument(self, *args, **kwargs):
        """this method overrides the standard in order to create a parallel
        argument system in both the argparse and configman worlds.  Each call
        to this method returns a standard argparse Action object as well as
        adding an equivalent configman Option object to the required_config
        for this object.  The original args & kwargs that defined an argparse
        argument are preserved in the 'foreign_data' section of the
        corresponding configman Option."""
        # pull out each of the argument definition components from the args
        # so that we can deal with them one at a time in a well labeled manner
        # In this section, variables beginning with the prefix "argparse" are
        # values that define Action object.  Variables that begin with
        # "configman" are the arguments to create configman Options.
        argparse_action_name = kwargs.get('action', None)
        argparse_dest = kwargs.get('dest', None)
        argparse_const = kwargs.get('const', None)
        argparse_default = kwargs.get('default', None)
        if argparse_default is argparse.SUPPRESS:
            # we'll be forcing all options to have the attribute of
            # argparse.SUPPRESS later.  It's our way of making sure that
            # argparse returns only values that the user explicitly added to
            # the command line.
            argparse_default = None
        argparse_nargs = kwargs.get('nargs', None)
        argparse_type = kwargs.get('type', None)
        argparse_suppress_help = kwargs.pop('suppress_help', False)
        if argparse_suppress_help:
            configman_doc = kwargs.get('help', '')
            kwargs['help'] = argparse.SUPPRESS
        else:
            argparse_help = kwargs.get('help', '')
            if argparse_help == argparse.SUPPRESS:
                configman_doc = ''
            else:
                configman_doc = argparse_help

        # we need to make sure that all arguments that the user has not
        # explicily set on the command line have this attribute.  This means
        # that when the argparse parser returns the command line values, it
        # will not return values that the user did not mention on the command
        # line.  The defaults that otherwise would have been returned will be
        # handled by configman.
        kwargs['default'] = argparse.SUPPRESS
        # forward all parameters to the underlying base class to create a
        # normal argparse action object.
        an_action = super(ArgumentParser, self).add_argument(
            *args,
            **kwargs
        )
        argparse_option_strings = an_action.option_strings

        # get a human readable string that identifies the type of the argparse
        # action class that was created
        if argparse_action_name is None:
            argparse_action_name = find_action_name_by_value(
                self._optionals._registries,
                an_action
            )

        configman_is_argument = False

        # each of argparse's Action types must be handled separately.
        #--------------------------------------------------------------------
        # STORE
        if argparse_action_name == 'store':
            if argparse_dest is None:
                configman_name, configman_is_argument = self._get_option_name(
                    args
                )
                if not configman_name:
                    configman_name = args[0]
            else:
                configman_name = argparse_dest
                configman_is_argument = not argparse_option_strings
            configman_default = argparse_default
            if argparse_nargs and argparse_nargs in "1?":
                if argparse_type:
                    configman_from_string = argparse_type
                elif argparse_default:
                    configman_from_string = (
                        str_to_instance_of_type_converters.get(
                            type(argparse_default),
                            str
                        )
                    )
                else:
                    configman_from_string = str
            elif argparse_nargs and argparse_type:
                configman_from_string = partial(
                    str_to_list,
                    item_converter=argparse_type,
                    item_separator=' ',
                )
            elif argparse_nargs and argparse_default:
                configman_from_string = partial(
                    str_to_list,
                    item_converter=str_to_instance_of_type_converters.get(
                        type(argparse_default),
                        str
                    ),
                    item_separator=' ',
                )
            elif argparse_nargs:
                configman_from_string = partial(
                    str_to_list,
                    item_converter=str,
                    item_separator=' ',
                )
            elif argparse_type:
                configman_from_string = argparse_type
            elif argparse_default:
                configman_from_string = str_to_instance_of_type_converters.get(
                    type(argparse_default),
                    str
                )
            else:
                configman_from_string = str
            configman_to_string = to_str

        #--------------------------------------------------------------------
        # STORE_CONST
        elif (
            argparse_action_name == 'store_const'
            or argparse_action_name == 'count'
        ):
            if argparse_dest is None:
                configman_name, configman_is_argument = self._get_option_name(
                    args
                )
                if not configman_name:
                    configman_name = args[0]
            else:
                configman_name = argparse_dest
            configman_default = argparse_default
            if argparse_type:
                configman_from_string = argparse_type
            else:
                configman_from_string = str_to_instance_of_type_converters.get(
                    type(argparse_const),
                    str
                )
            configman_to_string = to_str

        #--------------------------------------------------------------------
        # STORE_TRUE /  STORE_FALSE
        elif (
            argparse_action_name == 'store_true'
            or argparse_action_name == 'store_false'
        ):
            if argparse_dest is None:
                configman_name, configman_is_argument = self._get_option_name(
                    args
                )
                if not configman_name:
                    configman_name = args[0]
            else:
                configman_name = argparse_dest
            configman_default = argparse_default
            configman_from_string = boolean_converter
            configman_to_string = to_str

        #--------------------------------------------------------------------
        # APPEND
        elif argparse_action_name == 'append':
            if argparse_dest is None:
                configman_name, configman_is_argument = self._get_option_name(
                    args
                )
                if not configman_name:
                    configman_name = args[0]
            else:
                configman_name = argparse_dest
            configman_default = argparse_default
            if argparse_type:
                configman_from_string = argparse_type
            else:
                configman_from_string = str
            configman_to_string = to_str

        #--------------------------------------------------------------------
        # APPEND_CONST
        elif argparse_action_name == 'append_const':
            if argparse_dest is None:
                configman_name, configman_is_argument = self._get_option_name(
                    args
                )
                if not configman_name:
                    configman_name = args[0]
            else:
                configman_name = argparse_dest
            configman_default = argparse_default
            if argparse_type:
                configman_from_string = argparse_type
            else:
                configman_from_string = str_to_instance_of_type_converters.get(
                    type(argparse_const),
                    str
                )
            configman_to_string = to_str

        #--------------------------------------------------------------------
        # VERSION
        elif argparse_action_name == 'version':
            return an_action

        #--------------------------------------------------------------------
        # OTHER
        else:
            configman_name = argparse_dest

        # configman uses the switch name as the name of the key inwhich to
        # store values.  argparse is able to use different names for each.
        # this means that configman may encounter repeated targets.  Rather
        # than overwriting Options with new ones with the same name, configman
        # renames them by appending the '$' character.
        while configman_name in self.required_config:
            configman_name = "%s$" % configman_name
        configman_not_for_definition = configman_name.endswith('$')

        # it's finally time to create the configman Option object and add it
        # to the required_config.
        self.required_config.add_option(
            name=configman_name,
            default=configman_default,
            doc=configman_doc,
            from_string_converter=configman_from_string,
            to_string_converter=configman_to_string,
            #short_form=configman_short_form,
            is_argument=configman_is_argument,
            not_for_definition=configman_not_for_definition,
            # we're going to save the args & kwargs that created the
            # argparse Action.  This enables us to perfectly reproduce the
            # the original Action object later during the configman overlay
            # process.
            foreign_data=DotDict({
                'argparse.flags.subcommand': False,
                'argparse.args': args,
                'argparse.kwargs': kwargs,
                'argparse.owning_subparser_name': self.subparser_name,
            })
        )
        return an_action

    #--------------------------------------------------------------------------
    def add_subparsers(self, *args, **kwargs):
        """When adding a subparser, we need to ensure that our version of the
        SubparserAction object is returned.  We also need to create the
        corresponding configman Option object for the subparser and pack it's
        foreign data section with the original args & kwargs."""

        kwargs['parser_class'] = self.__class__
        kwargs['action'] = ConfigmanSubParsersAction

        subparser_action = super(ArgumentParser, self).add_subparsers(
            *args,
            **kwargs
        )
        self._argparse_subparsers = subparser_action

        if "dest" not in kwargs or kwargs['dest'] is None:
            kwargs['dest'] = 'subcommand'
        configman_name = kwargs['dest']
        configman_default = None
        configman_doc = kwargs.get('help', '')
        subprocessor_from_string_converter = SubparserFromStringConverter()
        configman_to_string = str
        configman_is_argument = True
        configman_not_for_definition = True

        # it's finally time to create the configman Option object and add it
        # to the required_config.
        self.required_config.add_option(
            name=configman_name,
            default=configman_default,
            doc=configman_doc,
            from_string_converter=subprocessor_from_string_converter,
            to_string_converter=configman_to_string,
            is_argument=configman_is_argument,
            not_for_definition=configman_not_for_definition,
            # we're going to save the input parameters that created the
            # argparse Action.  This enables us to perfectly reproduce the
            # the original Action object later during the configman overlay
            # process.
            foreign_data=DotDict({
                'argparse.flags.subcommand': subparser_action,
                'argparse.args': args,
                'argparse.kwargs': kwargs,
                'argparse.subparsers': DotDict(),
                'argparse.subprocessor_from_string_converter':
                subprocessor_from_string_converter
            })
        )

        self.configman_subparsers_option = self.required_config[configman_name]
        subparser_action.add_configman_option(self.configman_subparsers_option)

        return subparser_action

    #--------------------------------------------------------------------------
    def set_defaults(self, **kwargs):
        """completely take over the 'set_defaults' system of argparse, because
        configman has no equivalent.  These will be added back to the configman
        result at the very end."""
        self.extra_defaults = kwargs

    #--------------------------------------------------------------------------
    def parse_args(self, args=None, namespace=None):
        """this method hijacks the normal argparse Namespace generation,
        shimming configman into the process. The return value will be a
        configman DotDict rather than an argparse Namespace."""
        # load the config_manager within the scope of the method that uses it
        # so that we avoid circular references in the outer scope
        from configman.config_manager import ConfigurationManager

        configuration_manager = ConfigurationManager(
            definition_source=[self.get_required_config()],
            values_source_list=self.value_source_list,
            argv_source=args,
            app_name=self.prog,
            app_version=self.version,
            app_description=self.description,
            use_auto_help=False,
        )

        # it is apparent a common idiom that commandline options may have
        # embedded '-' characters in them.  Configman requires that option
        # follow the Python Identifier rules.  Fortunately, Configman has a
        # class that will perform dynamic translation of keys.  In this
        # code fragment, we fetch the final configuration from configman
        # using a Mapping that will translate keys with '-' into keys with
        # '_' instead.
        conf = configuration_manager.get_config(
            mapping_class=create_key_translating_dot_dict(
                "HyphenUnderscoreDict",
                (('-', '_'),)
            )
        )

        # here is where we add the values given to "set_defaults" method
        # of argparse.
        if self.configman_subparsers_option:
            subparser_name = conf[self.configman_subparsers_option.name]
            try:
                conf.update(
                    self.configman_subparsers_option.foreign_data.argparse
                    .subparsers[subparser_name].subparser
                    .extra_defaults
                )
            except (AttributeError, KeyError):
                # no extra_defaults skip on
                pass

        if hasattr(self, 'extra_defaults'):
            conf.update(self.extra_defaults)

        return conf

    #--------------------------------------------------------------------------
    def parse_known_args(self, args=None, namespace=None):
        """this method hijacks the normal argparse Namespace generation,
        shimming configman into the process. The return value will be a
        configman DotDict rather than an argparse Namespace."""
        # load the config_manager within the scope of the method that uses it
        # so that we avoid circular references in the outer scope
        from configman.config_manager import ConfigurationManager
        configuration_manager = ConfigurationManager(
            definition_source=[self.get_required_config()],
            values_source_list=self.value_source_list,
            argv_source=args,
            app_name=self.prog,
            app_version=self.version,
            app_description=self.description,
            use_auto_help=False,
        )
        conf = configuration_manager.get_config(
            mapping_class=create_key_translating_dot_dict(
                "HyphenUnderscoreDict",
                (('-', '_'),)
            )
        )
        return conf

    #--------------------------------------------------------------------------
    def _get_option_name(self, args):
        # argparse is loose in the manner that it names arguments.  Sometimes
        # it comes in as the 'dest' kwarg, othertimes it is deduced from args
        # as the first "long" style argument in the args.  This method
        short_name = None
        for an_option in args:
            if an_option[0] in self.prefix_chars:
                if an_option[1] in self.prefix_chars:
                    return an_option[2:], False
                if not short_name:
                    short_name = an_option[1:]
            else:
                return an_option, True
        if short_name:
            return short_name, False
        return None


#------------------------------------------------------------------------------
def setup_definitions(source, destination):
    """this method stars the process of configman reading and using an argparse
    instance as a source of configuration definitions."""
    #"""assume that source is of type argparse
    try:
        destination.update(source.get_required_config())
    except AttributeError:
        # looks like the user passed in a real arpgapse parser rather than our
        # bastardized version of one.  No problem, we can work with it,
        # though the translation won't be as perfect.
        our_parser = ArgumentParser()
        for i, an_action in enumerate(source._actions):
            args, kwargs = get_args_and_values(source, an_action)
            dest = kwargs.get('dest', '')
            if dest in ('help', 'version'):
                continue
            our_parser.add_argument(*args, **kwargs)
        destination.update(our_parser.get_required_config())
