# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function

import unittest
import os
import tempfile
import contextlib
from six.moves import cStringIO as StringIO

from configman.datetime_util import datetime_from_ISO_string

from configman.value_sources import for_conf
from configman.namespace import Namespace
from configman.config_manager import ConfigurationManager
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

    #--------------------------------------------------------------------------
    def test_for_conf_basics(self):
        tmp_filename = os.path.join(tempfile.gettempdir(), 'test.conf')
        with open(tmp_filename, 'w') as f:
            f.write('# comment\n')
            f.write('limit=20\n')
            f.write('\n')
        try:
            o = for_conf.ValueSource(tmp_filename)
            assert o.values == {'limit': '20'}, o.values
            # in the case of this implementation of a ValueSource,
            # the two parameters to get_values are dummies.  That may
            # not be true for all ValueSource implementations
            self.assertEqual(o.get_values(1, False), {'limit': '20'})
            self.assertEqual(o.get_values(2, True), {'limit': '20'})

            v = o.get_values(None, True, DotDict)
            self.assertTrue(isinstance(v, DotDict))
            v = o.get_values(None, None, obj_hook=DotDictWithAcquisition)
            self.assertTrue(isinstance(v, DotDictWithAcquisition))
        finally:
            if os.path.isfile(tmp_filename):
                os.remove(tmp_filename)

    #--------------------------------------------------------------------------
    def donttest_for_conf_nested_namespaces(self):
        n = self._some_namespaces()
        cm = ConfigurationManager(
            n,
            values_source_list=[],
        )
        out = StringIO()
        cm.write_conf(for_conf, opener=stringIO_context_wrapper(out))
        received = out.getvalue()
        out.close()
        expected = """# name: aaa
# doc: the a
aaa=2011-05-04T15:10:00

#------------------------------------------------------------------------------
# c - c space

# name: c.dwight
# doc: your uncle
c.dwight=98

# name: c.fred
# doc: husband from Flintstones
c.fred=stupid

# name: c.wilma
# doc: wife from Flintstones
c.wilma=waspish

#------------------------------------------------------------------------------
# e - e space

# name: c.e.dwight
# doc: my uncle
c.e.dwight=97

#------------------------------------------------------------------------------
# d - d space

# name: d.ethel
# doc: female neighbor from I Love Lucy
d.ethel=silly

# name: d.fred
# doc: male neighbor from I Love Lucy
d.fred=crabby

#------------------------------------------------------------------------------
# x - x space

# name: x.password
# doc: the password
x.password=secret

# name: x.size
# doc: how big in tons
x.size=100"""
        self.assertEqual(received.strip(), expected)

        strio = StringIO(expected)
        n.c.dwight.default = 3823
        n.c.e.dwight = 'fred'
        cm2 = ConfigurationManager(
            n,
            [stringIO_context_wrapper(strio)],
            use_admin_controls=False,
            use_auto_help=False
        )
        result = cm2.get_config()
        self.assertEqual(len(result), 4)
        self.assertEqual(sorted(result.keys()), ['aaa', 'c', 'd', 'x'])
        self.assertEqual(len(result.c), 4)
        self.assertEqual(
            sorted(result.c.keys()),
            ['dwight', 'e', 'fred', 'wilma']
        )
        self.assertEqual(result.c.dwight, 98)
        self.assertEqual(len(result.c.e), 1)
        self.assertEqual(result.c.e.dwight, '97')
