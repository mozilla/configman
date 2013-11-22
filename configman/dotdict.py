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


#------------------------------------------------------------------------------
def iteritems_breadth_first(a_mapping, include_dicts=False):
    """a generator that returns all the keys in a set of nested
    Mapping instances.  The keys take the form X.Y.Z"""
    subordinate_mappings = []
    for key, value in a_mapping.iteritems():
        if isinstance(value, collections.Mapping):
            subordinate_mappings.append((key, value))
            if include_dicts:
                yield key, value
        else:
            yield key, value
    for key, a_map in subordinate_mappings:
        for sub_key, value in iteritems_breadth_first(a_map, include_dicts):
            yield '%s.%s' % (key, sub_key), value


#==============================================================================
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

    We can even use combination keys:

        d = DotDict()
        d.x = DotDict()
        d.x.y = DotDict()
        d.x.y.a = 'Wilma'
        assert d['x.y.a'] == 'Wilma'
        assert d['x.y'].a == 'Wilma'
        assert d['x'].y.a == 'Wilma'
        assert d.x.y.a == 'Wilma'
        assert d.x.y['a'] == 'Wilma'
        assert d.x['y.a'] == 'Wilma'
        assert d['x'].y['a'] == 'Wilma'
        assert d['x']['y']['a'] == 'Wilma'

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

    #--------------------------------------------------------------------------
    def __init__(self, initializer=None):
        """the constructor allows for initialization from another mapping.

        parameters:
            initializer - a mapping of keys and values to be added to this
                          mapping."""
        self.__dict__['_key_order'] = []
        if isinstance(initializer, collections.Mapping):
            for key, value in iteritems_breadth_first(
                initializer,
                include_dicts=True
            ):
                if isinstance(value, collections.Mapping):
                    self[key] = self.__class__(value)
                else:
                    self[key] = value
        elif initializer is not None:
            raise TypeError('can only initialize with a Mapping')

    #--------------------------------------------------------------------------
    def __setattr__(self, key, value):
        """this function saves keys into the mapping's __dict__."""
        if key not in self._key_order:
            self._key_order.append(key)
        self.__dict__[key] = value

    #--------------------------------------------------------------------------
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

    #--------------------------------------------------------------------------
    def __delattr__(self, key):
        try:
            self._key_order.remove(key)
        except ValueError:
            # we must be trying to delete something that wasn't a key
            # the next line will catch the error if it still is one
            pass
        super(DotDict, self).__delattr__(key)

    #--------------------------------------------------------------------------
    def __getitem__(self, key):
        """define the square bracket operator to refer to the object's __dict__
        for fetching values.  It accepts keys in the form X.Y.Z"""
        key_split = key.split('.')
        current = self
        for k in key_split:
            current = getattr(current, k)
        return current

    #--------------------------------------------------------------------------
    def __setitem__(self, key, value):
        """define the square bracket operator to refer to the object's __dict__
        for setting values."""
        if '.' in key:
            self.assign(key, value)
        else:
            setattr(self, key, value)

    #--------------------------------------------------------------------------
    def __delitem__(self, key):
        """define the square bracket operator to refer to the object's __dict__
        for deleting values.
        examples:
           d = DotDict()
           d['a.b.c'] = 8
           assert isinstance(d.a, DotDict)
           assert isinstance(d.a.b, DotDict)
           del d['a.b.c']
           assert isinstance(d.a, DotDict)
           assert isinstance(d.a.b, DotDict)
           assert 'c' not in d.a.b

           d = DotDict()
           d['a.b.c'] = 8
           del d.a
           assert 'a' not in d
        """
        key_split = key.split('.')
        current = self
        for k in key_split[:-1]:
            current = getattr(current, k)
        current.__delattr__(key_split[-1])

    #--------------------------------------------------------------------------
    def __iter__(self):
        """redirect the default iterator to iterate over the object's __dict__
        making sure that it ignores the special '_' keys.  We want those items
        ignored or we risk infinite recursion, not with this function, but
        with the clients of this class deep within configman"""
        return iter(self._key_order)

    #--------------------------------------------------------------------------
    def __len__(self):
        """makes the len function also ignore the '_' keys"""
        return len(self._key_order)

    #--------------------------------------------------------------------------
    def keys_breadth_first(self, include_dicts=False):
        """a generator that returns all the keys in a set of nested
        DotDict instances.  The keys take the form X.Y.Z"""
        namespaces = []
        for key in self._key_order:
            if isinstance(getattr(self, key), DotDict):
                namespaces.append(key)
                if include_dicts:
                    yield key
            else:
                yield key
        for a_namespace in namespaces:
            for key in self[a_namespace].keys_breadth_first(include_dicts):
                yield '%s.%s' % (a_namespace, key)

    #--------------------------------------------------------------------------
    def assign(self, key, value):
        """an alternative method for assigning values to nested DotDict
        instances.  It accepts keys in the form of X.Y.Z.  If any nested
        DotDict instances don't yet exist, they will be created."""
        key_split = key.split('.')
        cur_dict = self
        for k in key_split[:-1]:
            try:
                cur_dict = cur_dict[k]
            except KeyError:
                cur_dict[k] = self.__class__()  # so that derived classes
                                                # remain true to type
                cur_dict = cur_dict[k]
        cur_dict[key_split[-1]] = value

    #--------------------------------------------------------------------------
    def parent(self, key):
        """when given a key of the form X.Y.Z, this method will return the
        parent DotDict of the 'Z' key."""
        parent_key = '.'.join(key.split('.')[:-1])
        if not parent_key:
            return None
        else:
            return self[parent_key]


#==============================================================================
class DotDictWithAcquisition(DotDict):
    """This mapping, a derivative of DotDict, has special semantics when
    nested with mappings of the same type.

        d = DotDictWithAcquisition()
        d.a = 23
        d.dd = DotDictWithAcquisition()
        assert d.dd.a == 23

    Nested instances of DotDictWithAcquisition, when faced with a key not
    within the local mapping, will defer to the parent DotDict to find a key.
    Only if the key is not found in the root of the nested mappings will the
    KeyError be raised.  This is similar to the "acquisition" system found in
    Zope.

        d = DotDictWithAcquisition()
        d.dd = DotDictWithAcquisition()
        try:
            d.dd.x
        except KeyError:
            print "'x' was not found in d.dd or in d"

    When used with keys of the form 'x.y.z', acquisition can allow it to return
    acquired values even if the intermediate keys don't exist:

        d = DotDictWithAcquisition()
        d.a = 39
        assert d['x.y.z.a'] == 39

    Interestingly, indexing each component individually will result in a
    KeyError:

        d = DotDictWithAcquisition()
        d.a = 39
        try:
            print d.x.y.z.a
        except KeyError, e:
            assert str(e) == 'x'

    This behavior seems inconsistent, but really works so by design.  The form
    d.x.y.z.a is really equivalent to:

        t0 = d.x
        t1 = t0.y
        t2 = t1.z
        result = t2.a

    When broken out into separate operations, we want key errors to happen.
    Contrarily, the form d['x.y.z.a'] is a single lookup operation that reveals
    that our goal is to get a value for 'a'.  Since this class has acquisition,
    and 'a' is defined in the base, it is perfectly allowable.
    """

    #--------------------------------------------------------------------------
    def __getitem__(self, key):
        """define the square bracket operator to refer to the object's __dict__
        for fetching values.  It accepts keys in the form 'x.y.z'"""
        key_split = key.split('.')
        last_index = len(key_split) - 1
        current = self
        for i, k in enumerate(key_split):
            try:
                current = getattr(current, k)
            except KeyError:
                if i == last_index:
                    raise
                temp_dict = DotDictWithAcquisition()
                temp_dict.__dict__['_parent'] = weakref.proxy(current)
                current = temp_dict
        return current

    #--------------------------------------------------------------------------
    def __setattr__(self, key, value):
        """this function saves keys into the mapping's __dict__.  If the
        item being added is another instance of DotDict, it makes a weakref
        proxy object of itself and assigns it to '_parent' in the incoming
        DotDict."""
        if isinstance(value, DotDict) and key != '_parent':
            value.__dict__['_parent'] = weakref.proxy(self)
        super(DotDictWithAcquisition, self).__setattr__(key, value)

    #--------------------------------------------------------------------------
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
