import sys
import getopt

from dotdict import DotDict
from option import Option
from namespace import Namespace

import exceptions as exc
import converters as conv

#==============================================================================
class OptionsByGetopt(object):
    #--------------------------------------------------------------------------
    def __init__(self, argv_source=sys.argv):
        self.argv_source = argv_source

    #--------------------------------------------------------------------------
    def get_values(self, config_manager, ignore_mismatches):
        short_options_str, \
        long_options_list = self.getopt_create_opts(
                             config_manager.option_definitions)
        try:
            if ignore_mismatches:
                fn = OptionsByGetopt.getopt_with_ignore
            else:
                fn = getopt.gnu_getopt
            getopt_options, self.args = fn(self.argv_source,
                                           short_options_str,
                                           long_options_list)
        except getopt.GetoptError, x:
            raise exc.NotAnOptionError(str(x))
        command_line_values = DotDict()
        for opt_name, opt_val in getopt_options:
            if opt_name.startswith('--'):
                name = opt_name[2:]
            else:
                name = self.find_name_with_short_form(opt_name[1:],
                                            config_manager.option_definitions,
                                            '')
                if not name:
                    raise NotAnOptionError('%s is not a valid short '
                                           'form option' % opt_name[1:])
            option = config_manager.get_option_by_name(name)
            if option.from_string_converter == conv.boolean_converter:
                command_line_values[name] = not option.default
            else:
                command_line_values[name] = opt_val
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
            if type(val) == Option:
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
            if type_of_val == Namespace:
                prefix = '%s.' % key
                name = self.find_name_with_short_form(short_name, val, prefix)
                if name:
                    return name
            else:
                try:
                    if short_name == val.short_form:
                        return '%s%s' % (prefix, val.name)
                except KeyError:
                    continue
        return None


