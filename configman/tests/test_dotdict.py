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

import unittest
from configman.dotdict import (
    DotDict,
    DotDictWithAcquisition,
    iteritems_breadth_first,
)


#==============================================================================
class TestCase(unittest.TestCase):

    #--------------------------------------------------------------------------
    def test_setting_and_getting(self):
        dd = DotDict()
        dd.name = u'Peter'
        dd['age'] = 31
        setattr(dd, 'gender', 'male')

        self.assertEqual(dd['name'], u'Peter')
        self.assertEqual(dd.age, 31)
        self.assertEqual(dd['gender'], dd.gender)
        self.assertEqual(dd.get('name'), u'Peter')
        self.assertEqual(getattr(dd, 'gender'), 'male')
        self.assertEqual(dd.get('gender'), 'male')
        self.assertEqual(dd.get('junk'), None)
        self.assertEqual(dd.get('junk', 'trash'), 'trash')

    #--------------------------------------------------------------------------
    def test_getting_and_setting_2(self):
        d = DotDict()
        d['a'] = 17
        self.assertEqual(d['a'], 17)
        self.assertEqual(d.a, 17)
        d['b.d'] = 23
        self.assertEqual(d['b.d'], 23)
        self.assertEqual(d['b']['d'], 23)
        self.assertEqual(d.b['d'], 23)
        self.assertEqual(d.b.d, 23)

    #--------------------------------------------------------------------------
    def test_access_combos(self):
        d = DotDictWithAcquisition()
        d.x = DotDictWithAcquisition()
        d.x.y = DotDictWithAcquisition()
        d.x.y.a = 'Wilma'
        self.assertEqual(d['x.y.a'], 'Wilma')
        self.assertEqual(d['x.y'].a, 'Wilma')
        self.assertEqual(d['x'].y.a, 'Wilma')
        self.assertEqual(d.x.y.a, 'Wilma')
        self.assertEqual(d.x.y['a'], 'Wilma')
        self.assertEqual(d.x['y.a'], 'Wilma')
        self.assertEqual(d['x'].y['a'], 'Wilma')
        self.assertEqual(d['x']['y']['a'], 'Wilma')
        self.assertTrue(isinstance(d.x, DotDictWithAcquisition))
        self.assertTrue(isinstance(d.x.y, DotDictWithAcquisition))

    #--------------------------------------------------------------------------
    def test_access_combos_2(self):
        d = DotDict()
        d.x = DotDict()
        d.x.y = DotDict()
        d.x.y.a = 'Wilma'
        self.assertEqual(d['x.y.a'], 'Wilma')
        self.assertEqual(d['x.y'].a, 'Wilma')
        self.assertEqual(d['x'].y.a, 'Wilma')
        self.assertEqual(d.x.y.a, 'Wilma')
        self.assertEqual(d.x.y['a'], 'Wilma')
        self.assertEqual(d.x['y.a'], 'Wilma')
        self.assertEqual(d['x'].y['a'], 'Wilma')
        self.assertEqual(d['x']['y']['a'], 'Wilma')

    #--------------------------------------------------------------------------
    def test_deleting_attributes(self):
        dd = DotDict()
        dd.name = 'peter'
        dd.age = 31
        del dd.name
        del dd.age
        self.assertEqual(dict(dd), {})

    #--------------------------------------------------------------------------
    def test_key_errors(self):
        dd = DotDict()

        try:
            dd.name
            raise AssertionError("should have raised KeyError")
        except KeyError:
            pass
        #self.assertRaises(KeyError, getattr(dd, 'name'))
        self.assertEqual(dd.get('age'), None)
        self.assertEqual(dd.get('age', 0), 0)

    #--------------------------------------------------------------------------
    def test_nesting(self):
        d = DotDictWithAcquisition()
        d.e = 1
        d.dd = DotDictWithAcquisition()
        d.dd.f = 2
        d.dd.ddd = DotDictWithAcquisition()
        d.dd.ddd.g = 3
        d['a'] = 21
        d.dd['a'] = 22

        self.assertEqual(d.dd.ddd.e, 1)
        self.assertEqual(d.dd.e, 1)
        self.assertEqual(d.e, 1)

        self.assertEqual(d.dd.ddd.a, 22)
        self.assertEqual(d.dd.a, 22)
        self.assertEqual(d.a, 21)

        self.assertEqual(d.dd.ddd.f, 2)
        self.assertEqual(d.dd.f, 2)
        try:
            d.f
            raise AssertionError("should have raised KeyError")
        except KeyError:
            pass
        self.assertEqual(d.dd.dd.dd.dd.ddd.f, 2)
        self.assertEqual(d.dd.ddd.dd.ddd.dd.ddd.e, 1)

        self.assertEqual(len(d), 3)
        _keys = [x for x in d]
        self.assertEqual(_keys, ['e', 'dd', 'a'])
        self.assertEqual(d.keys(), ['e', 'dd', 'a'])
        self.assertEqual(list(d.iterkeys()), ['e', 'dd', 'a'])

        d.xxx = DotDictWithAcquisition()
        d.xxx.p = 69
        del d.xxx.p
        try:
            d.xxx.p
            assert 0
        except KeyError:
            pass

        # initialization
        d.yy = DotDictWithAcquisition(dict(foo='bar'))
        self.assertEqual(d.yy.foo, 'bar')

        # clashing names
        d.zzz = DotDictWithAcquisition()
        d.zzz.Bool = 'True'
        d.zzz.www = DotDictWithAcquisition()
        self.assertEqual(d.zzz.www.Bool, 'True')
        d.zzz.www.Bool = 'False'
        self.assertEqual(d.zzz.www.Bool, 'False')

        # test __setitem__ and __getitem__
        d = DotDictWithAcquisition()
        d.a = 17
        d['dd'] = DotDictWithAcquisition()
        self.assertEqual(d.dd.a, 17)
        d['dd']['ddd'] = DotDictWithAcquisition()
        self.assertEqual(d.dd.ddd.a, 17)
        self.assertEqual(d['dd']['ddd'].a, 17)
        self.assertEqual(d['dd']['ddd']['dd'].a, 17)

    #--------------------------------------------------------------------------
    def test_key_errors__with_dunder(self):
        dd = DotDict()
        try:
            dd['__something']
            raise AssertionError("should have raised KeyError")
        except KeyError:
            pass

        try:
            dd.__something
            raise AssertionError("should have raised KeyError")
        except KeyError:
            pass

        try:
            getattr(dd, '__something')
            raise AssertionError("should have raised KeyError")
        except KeyError:
            pass

        self.assertEqual(dd.get('__something'), None)
        self.assertEqual(dd.get('__something', 0), 0)

    #--------------------------------------------------------------------------
    def test_attribute_errors__with_dunders(self):
        dd = DotDict()
        try:
            dd['__something__']
            raise AssertionError("should have raised AttributeError")
        except AttributeError:
            pass

        try:
            dd.__something__
            raise AssertionError("should have raised AttributeError")
        except AttributeError:
            pass

        try:
            getattr(dd, '__something__')
            raise AssertionError("should have raised AttributeError")
        except AttributeError:
            pass

        # you just can't use the high-level function .get()
        # on these Python special keys
        self.assertRaises(AttributeError, dd.get, '__something__')

    #--------------------------------------------------------------------------
    def test_keys_breadth_first(self):
        d = DotDict()
        d.a = 1
        d.b = 2
        d.c = 3
        d.d = DotDict()
        d.d.a = 4
        d.d.b = 5
        d.d.c = 6
        d.d.d = DotDict()
        d.d.d.a = 7
        d.e = DotDict()
        d.e.a = 8
        expected = ['a', 'b', 'c', 'd.a', 'd.b', 'd.c', 'd.d.a', 'e.a']
        actual = [x for x in d.keys_breadth_first()]
        actual.sort()
        self.assertEqual(expected, actual)

    #--------------------------------------------------------------------------
    def test_dot_lookup(self):
        d = DotDict()
        d.a = 1
        d.b = 2
        d.c = 3
        d.d = DotDict()
        d.d.a = 4
        d.d.b = 5
        d.d.c = 6
        d.d.d = DotDict()
        d.d.d.a = 7
        d.e = DotDict()
        d.e.a = 8

        self.assertEqual(d['a'], 1)
        self.assertEqual(d['b'], 2)
        self.assertEqual(d['c'], 3)
        self.assertEqual(d['d.a'], 4)
        self.assertEqual(d['d.b'], 5)
        self.assertEqual(d['d.c'], 6)
        self.assertEqual(d['d.d.a'], 7)
        self.assertEqual(d['e.a'], 8)

        self.assertTrue(isinstance(d['d'], DotDict))
        self.assertTrue(isinstance(d['d.d'], DotDict))

        self.assertRaises(
            KeyError,
            d.__getitem__,
            'x'
        )
        self.assertRaises(
            KeyError,
            d.__getitem__,
            'd.x'
        )
        self.assertRaises(
            KeyError,
            d.__getitem__,
            'd.d.x'
        )

    #--------------------------------------------------------------------------
    def test_parent(self):
        d = DotDict()
        d.a = 1
        d.b = 2
        d.c = 3
        d.d = DotDict()
        d.d.a = 4
        d.d.b = 5
        d.d.c = 6
        d.d.d = DotDict()
        d.d.d.a = 7
        d.e = DotDict()
        d.e.a = 8

        self.assertEqual(d.parent('d.d.a'), d['d.d'])
        self.assertTrue(d.parent('d') is None)

    #--------------------------------------------------------------------------
    def test_assign(self):
        d = DotDict()
        d.assign('a.b', 10)
        self.assertEqual(d['a.b'], 10)
        self.assertTrue(isinstance(d.a, DotDict))
        self.assertEqual(d.a['b'], 10)

    #--------------------------------------------------------------------------
    def test_iteritems_breadth_first(self):
        d = {
            'a': {'aa': 13, 'ab': 14},
            'b': {'ba': {'baa': 0, 'bab': 1}, 'bb': {'bba': 2}},
            'c': 9,
            'd': {'dd': 2}
        }
        e = [
            ('a.aa', 13),
            ('a.ab', 14),
            ('b.ba.baa', 0),
            ('b.ba.bab', 1),
            ('b.bb.bba', 2),
            ('c', 9),
            ('d.dd', 2)
        ]
        a = [x for x in iteritems_breadth_first(d)]
        e = sorted(e)
        a = sorted(a)
        self.assertEqual(a, e)

        # try a round trip
        dd = DotDict()
        for k, v in a:
            dd.assign(k, v)
        ddkv = sorted(iteritems_breadth_first(dd))
        self.assertEqual(e, ddkv)

    #--------------------------------------------------------------------------
    def test_copy_constructor_1(self):
        d = {'d': {'x': 10}}
        dd = DotDict(d)
        self.assertTrue('d' in dd)
        d = {'d': {}}
        dd = DotDict(d)
        self.assertTrue('d' in dd)

    #--------------------------------------------------------------------------
    def test_copy_constructor_2(self):
        d = {
            'a': {'aa': 13, 'ab': 14},
            'b': {'ba': {'baa': 0, 'bab': 1}, 'bb': {'bba': 2}},
            'c': 9,
            'd': {'dd': 2}
        }
        dd = DotDictWithAcquisition(d)
        e = [
            ('a.aa', 13),
            ('a.ab', 14),
            ('b.ba.baa', 0),
            ('b.ba.bab', 1),
            ('b.bb.bba', 2),
            ('c', 9),
            ('d.dd', 2)
        ]
        a = [x for x in iteritems_breadth_first(d)]
        e = sorted(e)
        a = sorted(a)
        self.assertEqual(a, e)
        self.assertTrue(isinstance(dd.a, DotDictWithAcquisition))

    #--------------------------------------------------------------------------
    def test_dot_dupe_fix(self):
        # a bug caused an interal structure to have duplicates if a key was
        # changed using two different access methods.  This caused the
        # 'keys_breadth_first' method to return duplicate keys.  This test
        # insures that condition doesn't still trouble 'keys_breadth_first'
        d = DotDict()
        d.m = DotDict()
        d.m.m = 17
        d['m.m'] = 23
        keys = [x for x in d.keys_breadth_first()]
        self.assertTrue('m.m' in keys)
        self.assertEqual(len(keys), 1)
