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
from .. import converters

from source_exceptions import ValueException, CantHandleTypeException

function_type = type(lambda x: x)  # TODO: just how do you express the Fuction
                                   # type as a constant?
                                   # (peter: why not use inspect.isfunction()?)

# the list of types that the contstuctor can handle.
can_handle = (
    basestring,
    function_type  # this is to say that this ValueSource is willing
                   # to try a function that will return a
                   # context manager
)

file_name_extension = 'conf'


#==============================================================================
class NotAConfigFileError(ValueException):
    pass


#==============================================================================
class ValueSource(object):

    #--------------------------------------------------------------------------
    def __init__(self, candidate, the_config_manager=None):
        if (
            isinstance(candidate, basestring) and
            candidate.endswith(file_name_extension)
        ):
            # we're trusting the string represents a filename
            opener = functools.partial(open, candidate)
        elif isinstance(candidate, function_type):
            # we're trusting that the function when called with no parameters
            # will return a Context Manager Type.
            opener = candidate
        else:
            raise CantHandleTypeException()
        self.values = {}
        try:
            with opener() as f:
                previous_key = None
                for line in f:
                    if line.strip().startswith('#') or not line.strip():
                        continue
                    if line[0] in ' \t' and previous_key:
                        line = line[1:]
                        self.values[previous_key] = (
                            '%s%s' % (self.values[previous_key],line.rstrip())
                        )
                        continue
                    try:
                        key, value = line.split("=", 1)
                        self.values[key.strip()] = value.strip()
                        previous_key = key
                    except ValueError:
                        self.values[line] = ''
        except Exception, x:
            raise NotAConfigFileError(
                "Conf couldn't interpret %s as a config file: %s"
                % (candidate, str(x))
            )

    #--------------------------------------------------------------------------
    def get_values(self, config_manager, ignore_mismatches):
        """the 'config_manager' and 'ignore_mismatches' are dummy values for
        this implementation of a ValueSource."""
        return self.values

    #--------------------------------------------------------------------------
    @staticmethod
    def write(source_dict, namespace_name=None, output_stream=sys.stdout):
        options = [
            value
            for value in source_dict.values()
            if isinstance(value, opt.Option)
        ]
        options.sort(cmp=lambda x, y: cmp(x.name, y.name))
        namespaces = [
            (key, value)
            for key, value in source_dict.items()
            if isinstance(value, namespace.Namespace)
        ]
        for an_option in options:
            if namespace_name:
                option_name = "%s.%s" % (namespace_name, an_option.name)
            else:
                option_name = an_option.name
            print >>output_stream, "# name: %s" % option_name
            print >>output_stream, "# doc: %s" % an_option.doc
            option_value = str(an_option)
            if isinstance(option_value, unicode):
                option_value = option_value.encode('utf8')

            if an_option.likely_to_be_changed:
                option_format = '%s=%r\n'
            else:
                option_format = '# %s=%r\n'
            print >>output_stream, option_format % (
              option_name,
              option_value
            )
        for key, a_namespace in namespaces:
            if namespace_name:
                namespace_label = ''.join((namespace_name, '.', key))
            else:
                namespace_label = key
            print >> output_stream, '#%s' % ('-' * 79)
            print >> output_stream, '# %s - %s\n' % (
                namespace_label,
                a_namespace._doc
            )
            ValueSource.write(
              a_namespace,
              namespace_name=namespace_label,
              output_stream=output_stream
            )
