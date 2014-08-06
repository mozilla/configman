# this file is for testing modules as an overlay source

# there are two ways to get make configman ignore extra symbols in modules
# this is the second method, listing symbols to be ignored in
# 'ignore_symbol_list':
ignore_symbol_list = [
    'DotDict',
    'timedelta',
    'date',
    '__doc__',
    'Alpha',
    'RequiredConfig'
]

from configman.dotdict import DotDict
from configman import RequiredConfig
from datetime import timedelta, date


b = 'now is the time'

n = DotDict()
n.y = timedelta(1)
n.z = date(1960, 5, 4)


class Alpha(RequiredConfig):
    required_config = {
        'host': 'localhost',
        'port':  5432,
    }

dynamic_load = Alpha