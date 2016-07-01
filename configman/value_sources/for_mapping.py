# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function
import collections
import os
import sys
import six

from configman.value_sources.source_exceptions import CantHandleTypeException
from configman.option import Option
from configman.dotdict import DotDict
from configman.memoize import memoize
from configman import namespace

can_handle = (
    os.environ,
    collections.Mapping,
)

file_name_extension = 'env'


#==============================================================================
class ValueSource(object):
    #--------------------------------------------------------------------------
    def __init__(self, source, the_config_manager=None):
        if source is os.environ:
            self.always_ignore_mismatches = True
        elif isinstance(source, collections.Mapping):
            if "always_ignore_mismatches" in source:
                self.always_ignore_mismatches = \
                    bool(source["always_ignore_mismatches"])
            else:
                self.always_ignore_mismatches = False
        else:
            raise CantHandleTypeException()
        self.source = source

    #--------------------------------------------------------------------------
    @memoize()
    def get_values(self, config_manager, ignore_mismatches, obj_hook=DotDict):
        if isinstance(self.source, obj_hook):
            return self.source
        return obj_hook(initializer=self.source)

    #--------------------------------------------------------------------------
    @staticmethod
    def _namespace_reference_value_from_sort(key_value_tuple):
        key, value = key_value_tuple
        if value._reference_value_from:
            # this forces referenced value sections to sort to the top.
            return 'aaaaaa' + key
        else:
            return key

    #--------------------------------------------------------------------------
    @staticmethod
    def write(source_dict, namespace_name=None, output_stream=sys.stdout):
        options = [
            value
            for value in source_dict.values()
            if isinstance(value, Option)
        ]
        options.sort(key=lambda x: x.name)
        namespaces = [
            (key, value)
            for key, value in source_dict.items()
            if isinstance(value, namespace.Namespace)
        ]

        def split_long_line(line, prefix='\n', max_length=80):
            parts = line.split()
            lines = []
            one = []
            for part in parts:
                if len(' '.join(one + [part])) > max_length - len(prefix):
                    lines.append(one)
                    one = []
                one.append(part)
            lines.append(one)
            lines.insert(0, '')
            return prefix.join([' '.join(x) for x in lines])

        for an_option in options:
            if namespace_name:
                option_name = "%s.%s" % (namespace_name, an_option.name)
            else:
                option_name = an_option.name
            option_value = str(an_option)
            if isinstance(option_value, six.text_type):
                option_value = option_value.encode('utf8')

            comment_line = '%s (default: %r)' % (
                an_option.doc or '',
                an_option.default
            )
            comment_lines = split_long_line(comment_line, '\n# ').lstrip()
            print(comment_lines, file=output_stream)

            option_format = '%s=%r'
            print(option_format % (option_name.replace('.', '__'),
                                   option_value),
                  file=output_stream)
        for key, a_namespace in namespaces:
            if namespace_name:
                namespace_label = ''.join((namespace_name, '.', key))
            else:
                namespace_label = key
            print('', file=output_stream)
            ValueSource.write(
                a_namespace,
                namespace_name=namespace_label,
                output_stream=output_stream
            )
