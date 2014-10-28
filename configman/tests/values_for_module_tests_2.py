# this file is for testing modules as an overlay source

# there are two ways to get make configman ignore extra symbols in modules
# first is the same way that is used in Mappings:
always_ignore_mismatches = True
# the second method is demonstrated in the values_for_module_tests_3.py file

from configman.dotdict import DotDict  # will be ignored by configman
from datetime import datetime, timedelta  # will be ignored by configman


a = 99
b = 86
c = 13  # will be ignored by configman

n = DotDict()
n.x = datetime(1960, 5, 4, 15, 10)
n.y = timedelta(1)



