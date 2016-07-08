# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function
from functools import wraps


#------------------------------------------------------------------------------
def memoize(max_cache_size=1000):
    """Python 2.4 compatible memoize decorator.
    It creates a cache that has a maximum size.  If the cache exceeds the max,
    it is thrown out and a new one made.  With such behavior, it is wise to set
    the cache just a little larger that the maximum expected need.

    Parameters:
      max_cache_size - the size to which a cache can grow
    """
    def wrapper(f):
        @wraps(f)
        def fn(*args, **kwargs):
            if kwargs:
                key = (args, tuple(kwargs.items()))
            else:
                key = args
            try:
                return fn.cache[key]
            except KeyError:
                if fn.count >= max_cache_size:
                    fn.cache = {}
                    fn.count = 0
                result = f(*args, **kwargs)
                fn.cache[key] = result
                fn.count += 1
                return result
            except TypeError:
                return f(*args, **kwargs)
        fn.cache = {}
        fn.count = 0
        return fn
    return wrapper
