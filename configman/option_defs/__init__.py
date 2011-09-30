import collections


# TODO: This is a temporary dispatch mechanism.  This whole system
# is to be changed to automatic discovery of the for_* modules

import for_mappings
import for_modules
#import for_list
import for_json
#import for_class

definition_dispatch = { collections.Mapping: for_mappings.setup_definitions,
                        type(for_modules): for_modules.setup_definitions,
                        #list: for_list.setup_definitions,
                        str: for_json.setup_definitions,
                        #type: for_class.setup_definitions,
                      }

class UnknownDefinitionTypeException(Exception):
    pass

def setup_definitions(source, destination):
    target_setup_func = None
    try:
        target_setup_func = definition_dispatch[type(source)]
    except KeyError, x:
        for a_key in definition_dispatch.keys():
            if isinstance(source, a_key):
                target_setup_func = definition_dispatch[a_key]
                break
        if not target_setup_func:
            raise UnknownDefinitionTypeException(repr(type(source)))
    target_setup_func(source, destination)
