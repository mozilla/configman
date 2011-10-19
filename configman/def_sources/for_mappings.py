import collections

import configman.converters as converters
import configman.namespace as namespace
import configman.option as option


#------------------------------------------------------------------------------
def setup_definitions(source, destination):
    for key, val in source.items():
        if key.startswith('__'):
            continue  # ignore these
        val_type = type(val)
        if val_type == option.Option:
            destination[key] = val
            if not val.name:
                val.name = key
            val.set_value(val.default)
        elif isinstance(val, collections.Mapping):
            if 'name' in val and 'default' in val:
                # this is an Option in the form of a dict, not a Namespace
                params = converters.str_dict_keys(val)
                destination[key] = d = option.Option(**params)  # FIXME: why is 'd' defined here?
            else:
                # this is a Namespace
                try:
                    destination[key] = d = namespace.Namespace(doc=val._doc)
                except AttributeError:
                    destination[key] = d = namespace.Namespace()
                # recurse!
                setup_definitions(val, d)
        elif val_type in [int, float, str, unicode]:
            destination[key] = option.Option(name=key,
                                      doc=key,
                                      default=val)
