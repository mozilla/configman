from __future__ import absolute_import, division, print_function
import collections
import six

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# TODO: This is a temporary dispatch mechanism.  This whole system
# is to be changed to automatic discovery of the for_* modules

from configman.def_sources import for_mappings
from configman.def_sources import for_modules
from configman.def_sources import for_json

definition_dispatch = {
    collections.Mapping: for_mappings.setup_definitions,
    type(for_modules): for_modules.setup_definitions,
    six.binary_type: for_json.setup_definitions,
    six.text_type: for_json.setup_definitions,
}


try:
    from configman.def_sources import for_argparse
    import argparse
    definition_dispatch[argparse.ArgumentParser] = \
        for_argparse.setup_definitions
except ImportError:
    # silently ignore that argparse doesn't exist
    pass


class UnknownDefinitionTypeException(Exception):
    pass


def setup_definitions(source, destination):
    target_setup_func = None
    try:
        target_setup_func = definition_dispatch[type(source)]
    except KeyError:
        for a_key in definition_dispatch.keys():
            if isinstance(source, a_key):
                target_setup_func = definition_dispatch[a_key]
                break
        if not target_setup_func:
            raise UnknownDefinitionTypeException(repr(type(source)))
    target_setup_func(source, destination)
