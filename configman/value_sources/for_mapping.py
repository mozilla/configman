# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import collections
import os
import sys

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
    def write(source_mapping, output_stream=sys.stdout):
        ValueSource._write_ini(source_mapping, output_stream=output_stream)

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
            option_value = str(an_option)
            if isinstance(option_value, unicode):
                option_value = option_value.encode('utf8')

            option_format = '%s=%r'
            print >>output_stream, option_format % (
              option_name.replace('.', '__'),
              option_value
            )
        for key, a_namespace in namespaces:
            if namespace_name:
                namespace_label = ''.join((namespace_name, '.', key))
            else:
                namespace_label = key
            print >> output_stream, ''
            ValueSource.write(
              a_namespace,
              namespace_name=namespace_label,
              output_stream=output_stream
            )
