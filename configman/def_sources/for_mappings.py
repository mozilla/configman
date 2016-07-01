# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function

import collections

from configman.converters import str_dict_keys
from configman.namespace import Namespace
from configman.option import (
    Option,
    Aggregation,
)


#------------------------------------------------------------------------------
def setup_definitions(source, destination):
    for key, val in source.items():
        if key.startswith('__'):
            continue  # ignore these
        if isinstance(val, Option):
            destination[key] = val
            if not val.name:
                val.name = key
            val.set_value(val.default)
        elif isinstance(val, Aggregation):
            destination[key] = val
        elif isinstance(val, collections.Mapping):
            if 'name' in val and 'default' in val:
                # this is an Option in the form of a dict, not a Namespace
                if key == 'not_for_definition' and val is True:
                    continue  # ignore this element
                params = str_dict_keys(val)
                destination[key] = Option(**params)
            elif 'function' in val:  # this is an Aggregation
                params = str_dict_keys(val)
                destination[key] = Aggregation(**params)
            else:
                # this is a Namespace
                if key not in destination:
                    try:
                        destination[key] = Namespace(doc=val._doc)
                    except AttributeError:
                        destination[key] = Namespace()
                # recurse!
                setup_definitions(val, destination[key])
        else:
            destination[key] = Option(name=key,
                                      doc=key,
                                      default=val)
