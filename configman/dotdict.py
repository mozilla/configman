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


import collections
import weakref



class DotDict(collections.MutableMapping):
    """This class is a mapping that stores its items within the __dict__
    of a regular class.  This means that items can be access with either
    the regular square bracket notation or dot notation of class instance
    attributes:

        d = DotDict()
        d['a'] = 23
        assert d['a'] == 23
        assert d.a == 23
        d.b = 17
        assert d['b'] == 17
        assert d.b == 17

    Because it is a Mapping and key lookup for mappings requires the raising of
    a KeyError when a Key is missing, KeyError is used when an AttributeError
    might normally be expected:

        d = DotDict()
        try:
            d.a
        except KeyError:
            print 'yep, we got a KeyError'
        except AttributeError:
            print 'nope, this will never happen'
    """

    def __init__(self, initializer=None):
        """the constructor allows for initialization from another mapping.

        parameters:
            initializer - a mapping of keys and values to be added to this
                          mapping."""
        if isinstance(initializer, collections.Mapping):
            self.__dict__.update(initializer)
        elif initializer is not None:
            raise TypeError('can only initialize with a Mapping')

    def __setattr__(self, key, value):
        """this function saves keys into the mapping's __dict__."""
        self.__dict__[key] = value

    def __getattr__(self, key):
        """this function is called when the key wasn't found in self.__dict__.
        all that is left to do is raise the KeyError."""
        # the copy.deepcopy function will try to probe this class for an
        # instance of __deepcopy__.  If an AttributeError is raised, then
        # copy.deepcopy goes on with out it.  However, this class raises
        # a KeyError instead and copy.deepcopy can't handle it.  So we
        # make sure that any missing attribute that begins with '__'
        # raises an AttributeError instead of KeyError.
        if key.startswith('__') and key.endswith('__'):
            raise AttributeError(key)
        raise KeyError(key)

    def __getitem__(self, key):
        """define the square bracket operator to refer to the object's __dict__
        for fetching values."""
        return getattr(self, key)

    def __setitem__(self, key, value):
        """define the square bracket operator to refer to the object's __dict__
        for setting values."""
        setattr(self, key, value)

    def __delitem__(self, key):
        """define the square bracket operator to refer to the object's __dict__
        for deleting values."""
        del self.__dict__[key]

    def __iter__(self):
        """redirect the default iterator to iterate over the object's __dict__
        making sure that it ignores the special '_' keys.  We want those items
        ignored or we risk infinite recursion, not with this function, but
        with the clients of this class deep within configman"""
        return (k for k in self.__dict__
                     if not k.startswith('_'))

    def __len__(self):
        """makes the len function also ignore the '_' keys"""
        return len([x for x in self.__iter__()])


class DotDictWithAcquisition(DotDict):
    """This mapping, a derivative of DotDict, has special semantics when
    nested with mappings of the same type.

        d = DotDict()
        d.a = 23
        d.dd = DotDict()
        assert d.dd.a == 23

    Nested instances of DotDict, when faced with a key not within the local
    mapping, will defer to the parent DotDict to find a key.  Only if the key
    is not found in the root of the nested mappings will the KeyError be
    raised.  This is similar to the "acquisition" system found in Zope.

        d = DotDict()
        d.dd = DotDict()
        try:
            d.dd.x
        except KeyError:
            print "'x' was not found in d.dd or in d"
    """

    def __setattr__(self, key, value):
        """this function saves keys into the mapping's __dict__.  If the
        item being added is another instance of DotDict, it makes a weakref
        proxy object of itself and assigns it to '_parent' in the incoming
        DotDict."""
        if isinstance(value, DotDict) and key != '_parent':
            value._parent = weakref.proxy(self)
        self.__dict__[key] = value

    def __getattr__(self, key):
        """if a key is not found in the __dict__ using the regular python
        attribute reference algorithm, this function will try to get it from
        parent class."""
        if key == '_parent':
            raise AttributeError('_parent')
        try:
            return getattr(self._parent, key)
        except AttributeError:  # no parent attribute
            # the copy.deepcopy function will try to probe this class for an
            # instance of __deepcopy__.  If an AttributeError is raised, then
            # copy.deepcopy goes on with out it.  However, this class raises
            # a KeyError instead and copy.deepcopy can't handle it.  So we
            # make sure that any missing attribute that begins with '__'
            # raises an AttributeError instead of KeyError.
            if key.startswith('__'):
                raise
            raise KeyError(key)
