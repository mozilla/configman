# this file is for testing modules as an overlay source

# none of the symbols in this file have been set to be ignored.  That means
# that configman will warn that there are extra symbols in this file that it
# doesn't know about.  Further, if '--admin.strict' is enabled, the extra
# symbols are a fatal error

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