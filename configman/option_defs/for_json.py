import json

import for_mappings

def setup_definitions(source, destination):
    json_dict = json.loads(source)
    for_mappings.setup_definitions(json_dict, destination)

