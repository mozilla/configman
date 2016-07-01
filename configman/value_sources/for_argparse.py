# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""This module implements a configuration value source from the commandline
implemented using argparse.  This was a difficult module to make because of
some fundemental differences with the way that configman and argparse set up
their respective priorities.

One of the primary problems is that both configman and argparse have their own
data definition specs.  Configman has Options while argparse has Actions.  Both
libraries can use their own specs, so a translation layer had to be created.

During the process of configman's overlay/expansion phase, the definitions as
to what is allowed on the command line change. What was not allowed during an
earlier pass may be allowed in a later pass.  This means that argparse may need
to be setup and used several times as the definitions change.

Creating a perfect round trip translation system proved to be impossible
because the feature sets of argparse and configman do not correspond pefectly.
So rather than trying to translate everything, each phase of the original
argparse definitions (args & kwargs) are captured and stored.  Then when
configman needs to get command line parameters during the overlay/expansion
process, it is able to perfectly recreate the original arparse parsers tweaked
with whatever new arguments that the expansion process introduced.

This module introduces a flock of different derivations of argparse parsers.
Each is used in a different context during the overlay expansion process.
While several of them are functionally equivalent, we keep them as separate
classes so that we can use class identity as a differention mechanism.
"""
from __future__ import absolute_import, division, print_function
import argparse
import copy
import six

import collections

from configman.option import Option
from configman.dotdict import DotDict
from configman.converters import (
    boolean_converter,
    to_str,
)
from configman.namespace import Namespace

is_command_line_parser = True

can_handle = (
    argparse,
)

parser_count = 0


#==============================================================================
class IntermediateConfigmanParser(argparse.ArgumentParser):
    """"""
    #--------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        self.get_parser_id()
        self.subparser_name = kwargs.pop('subparser_name', None)
        self.configman_subparsers_option = kwargs.pop(
            'configman_subparsers_option',
            None
        )
        super(IntermediateConfigmanParser, self).__init__(
            *args, **kwargs
        )
        self.required_config = Namespace()

        self._use_argparse_add_help = kwargs.get('add_help', False)

    #--------------------------------------------------------------------------
    def get_parser_id(self):
        global parser_count
        if hasattr(self, 'id'):
            return
        self.id = "%03d" % parser_count
        parser_count += 1

    #--------------------------------------------------------------------------
    def error(self, message):
        """we need to suppress errors that might happen in earlier phases of
        the expansion/overlay process. """
        if (
            "not allowed" in message
            or "ignored" in message
            or "expected" in message
            or "invalid" in message
            or self.add_help
        ):
            # when we have "help" then we must also have proper error
            # processing.  Without "help", we suppress the errors by
            # doing nothing here
            super(IntermediateConfigmanParser, self).error(message)

    #--------------------------------------------------------------------------
    def parse_args(self, args=None, namespace=None, object_hook=None):
        proposed_config = \
            super(IntermediateConfigmanParser, self).parse_args(
                args,
                namespace
            )
        return proposed_config

    #--------------------------------------------------------------------------
    def parse_known_args(self, args=None, namespace=None, object_hook=None):
        result = super(IntermediateConfigmanParser, self) \
            .parse_known_args(args, namespace)
        try:
            an_argparse_namespace, extra_arguments = result
        except TypeError:
            an_argparse_namespace = argparse.Namespace()
            extra_arguments = result
        return (an_argparse_namespace, extra_arguments)

    #--------------------------------------------------------------------------
    @staticmethod
    def argparse_namespace_to_dotdict(proposed_config, object_hook=None):
        if object_hook is None:
            object_hook = DotDict
        config = object_hook()
        for key, value in six.iteritems(proposed_config.__dict__):
            config[key] = value
        return config

counter = 0


#==============================================================================
class FinalStageConfigmanParser(IntermediateConfigmanParser):
    #--------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        self.get_parser_id()
        super(FinalStageConfigmanParser, self).__init__(
            *args, **kwargs
        )


#==============================================================================
class HelplessConfigmanParser(IntermediateConfigmanParser):
    #--------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        new_kwargs = copy.copy(kwargs)
        new_kwargs['add_help'] = False
        self.get_parser_id()
        super(HelplessConfigmanParser, self).__init__(
            *args, **new_kwargs
        )


#==============================================================================
class IntermediateConfigmanSubParser(IntermediateConfigmanParser):
    #--------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        self.get_parser_id()
        super(IntermediateConfigmanSubParser, self).__init__(
            *args, **kwargs
        )


#==============================================================================
class HelplessIntermediateConfigmanSubParser(IntermediateConfigmanParser):
    #--------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        new_kwargs = copy.copy(kwargs)
        new_kwargs['add_help'] = False
        self.get_parser_id()
        super(HelplessIntermediateConfigmanSubParser, self).__init__(
            *args, **new_kwargs
        )


#==============================================================================
class ConfigmanAdminParser(IntermediateConfigmanParser):
    #--------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        self.get_parser_id()
        new_kwargs = copy.copy(kwargs)
        new_kwargs['add_help'] = True
        #new_kwargs['add_help'] = False
        new_kwargs['prog'] = 'admin%s' % self.id
        new_kwargs['parents'] = []
        super(ConfigmanAdminParser, self).__init__(
            *args, **new_kwargs
        )


#==============================================================================
class HelplessConfigmanAdminParser(IntermediateConfigmanParser):
    #--------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        self.get_parser_id()
        new_kwargs = copy.copy(kwargs)
        new_kwargs['add_help'] = False
        new_kwargs['prog'] = 'admin%s' % self.id
        new_kwargs['parents'] = []
        super(HelplessConfigmanAdminParser, self).__init__(
            *args, **new_kwargs
        )


#==============================================================================
class ParserContainer(object):
    """this class is a argparse ArgumentParser generator.  Configman uses
    it to create sets of linked ArgumentParsers of the appropriate types.  It
    does the translations between configman and argparse.  First it tries to
    create argparse parameters by fetch original args & kwargs from the
    foreign_data sections of the configman Options.  Failing that, it tries
    to translate configman Options as best as it can."""
    #--------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):

        self.main_parser_args = DotDict()
        self.main_parser_args.args = args
        self.main_parser_args.kwargs = kwargs.copy()
        self.main_parser_args.kwargs.setdefault('parents', [])
        self.arguments_for_building_argparse = []
        self.subcommand = None
        self.subparser_args_list = []
        self.subparsers = {}
        self.admin_parser_args = DotDict()
        self.admin_parser_args.args = args
        self.admin_parser_args.kwargs = kwargs.copy()
        self.admin_arguments = []
        self._use_argparse_add_help = kwargs.get('add_help', False)
        self.get_parser_id()
        self.extra_defaults = {}

    #--------------------------------------------------------------------------
    def get_parser_id(self):
        global parser_count
        if hasattr(self, 'id'):
            return
        self.id = "%03d" % parser_count
        parser_count += 1

    #--------------------------------------------------------------------------
    def create_argparse_parser(
        self,
        main_parser_class=HelplessConfigmanParser,
        subparser_class=IntermediateConfigmanSubParser,
        admin_parser_class=ConfigmanAdminParser,
    ):
        # create admin parser to be used a a parent parser
        self.admin_parser_args.kwargs['parents'] = []
        admin_parser = admin_parser_class(
            *self.admin_parser_args.args,
            **self.admin_parser_args.kwargs
        )

        for admin_args in self.admin_arguments:
            admin_args.kwargs['default'] = argparse.SUPPRESS
            admin_parser.add_argument(*admin_args.args, **admin_args.kwargs)

        # create the main parser
        self.main_parser_args.kwargs['parents'] = [admin_parser]
        main_parser = main_parser_class(
            *self.main_parser_args.args,
            **self.main_parser_args.kwargs
        )

        if self.subcommand is not None:
            # add any subparsers to the parent parser
            subcommand_kwargs = copy.copy(self.subcommand.kwargs)
            subcommand_kwargs['parser_class'] = subparser_class
            subcommand_kwargs.setdefault('parents', [])
            if 'parents' in subcommand_kwargs:
                del subcommand_kwargs['parents']
            if 'action' in subcommand_kwargs:
                del subcommand_kwargs['action']
            local_subparser_action = main_parser.add_subparsers(
                *self.subcommand.args,
                **subcommand_kwargs
            )
            local_subparser_action.default = argparse.SUPPRESS
            for subparser_name in self.subcommand.subparsers.keys():
                subparser_kwargs = copy.copy(
                    self.subcommand.subparsers[subparser_name].kwargs
                )
                subparser_args = \
                    self.subcommand.subparsers[subparser_name].args
                if 'dest' in subparser_kwargs:
                    del subparser_kwargs['dest']
                subparser_kwargs['parents'] = [admin_parser]
                local_subparser = local_subparser_action.add_parser(
                    *subparser_args,
                    **subparser_kwargs
                )
                self.subparsers[subparser_name] = local_subparser

        # add the actual arguments to the appropriate main or subparsers
        for args_for_an_argparse_argument in (
            self.arguments_for_building_argparse
        ):
            args = args_for_an_argparse_argument.args
            kwargs = args_for_an_argparse_argument.kwargs
            owning_subparser_name = args_for_an_argparse_argument.get(
                'owning_subparser_name',
                None
            )
            if owning_subparser_name:
                the_parser = self.subparsers[owning_subparser_name]
                the_parser.add_argument(*args, **kwargs)
            else:
                main_parser.add_argument(*args, **kwargs)

        return main_parser

    #--------------------------------------------------------------------------
    def _add_argument_from_original_source(self, qualified_name, option):
        argparse_foreign_data = option.foreign_data.argparse
        if argparse_foreign_data.flags.subcommand:
            # this argument represents a subcommand, we must setup the
            # subparsers
            self.subcommand = argparse_foreign_data
            self.subparser_orignal_args = argparse_foreign_data.subparsers
            self.subcommand_configman_option = option

        else:
            new_arguments = DotDict()
            new_arguments.args = argparse_foreign_data.args
            new_arguments.kwargs = copy.copy(argparse_foreign_data.kwargs)
            new_arguments.qualified_name = qualified_name
            new_arguments.owning_subparser_name = \
                argparse_foreign_data.owning_subparser_name

            if new_arguments.args == (qualified_name.split('.')[-1],):
                new_arguments.args = (qualified_name,)
            elif 'dest' in new_arguments.kwargs:
                if new_arguments.kwargs['dest'] != qualified_name:
                    new_arguments.kwargs['dest'] = qualified_name
            else:
                new_arguments.kwargs['dest'] = qualified_name
            try:
                new_arguments.kwargs['dest'] = \
                    new_arguments.kwargs['dest'].replace('$', '')
            except KeyError:
                # there was no 'dest' key, so we can ignore this error
                pass
            self.arguments_for_building_argparse.append(new_arguments)

    #--------------------------------------------------------------------------
    def _add_argument_from_configman_option(self, qualified_name, option):
        opt_name = qualified_name
        kwargs = DotDict()

        if option.is_argument:  # is positional argument
            option_name = opt_name
        else:
            option_name = '--%s' % opt_name
            kwargs.dest = opt_name

        if option.short_form:
            option_short_form = '-%s' % option.short_form
            args = (option_name, option_short_form)
        else:
            args = (option_name,)

        if option.from_string_converter in (bool, boolean_converter):
            kwargs.action = 'store_true'
        else:
            kwargs.action = 'store'

        kwargs.default = argparse.SUPPRESS
        kwargs.help = option.doc

        new_arguments = DotDict()
        new_arguments.args = args
        new_arguments.kwargs = kwargs
        new_arguments.qualified_name = qualified_name

        if (
            isinstance(option.default, collections.Sequence)
            and not isinstance(option.default, (six.binary_type, six.text_type))
        ):
            if option.is_argument:
                kwargs.nargs = len(option.default)
            else:
                kwargs.nargs = "+"

        if qualified_name.startswith('admin'):
            self.admin_arguments.append(new_arguments)
        else:
            self.arguments_for_building_argparse.append(new_arguments)

    #--------------------------------------------------------------------------
    def add_argument_from_option(self, qualified_name, option):
        if (
            option.foreign_data is not None
            and "argparse" in option.foreign_data
        ):
            self._add_argument_from_original_source(qualified_name, option)
        else:
            self._add_argument_from_configman_option(qualified_name, option)


#==============================================================================
class ValueSource(object):
    """The ValueSource implementation for the argparse module.  This class will
    interpret an argv list of commandline arguments using argparse returning
    a DotDict derivative respresenting the values return by argparse."""
    #--------------------------------------------------------------------------
    def __init__(self, source, conf_manager):
        self.source = source
        self.parent_parsers = []
        self.argv_source = tuple(conf_manager.argv_source)

    # frequently, command line data sources must be treated differently.  For
    # example, even when the overall option for configman is to allow
    # non-strict option matching, the command line should not arbitrarily
    # accept bad command line switches.  The existance of this key will make
    # sure that a bad command line switch will result in an error without
    # regard to the overall --admin.strict setting.
    command_line_value_source = True

    #--------------------------------------------------------------------------
    @staticmethod
    def _get_known_args(conf_manager):
        return set(
            x
            for x in conf_manager.option_definitions.keys_breadth_first()
        )

    #--------------------------------------------------------------------------
    def _option_to_args_list(self, an_option, key):
        if an_option.is_argument:
            if an_option.foreign_data is not None:
                nargs = an_option.foreign_data.argparse.kwargs.get(
                    'nargs',
                    None
                )
            else:
                if isinstance(an_option.value, (six.binary_type, six.text_type)):
                    an_option.value = to_str(an_option.value)
                    return an_option.value
                if an_option.to_string_converter:
                    return an_option.to_string_converter(an_option.value)
                return to_str(an_option.value)
            if (
                nargs is not None
                and isinstance(an_option.value, collections.Sequence)
            ):
                if isinstance(an_option.value, (six.binary_type, six.text_type)):
                    an_option.value = to_str(an_option.value)
                    return an_option.value
                return [to_str(x) for x in an_option.value]
            if an_option.value is None:
                return []
            return to_str(an_option.value)
        #if an_option.foreign_data.argparse.kwargs.nargs == 0:
            #return None
        if an_option.from_string_converter in (bool, boolean_converter):
            if an_option.value:
                return "--%s" % key
            return None
        if an_option.value is None:
            return None
        return '--%s="%s"' % (
            key,
            to_str(an_option)
        )

    #--------------------------------------------------------------------------
    def create_fake_args(self, config_manager):
        # all of this is to keep argparse from barfing if the minumum number
        # of required arguments is not in place at run time.  It may be that
        # some config file or environment will bring them in later.   argparse
        # needs to cope using this placebo argv
        args = [
            self._option_to_args_list(
                config_manager.option_definitions[key],
                key
            )
            for key in config_manager.option_definitions.keys_breadth_first()
            if (
                isinstance(
                    config_manager.option_definitions[key],
                    Option
                )
                and config_manager.option_definitions[key].is_argument
            )
        ]

        flattened_arg_list = []
        for x in args:
            if isinstance(x, list):
                flattened_arg_list.extend(x)
            else:
                flattened_arg_list.append(x)
        final_arg_list = [
            x.strip()
            for x in flattened_arg_list
            if x is not None and x.strip() != ''
        ]
        try:
            return final_arg_list + self.extra_args
        except (AttributeError, TypeError):
            return final_arg_list

    #--------------------------------------------------------------------------
    def get_values(self, config_manager, ignore_mismatches, object_hook=None):
        if ignore_mismatches:
            self.extra_args = []
            parser = self._create_new_argparse_instance(
                {
                    "main_parser_class": HelplessConfigmanParser,
                    "subparser_class": HelplessIntermediateConfigmanSubParser,
                    "admin_parser_class": HelplessConfigmanAdminParser
                },
                config_manager,
                False,  # create auto help
            )
            namespace_and_extra_args = parser.parse_known_args(
                args=self.argv_source
            )

            try:
                argparse_namespace, unused_args = namespace_and_extra_args
                self.extra_args.extend(unused_args)
            except TypeError:
                argparse_namespace = argparse.Namespace()
                self.extra_args.extend(namespace_and_extra_args)

        else:
            fake_args = self.create_fake_args(config_manager)
            if (
                ('--help' in self.argv_source or "-h" in self.argv_source)
                and '--help' not in fake_args and '-h' not in fake_args
            ):
                fake_args.append("--help")

            parser = self._create_new_argparse_instance(
                {
                    "main_parser_class": FinalStageConfigmanParser,
                    "subparser_class": IntermediateConfigmanSubParser,
                    "admin_parser_class": HelplessConfigmanAdminParser
                },
                config_manager,
                True,  # create Help
            )

            argparse_namespace = parser.parse_args(
                args=fake_args,
            )
        return parser.argparse_namespace_to_dotdict(
            argparse_namespace,
            object_hook,
        )

    #--------------------------------------------------------------------------
    def _create_new_argparse_instance(
        self,
        parser_classes,
        config_manager,
        create_auto_help,
    ):
        a_parser = ParserContainer(
            prog=config_manager.app_name,
            #version=config_manager.app_version,
            description=config_manager.app_description,
            add_help=create_auto_help,
        )
        self._setup_argparse(a_parser, parser_classes, config_manager)
        main_parser = a_parser.create_argparse_parser(**parser_classes)
        return main_parser

    #--------------------------------------------------------------------------
    def _setup_argparse(self, parser, parser_classes, config_manager):
        # need to ensure that admin options are added first, since they'll
        # go into a subparser and the subparser must be complete before
        # given to any other parser as a parent
        for opt_name in config_manager.option_definitions.keys_breadth_first():
            an_option = config_manager.option_definitions[opt_name]
            if isinstance(an_option, Option):
                parser.add_argument_from_option(opt_name, an_option)

    #--------------------------------------------------------------------------
    @staticmethod
    def _setup_auto_help(the_config_manager):
        pass  # there's nothing to do, argparse already has a help feature
