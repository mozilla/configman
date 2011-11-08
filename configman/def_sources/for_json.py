import json
import for_mappings


def setup_definitions(source, destination):
    try:
        json_dict = json.loads(source)
    except ValueError:
        with open(source) as j:
            json_dict = json.load(j)
    for_mappings.setup_definitions(json_dict, destination)
