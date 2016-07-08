# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function

import json
import collections
import six
import sys

from configman.converters import (
    to_string_converters,
    to_str
)
from configman.namespace import Namespace
from configman.option import Option, Aggregation

from configman.value_sources.source_exceptions import (
    ValueException,
    NotEnoughInformationException,
    CantHandleTypeException
)

from configman.dotdict import DotDict
from configman.memoize import memoize

can_handle = (
    six.binary_type,
    six.text_type,
    json
)

file_name_extension = 'json'


#==============================================================================
class LoadingJsonFileFailsException(ValueException):
    pass


#==============================================================================
class ValueSource(object):

    #--------------------------------------------------------------------------
    def __init__(self, source, the_config_manager=None):
        self.values = None
        if source is json:
            try:
                app = the_config_manager._get_option('admin.application')
                source = "%s.%s" % (app.value.app_name, file_name_extension)
            except (AttributeError, KeyError):
                raise NotEnoughInformationException(
                    "Can't setup an json file without knowing the file name"
                )
        if isinstance(source, (six.binary_type, six.text_type)):
            source = to_str(source)
        if (
            isinstance(source, six.string_types)
            and source.endswith(file_name_extension)
        ):
            try:
                with open(source) as fp:
                    self.values = json.load(fp)
            except IOError as x:
                # The file doesn't exist.  That's ok, we'll give warning
                # but this isn't a fatal error
                import warnings
                warnings.warn("%s doesn't exist" % source)
                self.values = {}
            except ValueError:
                raise LoadingJsonFileFailsException(
                    "Cannot load json: %s" % str(x)
                )
        else:
            raise CantHandleTypeException()

    #--------------------------------------------------------------------------
    @memoize()
    def get_values(self, config_manager, ignore_mismatches, obj_hook=DotDict):
        if isinstance(self.values, obj_hook):
            return self.values
        return obj_hook(self.values)

    #--------------------------------------------------------------------------
    @staticmethod
    def recursive_default_dict():
        return collections.defaultdict(ValueSource.recursive_default_dict)

    #--------------------------------------------------------------------------
    @staticmethod
    def write(source_dict, output_stream=sys.stdout):
        json_dict = ValueSource.recursive_default_dict()
        for qkey in source_dict.keys_breadth_first(include_dicts=True):
            val = source_dict[qkey]
            if isinstance(val, Namespace):
                continue
            d = json_dict
            for x in qkey.split('.'):
                d = d[x]
            if isinstance(val, Option):
                for okey, oval in six.iteritems(val.__dict__):
                    try:
                        d[okey] = to_string_converters[type(oval)](oval)
                    except KeyError:
                        d[okey] = str(oval)
                d['default'] = d['value']
            elif isinstance(val, Aggregation):
                d['name'] = val.name
                fn = val.function
                d['function'] = to_string_converters[type(fn)](fn)
        json.dump(json_dict, output_stream)
