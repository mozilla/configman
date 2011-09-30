import for_mappings

def setup_definitions(source, destination):
    module_dict = source.__dict__.copy()
    del module_dict['__builtins__']
    for_mappings.setup_definitions(module_dict, destination)

