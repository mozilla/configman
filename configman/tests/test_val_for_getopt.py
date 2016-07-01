# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function

import unittest
import getopt

import configman.config_manager as config_manager
from configman.config_exceptions import NotAnOptionError
from configman.value_sources.for_getopt import ValueSource
from configman.dotdict import DotDict, DotDictWithAcquisition


#==============================================================================
class TestCase(unittest.TestCase):

    #--------------------------------------------------------------------------
    def test_for_getopt_basics(self):
        source = ['a', 'b', 'c']
        o = ValueSource(source)
        self.assertEqual(o.argv_source, source)

    #--------------------------------------------------------------------------
    def test_for_getopt_get_values(self):
        c = config_manager.ConfigurationManager(
            use_admin_controls=True,
            #use_config_files=False,
            use_auto_help=False,
            argv_source=[]
        )

        source = ['--limit', '10']
        o = ValueSource(source)
        self.assertEqual(o.get_values(c, True), {})
        self.assertRaises(NotAnOptionError,
                          o.get_values, c, False)

        c.option_definitions.add_option('limit', default=0)
        self.assertEqual(o.get_values(c, False), {'limit': '10'})
        self.assertEqual(o.get_values(c, True), {'limit': '10'})
        v = o.get_values(c, True, DotDict)
        self.assertTrue(isinstance(v, DotDict))
        v = o.get_values(c, True, DotDictWithAcquisition)
        self.assertTrue(isinstance(v, DotDictWithAcquisition))

    #--------------------------------------------------------------------------
    def test_for_getopt_get_values_with_short_form(self):
        c = config_manager.ConfigurationManager(
            use_admin_controls=True,
            #use_config_files=False,
            use_auto_help=False,
            argv_source=[]
        )

        source = ['-l', '10']
        o = ValueSource(source)
        c.option_definitions.add_option('limit', default=0, short_form='l')
        self.assertEqual(o.get_values(c, False), {'limit': '10'})
        self.assertEqual(o.get_values(c, True), {'limit': '10'})

    #--------------------------------------------------------------------------
    def test_for_getopt_get_values_with_aggregates(self):
        c = config_manager.ConfigurationManager(
            use_admin_controls=True,
            #use_config_files=False,
            use_auto_help=False,
            argv_source=[]
        )

        source = ['-l', '10']
        o = ValueSource(source)
        c.option_definitions.add_option('limit', default=0, short_form='l')
        c.option_definitions.add_aggregation('summer', lambda *x: False)
        self.assertEqual(o.get_values(c, False), {'limit': '10'})
        self.assertEqual(o.get_values(c, True), {'limit': '10'})

    #--------------------------------------------------------------------------
    def test_for_getopt_with_ignore(self):
        function = ValueSource.getopt_with_ignore
        args = ['a', 'b', 'c']
        o, a = function(args, '', [])
        self.assertEqual(o, [])
        self.assertEqual(a, args)
        args = ['-a', '14', '--fred', 'sally', 'ethel', 'dwight']
        o, a = function(args, '', [])
        self.assertEqual([], o)
        self.assertEqual(a, ['14', 'sally', 'ethel', 'dwight'])
        args = ['-a', '14', '--fred', 'sally', 'ethel', 'dwight']
        o, a = function(args, 'a:', [])
        self.assertEqual(o, [('-a', '14')])
        self.assertEqual(a, ['sally', 'ethel', 'dwight'])
        args = ['-a', '14', '--fred', 'sally', 'ethel', 'dwight']
        o, a = function(args, 'a', ['fred='])
        self.assertEqual(o, [('-a', ''), ('--fred', 'sally')])
        self.assertEqual(a, ['14', 'ethel', 'dwight'])

    #--------------------------------------------------------------------------
    def test_overlay_config_5(self):
        """test namespace definition w/getopt"""
        n = config_manager.Namespace()
        n.add_option('a', 1, doc='the a')
        n.b = 17
        n.add_option('c', False, doc='the c')
        c = config_manager.ConfigurationManager(
            [n],
            [['--a', '2', '--c']],
            use_admin_controls=True,
            use_auto_help=False,
            argv_source=[]
        )
        self.assertTrue(isinstance(c.option_definitions.b,
                                   config_manager.Option))
        self.assertEqual(c.option_definitions.a.value, 2)
        self.assertEqual(c.option_definitions.b.value, 17)
        self.assertEqual(c.option_definitions.b.default, 17)
        self.assertEqual(c.option_definitions.b.name, 'b')
        self.assertEqual(c.option_definitions.c.name, 'c')
        self.assertEqual(c.option_definitions.c.value, True)

    #--------------------------------------------------------------------------
    def test_overlay_config_6(self):
        """test namespace definition w/getopt"""
        n = config_manager.Namespace()
        n.add_option('a', doc='the a', default=1)
        n.b = 17
        n.c = config_manager.Namespace()
        n.c.add_option('extra', doc='the x', default=3.14159, short_form='e')
        c = config_manager.ConfigurationManager(
            [n],
            [['--a', '2', '--c.extra', '11.0']],
            use_admin_controls=True,
            use_auto_help=False
        )
        self.assertEqual(type(c.option_definitions.b), config_manager.Option)
        self.assertEqual(c.option_definitions.a.value, 2)
        self.assertEqual(c.option_definitions.b.value, 17)
        self.assertEqual(c.option_definitions.b.default, 17)
        self.assertEqual(c.option_definitions.b.name, 'b')
        self.assertEqual(c.option_definitions.c.extra.name, 'extra')
        self.assertEqual(c.option_definitions.c.extra.doc, 'the x')
        self.assertEqual(c.option_definitions.c.extra.default, '11.0')
        self.assertEqual(c.option_definitions.c.extra.value, 11.0)

    #--------------------------------------------------------------------------
    def test_overlay_config_6a(self):
        """test namespace w/getopt w/short form"""
        n = config_manager.Namespace()
        n.add_option('a', 1, doc='the a')
        n.b = 17
        n.c = config_manager.Namespace()
        n.c.add_option('extra', 3.14159, 'the x', short_form='e')
        c = config_manager.ConfigurationManager(
            [n],
            [getopt],
            use_admin_controls=True,
            argv_source=['--a', '2', '-e', '11.0'],
            use_auto_help=False
        )
        self.assertEqual(type(c.option_definitions.b), config_manager.Option)
        self.assertEqual(c.option_definitions.a.value, 2)
        self.assertEqual(c.option_definitions.b.value, 17)
        self.assertEqual(c.option_definitions.b.default, 17)
        self.assertEqual(c.option_definitions.b.name, 'b')
        self.assertEqual(c.option_definitions.c.extra.name, 'extra')
        self.assertEqual(c.option_definitions.c.extra.doc, 'the x')
        self.assertEqual(c.option_definitions.c.extra.default, '11.0')
        self.assertEqual(c.option_definitions.c.extra.value, 11.0)
