# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function

import collections
import weakref
import six

from configman.orderedset import OrderedSet
from configman.memoize import memoize


#------------------------------------------------------------------------------
def iteritems_breadth_first(a_mapping, include_dicts=False):
    """a generator that returns all the keys in a set of nested
    Mapping instances.  The keys take the form X.Y.Z"""
    subordinate_mappings = []
    for key, value in six.iteritems(a_mapping):
        if isinstance(value, collections.Mapping):
            subordinate_mappings.append((key, value))
            if include_dicts:
                yield key, value
        else:
            yield key, value
    for key, a_map in subordinate_mappings:
        for sub_key, value in iteritems_breadth_first(a_map, include_dicts):
            yield '%s.%s' % (key, sub_key), value


#------------------------------------------------------------------------------
def configman_keys(a_mapping):
    """return a DotDict that is a copy of the provided mapping with keys
    transformed into a configman compatible form:
     if the key is not all uppercase then
        all doubled underscores will be replaced
        with the '.' character.

    This has a specific use with the os.environ.  Linux shells generally do not
    allow the dot character in an identifier.  Configman relies on the
    dot character to separate namespaces.  If the environment is processed
    through this function, then doubled underscores will be interpretted as if
    they were the dot character.
    """
    configmanized_keys_dict = DotDict()
    for k, v in iteritems_breadth_first(a_mapping):
        if '__' in k and k != k.upper():
            k = k.replace('__', '.')
        configmanized_keys_dict[k] = v
    return configmanized_keys_dict


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
            print('yep, we got a KeyError')
        except AttributeError:
            print('nope, this will never happen')
    """

    #--------------------------------------------------------------------------
    def __init__(self, initializer=None):
        """the constructor allows for initialization from another mapping.

        parameters:
            initializer - a mapping of keys and values to be added to this
                          mapping."""
        self.__dict__['_key_order'] = OrderedSet()
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
        self._key_order.add(key)
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
            self._key_order.discard(key)
        except ValueError:
            # we must be trying to delete something that wasn't a key
            # the next line will catch the error if it still is one
            pass
        super(DotDict, self).__delattr__(key)

    #--------------------------------------------------------------------------
    def __getitem__(self, key):
        """define the square bracket operator to refer to the object's __dict__
        for fetching values.  It accepts keys in the form X.Y.Z"""
        try:
            key_split = key.split('.')
        except AttributeError:
            key_split = [key]
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

    def __str__(self):
        out = six.StringIO()
        for key in self.keys_breadth_first(False):
            value = self[key]
            indent = '\t' * key.count('.')
            if isinstance(value, collections.Mapping):
                value = str(value)  # recurse!
            print('{0}{1}: {2}'.format(indent, key, repr(value)), file=out)
        return out.getvalue().strip()


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
            print("'x' was not found in d.dd or in d")

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
            print(d.x.y.z.a)
        except KeyError as e:
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
            if six.PY2:
                _parent = self._parent
            else:
                _parent = object.__getattribute__(self, '_parent')
            return getattr(_parent, key)
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


#------------------------------------------------------------------------------
def create_key_translating_dot_dict(
    new_class_name,
    translation_tuples,
    base_class=DotDict
):
    """this function will generate a DotDict derivative class that has key
    translation built in.  If the key is not found, translations (as specified
    by the translation_tuples) are performed on the key and the lookup is
    tried again.  Only on failure of this second lookup will the KeyError
    exception be raised.

    parameters:
        new_class_name - the name of the returned class
        translation_tuples - a sequence of 2-tuples of the form:
                             (original_substring, substitution_string)
        base_class - the baseclass on which this new class is to be based
    """
    #==========================================================================
    class DotDictWithKeyTranslations(base_class):

        def __init__(self, *args, **kwargs):
            self.__dict__['_translation_tuples'] = translation_tuples
            super(DotDictWithKeyTranslations, self).__init__(*args, **kwargs)

        #----------------------------------------------------------------------
        @memoize()
        def _translate_key(self, key):
            for original, replacement in self._translation_tuples:
                key = key.replace(original, replacement)
            return key

        #----------------------------------------------------------------------
        def assign(self, key, value):
            super(DotDictWithKeyTranslations, self).assign(
                self._translate_key(key),
                value
            )

        #----------------------------------------------------------------------
        def __setattr__(self, key, value):
            super(DotDictWithKeyTranslations, self).__setattr__(
                self._translate_key(key),
                value
            )

        #----------------------------------------------------------------------
        def __getattr__(self, key):
            alt_key = self._translate_key(key)
            if alt_key == key:
                return super(DotDictWithKeyTranslations, self).__getattr__(key)
            try:
                return getattr(self, alt_key)
            except KeyError:
                raise KeyError(key)

        #----------------------------------------------------------------------
        def __delattr__(self, key):
            super(DotDictWithKeyTranslations, self).__delattr__(
                self._translate_key(key)
            )

    if six.PY2:
        new_class_name = six.binary_type(new_class_name)
    DotDictWithKeyTranslations.__name__ = new_class_name
    return DotDictWithKeyTranslations
