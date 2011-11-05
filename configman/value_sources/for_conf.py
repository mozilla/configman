"""This module implements a configuration value source comprising a stream of
textual key/value pairs.  The implementation uses a ContextManger to iterate
through the stream.  The ContextManager can represent any number of sources,
like files or database results.  If supplied with a simple string rather than
a ContextManager, the value source will assume it is a file pathname and try
to open it.
"""

import functools
import sys
import exceptions

import configman.option as opt
import configman.converters as conv
import configman

function_type = type(lambda x: x)  # TODO: just how do you express the Fuction
                                   # type as a constant?

# the list of types that the contstuctor can handle.
can_handle = (basestring,
              function_type  # this is to say that this ValueSource is willing
                             # to try a function that will return a
                             # context manager
             )

file_name_extension = '.conf'


class NotAConfigFileException(exceptions.ValueException):
    pass


class ValueSource(object):

    def __init__(self, candidate, the_config_manager=None):
        if isinstance(candidate, basestring):
            # we're trusting the string represents a filename
            opener = functools.partial(open, candidate)
        elif isinstance(candidate, function_type):
            # we're trusting that the function when called with no parameters
            # will return a Context Manager Type.
            opener = candidate
        else:
            raise exceptions.CantHandleTypeException("don't know how to handle"
                                                     " %s." % str(candidate))
        self.values = {}
        try:
            with opener() as f:
                previous_key = None
                for line in f:
                    if line.strip().startswith('#') or not line.strip():
                        continue
                    if line[0] in ' \t' and previous_key:
                        line = line[1:]
                        self.values[previous_key] = '%s%s' % \
                                            (self.values[previous_key],
                                             line.rstrip())
                        continue
                    try:
                        key, value = line.split("=", 1)
                        self.values[key.strip()] = value.strip()
                        previous_key = key
                    except ValueError:
                        self.values[line] = ''
        except Exception, x:
            raise NotAConfigFileException("couldn't interpret %s as a context "
                                          "file: %s" % (candidate, str(x)))

    def get_values(self, config_manager, ignore_mismatches):
        """the 'config_manager' and 'ignore_mismatches' are dummy values for
        this implementation of a ValueSource."""
        return self.values

    @staticmethod
    def write(option_iter, output_stream=sys.stdout, comments=True):
        for qkey, key, val in option_iter():
            if isinstance(val, opt.Option):
                if comments:
                    print >> output_stream, '# name:', qkey
                    print >> output_stream, '# doc:', val.doc
                    print >> output_stream, '# converter:', \
                        conv.py_obj_to_str(val.from_string_converter)
                val_str = configman.ConfigurationManager.option_value_str(val)
                print >> output_stream, '%s=%s\n' % (qkey, val_str)
            else:
                print >> output_stream, '#%s' % ('-' * 79)
                print >> output_stream, '# %s - %s\n' % (key, val._doc)
