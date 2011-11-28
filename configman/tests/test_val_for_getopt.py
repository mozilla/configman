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
import getopt

import configman.config_manager as config_manager
from configman.config_exceptions import NotAnOptionError
from ..value_sources.for_getopt import ValueSource


class TestCase(unittest.TestCase):

    def test_for_getopt_basics(self):
        source = ['a', 'b', 'c']
        o = ValueSource(source)
        self.assertEqual(o.argv_source, source)

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

    def test_for_getopt_with_ignore(self):
        function = ValueSource.getopt_with_ignore
        args = ['a', 'b', 'c']
        o, a = function(args, '', [])
        self.assertEqual(o, [])
        self.assertEqual(a, args)
        args = ['-a', '14', '--fred', 'sally', 'ethel', 'dwight']
        o, a = function(args, '', [])
        self.assertEqual([], o)
        self.assertEqual(a, args)
        args = ['-a', '14', '--fred', 'sally', 'ethel', 'dwight']
        o, a = function(args, 'a:', [])
        self.assertEqual(o, [('-a', '14')])
        self.assertEqual(a, ['--fred', 'sally', 'ethel', 'dwight'])
        args = ['-a', '14', '--fred', 'sally', 'ethel', 'dwight']
        o, a = function(args, 'a', ['fred='])
        self.assertEqual(o, [('-a', ''), ('--fred', 'sally')])
        self.assertEqual(a, ['14', 'ethel', 'dwight'])

    def test_overlay_config_5(self):
        """test namespace definition w/getopt"""
        n = config_manager.Namespace()
        n.add_option('a', 1, doc='the a')
        n.b = 17
        n.add_option('c', False, doc='the c')
        c = config_manager.ConfigurationManager([n], [['--a', '2', '--c']],
                                    use_admin_controls=True,
                                    use_auto_help=False,
                                    argv_source=[])
        self.assertEqual(c.option_definitions.a, n.a)
        self.assertTrue(isinstance(c.option_definitions.b,
                                   config_manager.Option))
        self.assertEqual(c.option_definitions.a.value, 2)
        self.assertEqual(c.option_definitions.b.value, 17)
        self.assertEqual(c.option_definitions.b.default, 17)
        self.assertEqual(c.option_definitions.b.name, 'b')
        self.assertEqual(c.option_definitions.c.name, 'c')
        self.assertEqual(c.option_definitions.c.value, True)

    def test_overlay_config_6(self):
        """test namespace definition w/getopt"""
        n = config_manager.Namespace()
        n.add_option('a', doc='the a', default=1)
        n.b = 17
        n.c = config_manager.Namespace()
        n.c.add_option('extra', doc='the x', default=3.14159, short_form='e')
        c = config_manager.ConfigurationManager([n],
                                                [['--a', '2', '--c.extra',
                                                  '11.0']],
                                                use_admin_controls=True,
                                                use_auto_help=False)
        self.assertEqual(c.option_definitions.a, n.a)
        self.assertEqual(type(c.option_definitions.b), config_manager.Option)
        self.assertEqual(c.option_definitions.a.value, 2)
        self.assertEqual(c.option_definitions.b.value, 17)
        self.assertEqual(c.option_definitions.b.default, 17)
        self.assertEqual(c.option_definitions.b.name, 'b')
        self.assertEqual(c.option_definitions.c.extra.name, 'extra')
        self.assertEqual(c.option_definitions.c.extra.doc, 'the x')
        self.assertEqual(c.option_definitions.c.extra.default, 3.14159)
        self.assertEqual(c.option_definitions.c.extra.value, 11.0)

    def test_overlay_config_6a(self):
        """test namespace w/getopt w/short form"""
        n = config_manager.Namespace()
        n.add_option('a', 1, doc='the a')
        n.b = 17
        n.c = config_manager.Namespace()
        n.c.add_option('extra', 3.14159, 'the x', short_form='e')
        c = config_manager.ConfigurationManager([n], [getopt],
                                    use_admin_controls=True,
                                    argv_source=['--a', '2', '-e', '11.0'],
                                    use_auto_help=False)
        self.assertEqual(c.option_definitions.a, n.a)
        self.assertEqual(type(c.option_definitions.b), config_manager.Option)
        self.assertEqual(c.option_definitions.a.value, 2)
        self.assertEqual(c.option_definitions.b.value, 17)
        self.assertEqual(c.option_definitions.b.default, 17)
        self.assertEqual(c.option_definitions.b.name, 'b')
        self.assertEqual(c.option_definitions.c.extra.name, 'extra')
        self.assertEqual(c.option_definitions.c.extra.doc, 'the x')
        self.assertEqual(c.option_definitions.c.extra.default, 3.14159)
        self.assertEqual(c.option_definitions.c.extra.value, 11.0)
