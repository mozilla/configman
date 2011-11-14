import collections
import os

from source_exceptions import CantHandleTypeException

can_handle = (os.environ,
              collections.Mapping,
             )


class ValueSource(object):
    def __init__(self, source, the_config_manager=None):
        if source is os.environ:
            self.always_ignore_mismatches = True
        elif isinstance(source, collections.Mapping):
            self.always_ignore_mismatches = False
        else:
            raise CantHandleTypeException(
                                      "don't know how to handle %s." % source)
        self.source = source

    def get_values(self, config_manager, ignore_mismatches):
        return self.source
