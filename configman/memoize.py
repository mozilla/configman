# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is configman
#
# The Initial Developer of the Original Code is
# Mozilla Foundation
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#    K Lars Lohn, lars@mozilla.com
#    Peter Bengtsson, peterbe@mozilla.com
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

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
            except TypeError, x:
                return f(*args, **kwargs)
        fn.cache = {}
        fn.count = 0
        return fn
    return wrapper


