# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function

import unittest
import os
import json
import tempfile
import contextlib
from six.moves import cStringIO as StringIO

from configman.namespace import Namespace
from configman.config_manager import ConfigurationManager
from configman.datetime_util import datetime_from_ISO_string
from configman.value_sources import for_json
from configman.value_sources.for_json import ValueSource
from configman.dotdict import DotDict, DotDictWithAcquisition


#------------------------------------------------------------------------------
def stringIO_context_wrapper(a_stringIO_instance):
    @contextlib.contextmanager
    def stringIO_context_manager():
        yield a_stringIO_instance
    return stringIO_context_manager


#------------------------------------------------------------------------------
def bbb_minus_one(config, local_config, args):
    return config.bbb - 1


#==============================================================================
class TestCase(unittest.TestCase):

    #--------------------------------------------------------------------------
    def test_for_json_basics(self):
        tmp_filename = os.path.join(tempfile.gettempdir(), 'test.json')
        j = {
            'fred': 'wilma',
            'number': 23,
        }
        with open(tmp_filename, 'w') as f:
            json.dump(j, f)
        try:
            jvs = ValueSource(tmp_filename)
            vals = jvs.get_values(None, True)
            self.assertEqual(vals['fred'], 'wilma')
            self.assertEqual(vals['number'], 23)
        finally:
            if os.path.isfile(tmp_filename):
                os.remove(tmp_filename)

    #--------------------------------------------------------------------------
    def test_write_json(self):
        n = Namespace(doc='top')
        n.add_option(
            'aaa',
            '2011-05-04T15:10:00',
            'the a',
            short_form='a',
            from_string_converter=datetime_from_ISO_string
        )

        c = ConfigurationManager(
            [n],
            use_admin_controls=True,
            use_auto_help=False,
            argv_source=[]
        )

        out = StringIO()
        c.write_conf(for_json, opener=stringIO_context_wrapper(out))
        received = out.getvalue()
        out.close()
        jrec = json.loads(received)

        expect_to_find = {
            "short_form": "a",
            "default": "2011-05-04T15:10:00",
            "doc": "the a",
            "value": "2011-05-04T15:10:00",
            "from_string_converter":
            "configman.datetime_util.datetime_from_ISO_string",
            "name": "aaa"
        }
        for key, value in expect_to_find.items():
            self.assertEqual(jrec['aaa'][key], value)

    #--------------------------------------------------------------------------
    def test_json_round_trip(self):
        n = Namespace(doc='top')
        n.add_option(
            'aaa',
            '2011-05-04T15:10:00',
            'the a',
            short_form='a',
            from_string_converter=datetime_from_ISO_string
        )
        expected_date = datetime_from_ISO_string('2011-05-04T15:10:00')
        n.add_option(
            'bbb',
            '37',
            'the a',
            short_form='a',
            from_string_converter=int
        )
        n.add_option('write', 'json')
        n.add_aggregation('bbb_minus_one', bbb_minus_one)
        name = '/tmp/test.json'
        import functools
        opener = functools.partial(open, name, 'w')
        c1 = ConfigurationManager(
            [n],
            [],
            use_admin_controls=True,
            use_auto_help=False,
            app_name='/tmp/test',
            app_version='0',
            app_description='',
            argv_source=[]
        )
        c1.write_conf('json', opener)
        d1 = {'bbb': 88}
        d2 = {'bbb': '-99'}
        try:
            with open(name) as jfp:
                j = json.load(jfp)
            c2 = ConfigurationManager(
                (j,),
                (d1, d2),
                use_admin_controls=True,
                use_auto_help=False,
                argv_source=[]
            )
            config = c2.get_config()
            self.assertEqual(config.aaa, expected_date)
            self.assertEqual(config.bbb, -99)
            self.assertEqual(config.bbb_minus_one, -100)

        finally:
            os.unlink(name)

    def test_get_values(self):
        j = {
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
        tmp_filename = os.path.join(tempfile.gettempdir(), 'test.json')
        with open(tmp_filename, 'w') as f:
            json.dump(j, f)
        try:
            jvs = ValueSource(tmp_filename)
            vals = jvs.get_values(None, True, DotDict)
            self.assertTrue(isinstance(vals, DotDict))
            vals = jvs.get_values(None, True, DotDictWithAcquisition)
            self.assertTrue(isinstance(vals, DotDictWithAcquisition))
            self.assertEqual(vals.d.b, 2)
        finally:
            if os.path.isfile(tmp_filename):
                os.remove(tmp_filename)
