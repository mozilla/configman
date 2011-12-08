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

"""This module implements a configuration value source comprising a stream of
textual key/value pairs.  The implementation uses a ContextManger to iterate
through the stream.  The ContextManager can represent any number of sources,
like files or database results.  If supplied with a simple string rather than
a ContextManager, the value source will assume it is a file pathname and try
to open it.
"""

import functools
import sys

from .. import namespace
from .. import option as opt
from .. import converters as conv

from source_exceptions import ValueException, CantHandleTypeException

function_type = type(lambda x: x)  # TODO: just how do you express the Fuction
                                   # type as a constant?
                                   # (peter: why not use inspect.isfunction()?)

# the list of types that the contstuctor can handle.
can_handle = (basestring,
              function_type  # this is to say that this ValueSource is willing
                             # to try a function that will return a
                             # context manager
             )

file_name_extension = 'conf'


class NotAConfigFileError(ValueException):
    pass


class ValueSource(object):

    def __init__(self, candidate, the_config_manager=None):
        if (isinstance(candidate, basestring) and
            candidate.endswith(file_name_extension)):
            # we're trusting the string represents a filename
            opener = functools.partial(open, candidate)
        elif isinstance(candidate, function_type):
            # we're trusting that the function when called with no parameters
            # will return a Context Manager Type.
            opener = candidate
        else:
            raise CantHandleTypeException("don't know how to handle"
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
            raise NotAConfigFileError("couldn't interpret %s as a context "
                                          "file: %s" % (candidate, str(x)))

    def get_values(self, config_manager, ignore_mismatches):
        """the 'config_manager' and 'ignore_mismatches' are dummy values for
        this implementation of a ValueSource."""
        return self.values

    @staticmethod
    def write(option_iter, output_stream=sys.stdout, comments=True):
        for qkey, key, val in option_iter():
            if isinstance(val, namespace.Namespace):
                print >> output_stream, '#%s' % ('-' * 79)
                print >> output_stream, '# %s - %s\n' % (key, val._doc)
            elif isinstance(val, opt.Option):
                if comments:
                    print >> output_stream, '# name:', qkey
                    print >> output_stream, '# doc:', val.doc
                    print >> output_stream, '# converter:', \
                        conv.py_obj_to_str(val.from_string_converter)
                val_str = conv.option_value_str(val)
                print >> output_stream, '%s=%s\n' % (qkey, val_str)
            elif isinstance(val, opt.Aggregation):
                # there is nothing to do for Aggregations at this time
                # it appears here anyway as a marker for future enhancements
                pass