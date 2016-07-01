# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function
import json
from configman.def_sources import for_mappings


def setup_definitions(source, destination):
    try:
        json_dict = json.loads(source)
    except ValueError:
        with open(source) as j:
            json_dict = json.load(j)
    for_mappings.setup_definitions(json_dict, destination)
