# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest
import os

from cStringIO import StringIO
import contextlib
from configman import Namespace, ConfigurationManager
from configman.datetime_util import datetime_from_ISO_string

from configman.value_sources import for_mapping
from configman.value_sources.for_mapping import ValueSource
from configman.dotdict import DotDict, DotDictWithAcquisition

def stringIO_context_wrapper(a_stringIO_instance):
    @contextlib.contextmanager
    def stringIS_context_manager():
        yield a_stringIO_instance
    return stringIS_context_manager


#==============================================================================
class TestCase(unittest.TestCase):

    #--------------------------------------------------------------------------
    def _some_namespaces(self):
        """set up some namespaces"""
        n = Namespace(doc='top')
        n.add_option(
            'aaa',
            '2011-05-04T15:10:00',
            'the a',
            short_form='a',
            from_string_converter=datetime_from_ISO_string
        )
        n.c = Namespace(doc='c space')
        n.c.add_option(
            'fred',
            'stupid',
            # deliberate whitespace to test that it gets stripped
            ' husband from Flintstones '
        )
        n.c.add_option('wilma', 'waspish', 'wife from Flintstones')
        n.c.e = Namespace(doc='e space')
        n.c.e.add_option(
            'dwight',
            default=97,
            doc='my uncle'
        )
        n.c.add_option(
            'dwight',
            default=98,
            doc='your uncle'
        )
        n.d = Namespace(doc='d space')
        n.d.add_option('fred', 'crabby', 'male neighbor from I Love Lucy')
        n.d.add_option(
            'ethel',
            'silly',
            'female neighbor from I Love Lucy'
        )
        n.x = Namespace(doc='x space')
        n.x.add_option('size', 100, 'how big in tons', short_form='s')
        n.x.add_option('password', 'secret', 'the password')
        return n

    def test_environ_ignores_mismatches(self):
        vs = ValueSource(os.environ)
        self.assertTrue(vs.always_ignore_mismatches)
        self.assertTrue(vs.source is os.environ)

    def test_mapping(self):
        m = {
            'a': '1',
            'b': 2
        }
        vs = ValueSource(m)
        self.assertFalse(vs.always_ignore_mismatches)
        self.assertTrue(vs.source is m)

        m = {
            'a': '1',
            'b': 2,
            'always_ignore_mismatches': False
        }
        vs = ValueSource(m)
        self.assertFalse(vs.always_ignore_mismatches)
        self.assertTrue(vs.source is m)

        m = {
            'a': '1',
            'b': 2,
            'always_ignore_mismatches': True
        }
        vs = ValueSource(m)
        self.assertTrue(vs.always_ignore_mismatches)
        self.assertTrue(vs.source is m)

    def test_get_values(self):
        m = {
            'a': '1',
            'b': 2,
            'c': {
                'd': 'x',
                'e': 'y'
            },
            'd': {
                'd': 'X'
            }
        }
        vs = ValueSource(m)
        v = vs.get_values(None, None)
        self.assertTrue(isinstance(v, DotDict))
        v = vs.get_values(None, None, obj_hook=DotDictWithAcquisition)
        self.assertTrue(isinstance(v, DotDictWithAcquisition))
        self.assertEqual(v.d.b, 2)

    #--------------------------------------------------------------------------
    def test_for_mapping_nested_namespaces(self):
        n = self._some_namespaces()
        cm = ConfigurationManager(
            n,
            values_source_list=[],
        )
        out = StringIO()
        cm.write_conf(for_mapping, opener=stringIO_context_wrapper(out))
        received = out.getvalue()
        out.close()
        expected = """aaa='2011-05-04T15:10:00'

c__dwight='98'
c__fred='stupid'
c__wilma='waspish'

c__e__dwight='97'

d__ethel='silly'
d__fred='crabby'

x__password='secret'
x__size='100'"""
        self.assertEqual(received.strip(), expected)
