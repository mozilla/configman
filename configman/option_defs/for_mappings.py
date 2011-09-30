import collections

import configman.namespace as nmsp
import configman.option as opt

#------------------------------------------------------------------------------
def setup_definitions(source, destination):
    for key, val in source.items():
        if key.startswith('__'):
            continue  # ignore these
        val_type = type(val)
        if val_type == opt.Option:
            destination[key] = val
            if not val.name:
                val.name = key
            val.set_value(val.default)
        elif isinstance(val, collections.Mapping):
            if 'name' in val and 'default' in val:
                # this is an Option in the form of a dict, not a Namespace
                destination[key] = d = opt.Option(**val)
            else:
                # this is a Namespace
                try:
                    destination[key] = d = nmsp.Namespace(doc=val._doc)
                except AttributeError:
                    destination[key] = d = nmsp.Namespace()
                # recurse!
                setup_definitions(val, d)
        elif val_type in [int, float, str, unicode]:
            destination[key] = opt.Option(name=key,
                                      doc=key,
                                      default=val)
        else:
            pass
