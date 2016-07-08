# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function

import unittest

from configman import (
    option, dotdict, namespace, ConfigurationManager, class_converter
)
from configman.def_sources import for_mappings


#==============================================================================
class MooseBase(object):
    required_config = {
        "nodename": "localhost",
        "url": "http://twobraids.com/",
        "auth_key": "675A8BFF2099",
    }

    #--------------------------------------------------------------------------
    def __init__(self, config):
        self.config = config

    #--------------------------------------------------------------------------
    def connect(self):
        return "MooseBase connection"  # actual connection stuff ommitted


#==============================================================================
class TestCase(unittest.TestCase):

    #--------------------------------------------------------------------------
    def test_setup_definitions_1(self):
        s = dotdict.DotDict()
        s.x = option.Option('x', 17, 'the x')
        s.n = {'name': 'n', 'doc': 'the n', 'default': 23}
        s.__forbidden__ = option.Option(
            '__forbidden__',
            'no, you cannot',
            38
        )
        s.t = namespace.Namespace()
        s.t.add_option('kk', 999, 'the kk')
        s.w = 89
        s.z = None
        s.t2 = namespace.Namespace('empty namespace')
        d = dotdict.DotDict()
        for_mappings.setup_definitions(s, d)
        self.assertEqual(len(d), 6)
        self.assertTrue(isinstance(d.x, option.Option))
        self.assertTrue(isinstance(d.n, option.Option))
        self.assertTrue(d.n.name == 'n')
        self.assertTrue(d.n.default == 23)
        self.assertTrue(d.n.doc == 'the n')
        self.assertTrue(isinstance(d.t, namespace.Namespace))
        self.assertTrue(d.t.kk.name == 'kk')
        self.assertTrue(d.t.kk.default == 999)
        self.assertTrue(d.t.kk.doc == 'the kk')
        self.assertTrue(isinstance(d.w, namespace.Option))
        self.assertTrue(d.w.name == 'w')
        self.assertTrue(d.w.default == 89)
        self.assertTrue(d.w.doc == 'w')
        self.assertTrue(isinstance(d.t2, namespace.Namespace))
        self.assertTrue(len(d.t2) == 0)

    #--------------------------------------------------------------------------
    def test_setup_definitions_2(self):
        d = {'cls': MooseBase}

        cm = ConfigurationManager(d, values_source_list=[])
        c = cm.get_config()
        self.assertTrue(
            cm.option_definitions.cls.from_string_converter is class_converter
        )
        self.assertTrue(c.cls is MooseBase)
