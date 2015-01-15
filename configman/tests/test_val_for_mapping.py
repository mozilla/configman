# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest
import os

from configman.value_sources.for_mapping import ValueSource
from configman.dotdict import DotDict, DotDictWithAcquisition

#==============================================================================
class TestCase(unittest.TestCase):

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



