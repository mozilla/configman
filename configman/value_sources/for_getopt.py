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

"""This module implements a configuration value source from the commandline.
It uses getopt in its implementation.  It is thought that this implementation
will be supplanted by the argparse implementation when using Python 2.7 or
greater.

This module declares that its ValueSource constructor implementation can
handle the getopt module or a list.  If specified as the getopt module, the
constructor will fetch the source of argv from the configmanager that was
passed in.  If specified as a list, the constructor will assume the list
represents the argv source."""

import getopt
import collections

from .. import dotdict
from .. import option
from .. import namespace
from ..config_exceptions import NotAnOptionError
from .. import converters as conv

from source_exceptions import ValueException, CantHandleTypeException


class GetOptFailureException(ValueException):
    pass

can_handle = (getopt,
              list,   # a list of options to serve as the argv source
             )


class ValueSource(object):
    """The ValueSource implementation for the getopt module.  This class will
    interpret an argv list of commandline arguments using getopt."""
    def __init__(self, source, the_config_manager=None):
        if source is getopt:
            self.argv_source = the_config_manager.argv_source
        elif isinstance(source, collections.Sequence):
            self.argv_source = source
        else:
            raise CantHandleTypeException("don't know how to handle"
                                             " %s." % str(source))

    def get_values(self, config_manager, ignore_mismatches):
        """This is the black sheep of the crowd of ValueSource implementations.
        It needs to know ahead of time all of the parameters that it will need,
        but we cannot give it.  We may not know all the parameters because
        not all classes may have been expanded yet.  The two parameters allow
        this ValueSource implementation to know what the parameters  have
        already been defined.  The 'ignore_mismatches' parameter tells the
        implementation if it can or cannot ignore extraneous commandline
        options.  The last time this function is called, it will be required
        to test for illegal commandline options and respond accordingly."""
        short_options_str, \
        long_options_list = self.getopt_create_opts(
                             config_manager.option_definitions)
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
        except getopt.GetoptError, x:
            raise NotAnOptionError(str(x))
        command_line_values = dotdict.DotDict()
        for opt_name, opt_val in getopt_options:
            if opt_name.startswith('--'):
                name = opt_name[2:]
            else:
                name = self.find_name_with_short_form(opt_name[1:],
                                            config_manager.option_definitions,
                                            '')
                if not name:
                    raise NotAnOptionError('%s is not a valid short'
                                              ' form option' % opt_name[1:])
            option_ = config_manager._get_option(name)
            if option_.from_string_converter == conv.boolean_converter:
                command_line_values[name] = not option_.default
            else:
                command_line_values[name] = opt_val
        return command_line_values

    def getopt_create_opts(self, option_definitions):
        short_options_list = []
        long_options_list = []
        self.getopt_create_opts_recursive(option_definitions,
                                          "",
                                          short_options_list,
                                          long_options_list)
        short_options_str = ''.join(short_options_list)
        return short_options_str, long_options_list

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
            if args[0][:2] == '--':
                try:
                    opts, args = getopt.do_longs(opts, args[0][2:],
                                                 longopts, args[1:])
                except getopt.GetoptError:
                    prog_args.append(args[0])
                    args = args[1:]
            elif args[0][:1] == '-':
                try:
                    opts, args = getopt.do_shorts(opts, args[0][1:], shortopts,
                                                  args[1:])
                except getopt.GetoptError:
                    prog_args.append(args[0])
                    args = args[1:]
            else:
                prog_args.append(args[0])
                args = args[1:]
        return opts, prog_args

    #--------------------------------------------------------------------------
    def find_name_with_short_form(self, short_name, source, prefix):
        for key, val in source.items():
            type_of_val = type(val)
            if type_of_val == namespace.Namespace:
                new_prefix = '%s.' % key
                name = self.find_name_with_short_form(short_name, val,
                                                      new_prefix)
                if name:
                    return name
            else:
                try:
                    if short_name == val.short_form:
                        return '%s%s' % (prefix, val.name)
                except KeyError:
                    continue
        return None
