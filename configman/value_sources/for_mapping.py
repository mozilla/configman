# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import collections
import os

from configman.value_sources.source_exceptions import CantHandleTypeException

from configman.dotdict import DotDict
from configman.memoize import memoize


can_handle = (
    os.environ,
    collections.Mapping,
)


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

