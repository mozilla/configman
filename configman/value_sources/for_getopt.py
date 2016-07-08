# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""This module implements a configuration value source from the commandline.
It uses getopt in its implementation.  It is thought that this implementation
will be supplanted by the argparse implementation when using Python 2.7 or
greater.

This module declares that its ValueSource constructor implementation can
handle the getopt module or a list.  If specified as the getopt module, the
constructor will fetch the source of argv from the configmanager that was
passed in.  If specified as a list, the constructor will assume the list
represents the argv source."""
from __future__ import absolute_import, division, print_function

import getopt
import collections

from configman import option
from configman import namespace
from configman.config_exceptions import NotAnOptionError
from configman.converters import boolean_converter
from configman.dotdict import DotDict

from configman.value_sources.source_exceptions import (
    ValueException,
    CantHandleTypeException
)


#==============================================================================
class GetOptFailureException(ValueException):
    pass

can_handle = (
    getopt,
    list,   # a list of options to serve as the argv source
)


#==============================================================================
class ValueSource(object):
    """The ValueSource implementation for the getopt module.  This class will
    interpret an argv list of commandline arguments using getopt."""
    #--------------------------------------------------------------------------
    def __init__(self, source, the_config_manager=None):
        if source is getopt:
            self.argv_source = the_config_manager.argv_source
        elif isinstance(source, collections.Sequence):
            self.argv_source = source
        else:
            raise CantHandleTypeException()

    # frequently, command line data sources must be treated differently.  For
    # example, even when the overall option for configman is to allow
    # non-strict option matching, the command line should not arbitrarily
    # accept bad command line switches.  The existance of this key will make
    # sure that a bad command line switch will result in an error without
    # regard to the overall --admin.strict setting.
    command_line_value_source = True

    #--------------------------------------------------------------------------
    def get_values(self, config_manager, ignore_mismatches, obj_hook=DotDict):
        """This is the black sheep of the crowd of ValueSource implementations.
        It needs to know ahead of time all of the parameters that it will need,
        but we cannot give it.  We may not know all the parameters because
        not all classes may have been expanded yet.  The two parameters allow
        this ValueSource implementation to know what the parameters  have
        already been defined.  The 'ignore_mismatches' parameter tells the
        implementation if it can or cannot ignore extraneous commandline
        options.  The last time this function is called, it will be required
        to test for illegal commandline options and respond accordingly.

        Unlike many of the Value sources, this method cannot be "memoized".
        The return result depends on an internal state within the parameter
        'config_manager'.  Any memoize decorator for this method would requrire
        capturing that internal state in the memoize cache key.
        """
        short_options_str, long_options_list = self.getopt_create_opts(
            config_manager.option_definitions
        )
        try:
            if ignore_mismatches:
                fn = ValueSource.getopt_with_ignore
            else:
                fn = getopt.gnu_getopt
            # here getopt looks through the command line arguments and
            # consumes the defined switches.  The things that are not
            # consumed are then offered as the 'args' variable of the
            # parent configuration_manager
            getopt_options, config_manager.args = fn(self.argv_source,
                                                     short_options_str,
                                                     long_options_list)
        except getopt.GetoptError as x:
            raise NotAnOptionError(str(x))
        command_line_values = obj_hook()
        for opt_name, opt_val in getopt_options:
            if opt_name.startswith('--'):
                name = opt_name[2:]
            else:
                name = self.find_name_with_short_form(
                    opt_name[1:],
                    config_manager.option_definitions,
                    ''
                )
                if not name:
                    raise NotAnOptionError(
                        '%s is not a valid short form option' % opt_name[1:]
                    )
            option_ = config_manager._get_option(name)
            if option_.from_string_converter == boolean_converter:
                command_line_values[name] = not option_.default
            else:
                command_line_values[name] = opt_val
        for name, value in zip(
            self._get_arguments(
                config_manager.option_definitions,
                command_line_values
            ),
            config_manager.args
        ):
            command_line_values[name] = value
        return command_line_values

    #--------------------------------------------------------------------------
    def getopt_create_opts(self, option_definitions):
        short_options_list = []
        long_options_list = []
        self.getopt_create_opts_recursive(option_definitions,
                                          "",
                                          short_options_list,
                                          long_options_list)
        short_options_str = ''.join(short_options_list)
        return short_options_str, long_options_list

    #--------------------------------------------------------------------------
    def getopt_create_opts_recursive(self, source,
                                     prefix,
                                     short_options_list,
                                     long_options_list):
        for key, val in source.items():
            if isinstance(val, option.Option):
                boolean_option = type(val.default) == bool
                if val.short_form:
                    try:
                        if boolean_option:
                            if val.short_form not in short_options_list:
                                short_options_list.append(val.short_form)
                        else:
                            short_with_parameter = "%s:" % val.short_form
                            if short_with_parameter not in short_options_list:
                                short_options_list.append(short_with_parameter)
                    except AttributeError:
                        pass
                if boolean_option:
                    long_options_list.append('%s%s' % (prefix, val.name))
                else:
                    long_options_list.append('%s%s=' % (prefix, val.name))
            elif isinstance(val, option.Aggregation):
                pass  # skip Aggregations they have nothing to do with getopt
            else:  # Namespace case
                new_prefix = '%s%s.' % (prefix, key)
                self.getopt_create_opts_recursive(val,
                                                  new_prefix,
                                                  short_options_list,
                                                  long_options_list)

    #--------------------------------------------------------------------------
    @staticmethod
    def getopt_with_ignore(args, shortopts, longopts=[]):
        """my_getopt(args, options[, long_options]) -> opts, args

        This function works like gnu_getopt(), except that unknown parameters
        are ignored rather than raising an error.
        """
        opts = []
        prog_args = []
        if isinstance(longopts, str):
            longopts = [longopts]
        else:
            longopts = list(longopts)
        while args:
            if args[0] == '--':
                prog_args += args[1:]
                break
            if args[0].startswith('--'):
                try:
                    opts, args = getopt.do_longs(
                        opts,
                        args[0][2:],
                        longopts,
                        args[1:]
                    )
                except getopt.GetoptError:
                    args = args[1:]
            elif args[0][0] == '-':
                try:
                    opts, args = getopt.do_shorts(
                        opts,
                        args[0][1:],
                        shortopts,
                        args[1:]
                    )
                except getopt.GetoptError:
                    args = args[1:]
            else:
                prog_args.append(args[0])
                args = args[1:]
        return opts, prog_args

    #--------------------------------------------------------------------------
    def find_name_with_short_form(self, short_name, source, prefix):
        for key, val in source.items():
            if isinstance(val, namespace.Namespace):
                new_prefix = '%s.' % key
                name = self.find_name_with_short_form(short_name, val,
                                                      new_prefix)
                if name:
                    return name
            elif isinstance(val, option.Option):
                try:
                    if short_name == val.short_form:
                        return '%s%s' % (prefix, val.name)
                except KeyError:
                    continue
        return None

    #--------------------------------------------------------------------------
    @staticmethod
    def _get_arguments(option_definitions, switches_already_used):
        for key in option_definitions.keys_breadth_first():
            try:
                if (
                    option_definitions[key].is_argument
                    and key not in switches_already_used
                ):
                    yield key
            except AttributeError:
                # this option definition does have the concept of being
                # an argument - likely an aggregation
                pass

    #--------------------------------------------------------------------------
    @staticmethod
    def _setup_auto_help(the_config_manager):
        help_option = option.Option(
            name='help',
            doc='print this',
            default=False
        )
        the_config_manager.definition_source_list.append({'help': help_option})
