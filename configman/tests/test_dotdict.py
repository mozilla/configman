# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function

import six
import unittest
from configman.dotdict import (
    DotDict,
    DotDictWithAcquisition,
    iteritems_breadth_first,
    configman_keys,
    create_key_translating_dot_dict
)
from configman.orderedset import OrderedSet
from configman import Namespace


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
        self.assertEqual(list(d.keys()), ['e', 'dd', 'a'])
        self.assertEqual(list(six.iterkeys(d)), ['e', 'dd', 'a'])

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

    #--------------------------------------------------------------------------
    def test_configmanize_dict(self):
        d = {
            "HELLO": "howdy",
            "JELL__O": "gelatin",
            "database_hostname": 'localhost',
            "resources__postgres__database_hostname": 'more-localhost',
        }
        r = configman_keys(d)
        self.assertTrue("HELLO" in r)
        self.assertTrue("JELL__O" in r)
        self.assertTrue("database_hostname" in r)
        self.assertTrue("resources__postgres__database_hostname" not in r)
        self.assertTrue("resources.postgres.database_hostname" in r)

    #--------------------------------------------------------------------------
    def test_verify_key_order(self):
        d = DotDict()
        d['a.b.c'] = 17
        d['a.b.d'] = 8
        d['a.x'] = 99
        d['b'] = 21
        self.assertTrue(isinstance(d._key_order, OrderedSet))
        # the keys should be in order of insertion within each level of the
        # nested dicts
        keys_in_breadth_first_order = [
            'a', 'b', 'a.b', 'a.x', 'a.b.c', 'a.b.d'
        ]
        self.assertEqual(
            keys_in_breadth_first_order,
            [k for k in d.keys_breadth_first(include_dicts=True)]
        )

    #--------------------------------------------------------------------------
    def test_translating_key_dot_dict(self):
        HyphenUnderscoreDict = create_key_translating_dot_dict(
            "HyphenUnderscoreDict",
            (('-', '_'),)
        )
        d = HyphenUnderscoreDict()
        d['a-a.b-b.c-c'] = 17
        d['a-a.b_b.d-d'] = 8
        d['a_a.x-x'] = 99
        d['b-b'] = 21
        self.assertTrue(isinstance(d._key_order, OrderedSet))
        # the keys should be in order of insertion within each level of the
        # nested dicts
        keys_in_breadth_first_order = [
            'a_a', 'b_b', 'a_a.b_b', 'a_a.x_x', 'a_a.b_b.c_c', 'a_a.b_b.d_d'
        ]
        self.assertEqual(
            keys_in_breadth_first_order,
            [k for k in d.keys_breadth_first(include_dicts=True)]
        )

        self.assertEqual(d.a_a.b_b.c_c, 17)
        self.assertEqual(d.a_a.b_b['c-c'], 17)
        self.assertEqual(d.a_a['b-b'].c_c, 17)
        self.assertEqual(d['a-a'].b_b.c_c, 17)
        self.assertEqual(d['a-a.b-b.c-c'], 17)
        self.assertEqual(d['a-a.b-b.c_c'], 17)
        self.assertEqual(d['a-a.b_b.c_c'], 17)
        self.assertEqual(d['a_a.b_b.c_c'], 17)

        del d['a-a.b-b.c-c']

        self.assertTrue('a-a.b-b.c-c' not in d)
        self.assertTrue('a-a.b-b.c_c' not in d)
        self.assertTrue('a-a.b_b.c_c' not in d)
        self.assertTrue('a_a.b_b.c_c' not in d)
        self.assertTrue('c-c' not in d['a_a']['b_b']._key_order)
        self.assertTrue('c_c' not in d['a_a']['b_b']._key_order)

        self.assertTrue(isinstance(d, HyphenUnderscoreDict))
        self.assertTrue(isinstance(d['a-a'], HyphenUnderscoreDict))
        self.assertTrue(isinstance(d.a_a, HyphenUnderscoreDict))
        self.assertTrue(isinstance(d.a_a.b_b, HyphenUnderscoreDict))

    #--------------------------------------------------------------------------
    def test_translating_key_dot_dict_with_acquisition(self):
        HyphenUnderscoreDictWithAcquisition = create_key_translating_dot_dict(
            "HyphenUnderscoreDictWithAcquisition",
            (('-', '_'),),
            base_class=DotDictWithAcquisition
        )
        d = HyphenUnderscoreDictWithAcquisition()
        d['a-a.b-b.c-c'] = 17
        d['a-a.b_b.d-d'] = 8
        d['a_a.x-x'] = 99
        d['b-b'] = 21
        self.assertTrue(isinstance(d._key_order, OrderedSet))
        # the keys should be in order of insertion within each level of the
        # nested dicts
        keys_in_breadth_first_order = [
            'a_a', 'b_b', 'a_a.b_b', 'a_a.x_x', 'a_a.b_b.c_c', 'a_a.b_b.d_d'
        ]
        self.assertEqual(
            keys_in_breadth_first_order,
            [k for k in d.keys_breadth_first(include_dicts=True)]
        )
        self.assertEqual(d.a_a.b_b.c_c, 17)
        self.assertEqual(d.a_a.b_b['c-c'], 17)
        self.assertEqual(d.a_a['b-b'].c_c, 17)
        self.assertEqual(d['a-a'].b_b.c_c, 17)
        self.assertEqual(d['a-a.b-b.c-c'], 17)
        self.assertEqual(d['a-a.b-b.c_c'], 17)
        self.assertEqual(d['a-a.b_b.c_c'], 17)
        self.assertEqual(d['a_a.b_b.c_c'], 17)

        del d['a-a.b-b.c-c']

        self.assertTrue('a-a.b-b.c-c' not in d)
        self.assertTrue('a-a.b-b.c_c' not in d)
        self.assertTrue('a-a.b_b.c_c' not in d)
        self.assertTrue('a_a.b_b.c_c' not in d)
        self.assertTrue('c-c' not in d['a_a']['b_b']._key_order)
        self.assertTrue('c_c' not in d['a_a']['b_b']._key_order)

        self.assertTrue(isinstance(d, HyphenUnderscoreDictWithAcquisition))
        self.assertTrue(
            isinstance(d['a-a'], HyphenUnderscoreDictWithAcquisition)
        )
        self.assertTrue(
            isinstance(d.a_a, HyphenUnderscoreDictWithAcquisition)
        )
        self.assertTrue(
            isinstance(d.a_a.b_b, HyphenUnderscoreDictWithAcquisition)
        )

        self.assertTrue(isinstance(d, HyphenUnderscoreDictWithAcquisition))
        self.assertTrue(isinstance(d.a_a, HyphenUnderscoreDictWithAcquisition))
        self.assertTrue(
            isinstance(d.a_a.b_b, HyphenUnderscoreDictWithAcquisition)
        )
        self.assertEqual(d.a_a.b_b['x_x'], 99)
        self.assertEqual(d.a_a.b_b.x_x, 99)
        self.assertEqual(d.a_a['b-b']['a-a'].x_x, 99)
        self.assertEqual(d.a_a['b-b']['a-a']['b-b']['a-a'].x_x, 99)

    #--------------------------------------------------------------------------
    def test_translating_key_namespace(self):
        HyphenUnderscoreNamespace = create_key_translating_dot_dict(
            "HyphenUnderscoreNamespace",
            (('-', '_'),),
            base_class=Namespace
        )
        d = HyphenUnderscoreNamespace()
        d.namespace('a-a')
        d.a_a.namespace('b-b')
        d.a_a['b-b'].add_option('c-c')
        d['a-a'].b_b.add_aggregation('d-d', lambda x, y, z: True)
        d['a_a'].add_option('x-x')
        d.add_option('b-b')
        self.assertTrue(isinstance(d._key_order, OrderedSet))
        # the keys should be in order of insertion within each level of the
        # nested dicts
        keys_in_breadth_first_order = [
            'a_a', 'b_b', 'a_a.b_b', 'a_a.x_x', 'a_a.b_b.c_c', 'a_a.b_b.d_d'
        ]
        self.assertEqual(
            keys_in_breadth_first_order,
            [k for k in d.keys_breadth_first(include_dicts=True)]
        )
        self.assertEqual(d.a_a.b_b.c_c.name, 'c-c')
        self.assertEqual(d.a_a.b_b['c-c'].name, 'c-c')
        self.assertEqual(d.a_a['b-b'].c_c.name, 'c-c')
        self.assertEqual(d['a-a'].b_b.c_c.name, 'c-c')
        self.assertEqual(d['a-a.b-b.c-c'].name, 'c-c')
        self.assertEqual(d['a-a.b-b.c_c'].name, 'c-c')
        self.assertEqual(d['a-a.b_b.c_c'].name, 'c-c')
        self.assertEqual(d['a_a.b_b.c_c'].name, 'c-c')

        del d['a-a.b-b.c-c']

        self.assertTrue('a-a.b-b.c-c' not in d)
        self.assertTrue('a-a.b-b.c_c' not in d)
        self.assertTrue('a-a.b_b.c_c' not in d)
        self.assertTrue('a_a.b_b.c_c' not in d)
        self.assertTrue('c-c' not in d['a_a']['b_b']._key_order)
        self.assertTrue('c_c' not in d['a_a']['b_b']._key_order)

        self.assertTrue(isinstance(d, HyphenUnderscoreNamespace))
        self.assertTrue(
            isinstance(d['a-a'], HyphenUnderscoreNamespace)
        )
        self.assertTrue(
            isinstance(d.a_a, HyphenUnderscoreNamespace)
        )
        self.assertTrue(
            isinstance(d.a_a.b_b, HyphenUnderscoreNamespace)
        )

        self.assertTrue(isinstance(d, HyphenUnderscoreNamespace))
        self.assertTrue(isinstance(d.a_a, HyphenUnderscoreNamespace))
        self.assertTrue(
            isinstance(d.a_a.b_b, HyphenUnderscoreNamespace)
        )

    #--------------------------------------------------------------------------
    def test__str__(self):
        d = DotDict()
        d.a = 1
        d.b = True
        d.c = 10/3.0
        d.d = DotDict()
        d.d.a = 'String'
        d.d.b = u'Péter'
        d.d.c = 6
        d.d.d = DotDict()
        d.d.d.a = 7
        d.e = DotDict()
        d.e.a = 8
        output = str(d)
        expected_output = '\n'.join([
            'a: 1',
            'b: True',
            'c: %r' % (10/3.0,),
            '\td.a: %r' % 'String',
            '\td.b: %r' % u'Péter',
            '\td.c: 6',
            '\t\td.d.a: 7',
            '\te.a: 8',
        ])
        self.assertEqual(output, expected_output)
