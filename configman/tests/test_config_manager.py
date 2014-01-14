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

import sys
import os
import os.path
import unittest
from contextlib import contextmanager
import io
from cStringIO import StringIO
import getopt

import mock
from nose.plugins.skip import SkipTest

import configman.config_manager as config_manager
from configman.option import Option
from configman.dotdict import DotDict, DotDictWithAcquisition
from configman import Namespace, RequiredConfig
from configman.converters import class_converter
import configman.datetime_util as dtu
from configman.config_exceptions import NotAnOptionError
from configman.value_sources.source_exceptions import (
    AllHandlersFailedException,
    UnknownFileExtensionException,
    NoHandlerForType
)
from configman import RequiredConfig

#==============================================================================
class T1(RequiredConfig):
    required_config = Namespace()
    required_config.add_option('a', default=11)


#==============================================================================
class T2(RequiredConfig):
    required_config = Namespace()
    required_config.add_option('b', default=22)


#==============================================================================
class T3(RequiredConfig):
    required_config = Namespace()
    required_config.add_option('c', default=33)
    required_config.namespace('ccc')
    required_config.ccc.add_option('x', default=99)


#==============================================================================
class TestCase(unittest.TestCase):

    #--------------------------------------------------------------------------
    def test_empty_ConfigurationManager_constructor(self):
        # because the default option argument defaults to using sys.argv we
        # have to mock that
        c = config_manager.ConfigurationManager(
            use_admin_controls=False,
            use_auto_help=False,
            argv_source=[]
        )
        self.assertEqual(c.option_definitions, config_manager.Namespace())

    #--------------------------------------------------------------------------
    def test_get_config_1(self):
        n = config_manager.Namespace()
        n.add_option('a', 1, 'the a')
        n.add_option('b', 17)
        c = config_manager.ConfigurationManager(
            [n],
            use_admin_controls=False,
            use_auto_help=False,
            argv_source=[]
        )
        d = c.get_config()
        e = DotDict()
        e.a = 1
        e.b = 17
        self.assertEqual(d, e)

    #--------------------------------------------------------------------------
    def test_get_config_2(self):
        n = config_manager.Namespace()
        n.add_option('a', 1, 'the a')
        n.b = 17
        n.c = c = config_manager.Namespace()
        c.x = 'fred'
        c.y = 3.14159
        c.add_option('z', 99, 'the 99')
        c = config_manager.ConfigurationManager(
            [n],
            use_admin_controls=False,
            use_auto_help=False,
            argv_source=[]
        )
        d = c.get_config()
        e = DotDict()
        e.a = 1
        e.b = 17
        e.c = DotDict()
        e.c.x = 'fred'
        e.c.y = 3.14159
        e.c.z = 99
        self.assertEqual(d, e)

    #--------------------------------------------------------------------------
    def _some_namespaces(self):
        """set up some namespaces"""
        n = config_manager.Namespace(doc='top')
        n.add_option(
            'aaa',
            '2011-05-04T15:10:00',
            'the a',
            short_form='a',
            from_string_converter=dtu.datetime_from_ISO_string
        )
        n.c = config_manager.Namespace(doc='c space')
        n.c.add_option('fred', 'stupid', 'husband from Flintstones')
        n.c.add_option('wilma', 'waspish', 'wife from Flintstones')
        n.d = config_manager.Namespace(doc='d space')
        n.d.add_option('fred', 'crabby', 'male neighbor from I Love Lucy')
        n.d.add_option('ethel', 'silly', 'female neighbor from I Love Lucy')
        n.x = config_manager.Namespace(doc='x space')
        n.x.add_option('size', 100, 'how big in tons', short_form='s')
        n.x.add_option('password', 'secret', 'the password')
        return n

    #--------------------------------------------------------------------------
    def test_overlay_config_4(self):
        """test overlay dict w/flat source dict"""
        n = config_manager.Namespace()
        n.add_option('a', doc='the a', default=1)
        n.b = 17
        n.c = config_manager.Namespace()
        n.c.add_option('extra', doc='the x', default=3.14159)
        g = {'a': 2, 'c.extra': 2.89}
        c = config_manager.ConfigurationManager(
            [n],
            [g],
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
        self.assertEqual(c.option_definitions.c.extra.name, 'extra')
        self.assertEqual(c.option_definitions.c.extra.doc, 'the x')
        self.assertEqual(c.option_definitions.c.extra.default, 2.89)
        self.assertEqual(c.option_definitions.c.extra.value, 2.89)

    #--------------------------------------------------------------------------
    def test_overlay_config_4a(self):
        """test overlay dict w/deep source dict"""
        n = config_manager.Namespace()
        n.add_option('a', 1, doc='the a')
        n.b = 17
        n.c = config_manager.Namespace()
        n.c.add_option('extra', doc='the x', default=3.14159)
        g = {'a': 2, 'c': {'extra': 2.89}}
        c = config_manager.ConfigurationManager(
            [n],
            [g],
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
        self.assertEqual(c.option_definitions.c.extra.name, 'extra')
        self.assertEqual(c.option_definitions.c.extra.doc, 'the x')
        self.assertEqual(c.option_definitions.c.extra.default, 2.89)
        self.assertEqual(c.option_definitions.c.extra.value, 2.89)

    #--------------------------------------------------------------------------
    def test_overlay_config_5(self):
        """test namespace definition w/getopt"""
        n = config_manager.Namespace()
        n.add_option('a', doc='the a', default=1)
        n.b = 17
        n.add_option('c', doc='the c', default=False)
        c = config_manager.ConfigurationManager(
            [n],
            [getopt],
            use_admin_controls=True,
            use_auto_help=False,
            argv_source=['--a', '2', '--c']
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
        n.c.add_option('extra', short_form='e', doc='the x', default=3.14159)
        c = config_manager.ConfigurationManager(
            [n],
            [getopt],
            use_admin_controls=True,
            use_auto_help=False,
            argv_source=['--a', '2', '--c.extra', '11.0']
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
        n.add_option('a', doc='the a', default=1)
        n.b = 17
        n.c = config_manager.Namespace()
        n.c.add_option('extra', 3.14159, 'the x', short_form='e')
        c = config_manager.ConfigurationManager(
            [n],
            [getopt],
            use_admin_controls=True,
            use_auto_help=False,
            argv_source=['--a', '2', '-e', '11.0']
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
    def test_overlay_config_7(self):
        """test namespace definition flat file"""
        n = config_manager.Namespace()
        n.add_option('a', doc='the a', default=1)
        n.b = 17
        n.c = config_manager.Namespace()
        n.c.add_option('extra', 3.14159, 'the x')
        n.c.add_option('string', 'fred', doc='str')

        @contextmanager
        def dummy_open():
            yield [
                '# comment line to be ignored\n',
                '\n',  # blank line to be ignored
                'a=22\n',
                'b = 33\n',
                'c.extra = 2.0\n',
                'c.string =   wilma\n'
            ]
        c = config_manager.ConfigurationManager(
            [n],
            [dummy_open],
            use_admin_controls=True,
            use_auto_help=False
        )
        self.assertEqual(type(c.option_definitions.b), config_manager.Option)
        self.assertEqual(c.option_definitions.a.value, 22)
        self.assertEqual(c.option_definitions.b.value, 33)
        self.assertEqual(c.option_definitions.b.default, '33')
        self.assertEqual(c.option_definitions.b.name, 'b')
        self.assertEqual(c.option_definitions.c.extra.name, 'extra')
        self.assertEqual(c.option_definitions.c.extra.doc, 'the x')
        self.assertEqual(c.option_definitions.c.extra.default, '2.0')
        self.assertEqual(c.option_definitions.c.extra.value, 2.0)
        self.assertEqual(c.option_definitions.c.string.name, 'string')
        self.assertEqual(c.option_definitions.c.string.doc, 'str')
        self.assertEqual(c.option_definitions.c.string.default, 'wilma')
        self.assertEqual(c.option_definitions.c.string.value, 'wilma')

    #--------------------------------------------------------------------------
    def test_overlay_config_8(self):
        """test namespace definition ini file"""
        n = config_manager.Namespace()
        n.other = config_manager.Namespace()
        n.other.add_option('t', 'tee', 'the t')
        n.d = config_manager.Namespace()
        n.d.add_option('a', 1, doc='the a')
        n.d.b = 17
        n.c = config_manager.Namespace()
        n.c.add_option('extra', 3.14159, 'the x')
        n.c.add_option('string', 'fred', doc='str')
        ini_data = """
other.t=tea
# blank line to be ignored
d.a=22
d.b=33
c.extra = 2.0
c.string = wilma
"""

        def strio():
            return io.BytesIO(ini_data)
        c = config_manager.ConfigurationManager(
            [n], [strio],
            use_admin_controls=True,
            use_auto_help=False
        )
        self.assertEqual(c.option_definitions.other.t.name, 't')
        self.assertEqual(c.option_definitions.other.t.value, 'tea')
        self.assertEqual(type(c.option_definitions.d.b), config_manager.Option)
        self.assertEqual(c.option_definitions.d.a.value, 22)
        self.assertEqual(c.option_definitions.d.b.value, 33)
        self.assertEqual(c.option_definitions.d.b.default, '33')
        self.assertEqual(c.option_definitions.d.b.name, 'b')
        self.assertEqual(c.option_definitions.c.extra.name, 'extra')
        self.assertEqual(c.option_definitions.c.extra.doc, 'the x')
        self.assertEqual(c.option_definitions.c.extra.default, '2.0')
        self.assertEqual(c.option_definitions.c.extra.value, 2.0)
        self.assertEqual(c.option_definitions.c.string.name, 'string')
        self.assertEqual(c.option_definitions.c.string.doc, 'str')
        self.assertEqual(c.option_definitions.c.string.default, 'wilma')
        self.assertEqual(c.option_definitions.c.string.value, 'wilma')

    #--------------------------------------------------------------------------
    def test_overlay_config_9(self):
        """test namespace definition ini file"""
        n = config_manager.Namespace()
        n.other = config_manager.Namespace()
        n.other.add_option('t', 'tee', 'the t')
        n.d = config_manager.Namespace()
        n.d.add_option('a', 1, doc='the a')
        n.d.b = 17
        n.c = config_manager.Namespace()
        n.c.add_option('extra', 3.14159, 'the x')
        n.c.add_option('string', 'fred', 'str')
        ini_data = """
other.t=tea
# blank line to be ignored
d.a=22
c.extra = 2.0
c.string =   from ini
"""

        def strio():
            return io.BytesIO(ini_data)
        e = DotDict()
        e.fred = DotDict()  # should be ignored
        e.fred.t = 'T'  # should be ignored
        e.d = DotDict()
        e.d.a = 16
        e.c = DotDict()
        e.c.extra = 18.6
        e.c.string = 'from environment'

        saved_environ = os.environ
        os.environ = e
        try:
            c = config_manager.ConfigurationManager(
                [n],
                [e, strio, getopt],
                use_admin_controls=True,
                use_auto_help=False,
                argv_source=[
                    '--other.t',
                    'TTT',
                    '--c.extra',
                    '11.0'
                ]
            )
        finally:
            os.environ = saved_environ
        #fm.os = saved_os
        self.assertEqual(c.option_definitions.other.t.name, 't')
        self.assertEqual(c.option_definitions.other.t.value, 'TTT')
        self.assertEqual(type(c.option_definitions.d.b), config_manager.Option)
        self.assertEqual(c.option_definitions.d.a.value, 22)
        self.assertEqual(c.option_definitions.d.b.value, 17)
        self.assertEqual(c.option_definitions.d.b.default, 17)
        self.assertEqual(c.option_definitions.d.b.name, 'b')
        self.assertEqual(c.option_definitions.c.extra.name, 'extra')
        self.assertEqual(c.option_definitions.c.extra.doc, 'the x')
        self.assertEqual(c.option_definitions.c.extra.default, '11.0')
        self.assertEqual(c.option_definitions.c.extra.value, 11.0)
        self.assertEqual(c.option_definitions.c.string.name, 'string')
        self.assertEqual(c.option_definitions.c.string.doc, 'str')
        self.assertEqual(c.option_definitions.c.string.default, 'from ini')
        self.assertEqual(c.option_definitions.c.string.value, 'from ini')

    #--------------------------------------------------------------------------
    def test_overlay_config_10(self):
        """test namespace definition ini file"""
        n = config_manager.Namespace()
        n.other = config_manager.Namespace()
        n.other.add_option('t', 'tee', 'the t')
        n.d = config_manager.Namespace()
        n.d.add_option('a', 1, 'the a')
        n.d.b = 17
        n.c = config_manager.Namespace()
        n.c.add_option('extra', 3.14159, 'the x')
        n.c.add_option('string', 'fred', doc='str')
        ini_data = """
other.t=tea
# blank line to be ignored
d.a=22
c.extra = 2.0
c.string =   from ini
"""

        def strio():
            return io.BytesIO(ini_data)
        e = DotDict()
        e.other = DotDict()
        e.other.t = 'T'
        e.d = DotDict()
        e.d.a = 16
        e.c = DotDict()
        e.c.extra = 18.6
        e.c.string = 'from environment'

        c = config_manager.ConfigurationManager(
            [n],
            [e, strio, getopt],
            use_admin_controls=True,
            argv_source=['--c.extra', '11.0'],
            use_auto_help=False
        )
        self.assertEqual(c.option_definitions.other.t.name, 't')
        self.assertEqual(c.option_definitions.other.t.value, 'tea')
        self.assertEqual(type(c.option_definitions.d.b), config_manager.Option)
        self.assertEqual(c.option_definitions.d.a.value, 22)
        self.assertEqual(c.option_definitions.d.b.value, 17)
        self.assertEqual(c.option_definitions.d.b.default, 17)
        self.assertEqual(c.option_definitions.d.b.name, 'b')
        self.assertEqual(c.option_definitions.c.extra.name, 'extra')
        self.assertEqual(c.option_definitions.c.extra.doc, 'the x')
        self.assertEqual(c.option_definitions.c.extra.default, '11.0')
        self.assertEqual(c.option_definitions.c.extra.value, 11.0)
        self.assertEqual(c.option_definitions.c.string.name, 'string')
        self.assertEqual(c.option_definitions.c.string.doc, 'str')
        self.assertEqual(c.option_definitions.c.string.default, 'from ini')
        self.assertEqual(c.option_definitions.c.string.value, 'from ini')

    #--------------------------------------------------------------------------
    def test_overlay_config_11(self):
        """test overlay dict w/deep source dict and reference value links"""
        n = config_manager.Namespace()
        n.add_option('a', 1, doc='the a', reference_value_from='xxx.yyy')
        n.b = 17
        n.c = config_manager.Namespace()
        n.c.add_option(
            'extra', doc='the x',
            default=3.14159,
            reference_value_from='xxx.yyy'
        )
        n.c.add_option(
            'a',
            doc='the a',
            reference_value_from='xxx.yyy'
        )
        g = {
            'xxx': {
                'yyy': {
                    'a': 2,
                    'extra': 2.89
                }
            }
        }
        c = config_manager.ConfigurationManager(
            [n],
            [g],
            use_admin_controls=True,
            use_auto_help=False,
            argv_source=[]
        )
        self.assertTrue(isinstance(
            c.option_definitions.b,
            config_manager.Option
        ))
        self.assertEqual(c.option_definitions.a.value, 2)
        self.assertEqual(c.option_definitions.b.value, 17)
        self.assertEqual(c.option_definitions.b.default, 17)
        self.assertEqual(c.option_definitions.b.name, 'b')
        self.assertEqual(c.option_definitions.c.extra.name, 'extra')
        self.assertEqual(c.option_definitions.c.extra.doc, 'the x')
        self.assertEqual(c.option_definitions.c.extra.default, 2.89)
        self.assertEqual(c.option_definitions.c.extra.value, 2.89)
        self.assertEqual(c.option_definitions.c.a.value, 2)

    #--------------------------------------------------------------------------
    def test_mapping_types_1(self):
        n = config_manager.Namespace()
        n.add_option(
            name='a',
            default=1,
            doc='the a'
        )
        n.b = 17
        n.c = config_manager.Namespace()
        n.c.x = 'fred'
        n.c.y = 3.14159
        n.c.add_option(
            name='z',
            default=99,
            doc='the 99'
        )
        o = {"a": 2, "c.z": 22, "c.x": 'noob', "c.y": "2.89"}
        c = config_manager.ConfigurationManager(
            [n],
            [o],
            use_admin_controls=False,
            use_auto_help=False,
            argv_source=[]
        )
        e = DotDict()
        e.a = 2
        e.b = 17
        e.c = DotDict()
        e.c.x = 'noob'
        e.c.y = 2.89
        e.c.z = 22
        d = c._generate_config(dict)
        self.assertTrue(isinstance(d, dict))
        self.assertTrue(isinstance(d['c'], dict))
        self.assertEqual(d, e)
        d = c._generate_config(DotDict)
        self.assertTrue(isinstance(d, DotDict))
        self.assertTrue(isinstance(d.c, DotDict))
        self.assertEqual(d, e)
        d = c._generate_config(DotDictWithAcquisition)
        self.assertTrue(isinstance(d, DotDictWithAcquisition))
        self.assertTrue(isinstance(d.c, DotDictWithAcquisition))
        self.assertEqual(d, e)
        self.assertEqual(d.a, 2)
        self.assertEqual(d.c.a, 2)
        self.assertEqual(d.c.b, 17)

    #--------------------------------------------------------------------------
    def test_get_option_names(self):
        n = config_manager.Namespace()
        n.add_option('a', 1, 'the a')
        n.b = 17
        n.c = config_manager.Namespace()
        n.c.add_option('fred')
        n.c.add_option('wilma')
        n.d = config_manager.Namespace()
        n.d.add_option('fred')
        n.d.add_option('wilma')
        n.d.x = config_manager.Namespace()
        n.d.x.add_option('size')
        c = config_manager.ConfigurationManager(
            [n],
            use_admin_controls=False,
            use_auto_help=False,
            argv_source=[]
        )
        names = c.get_option_names()
        names.sort()
        e = ['a', 'b', 'c.fred', 'c.wilma', 'd.fred', 'd.wilma', 'd.x.size']
        e.sort()
        self.assertEqual(names, e)
        names = sorted([x for x in c.option_definitions.keys_breadth_first()])
        self.assertEqual(names, e)

    #--------------------------------------------------------------------------
    def test_get_option(self):
        n = config_manager.Namespace()
        n.add_option('a', 1, 'the a')
        n.b = 17
        n.c = config_manager.Namespace()
        n.c.add_option('fred')
        n.c.add_option('wilma')
        n.d = config_manager.Namespace()
        n.d.add_option('fred')
        n.d.add_option('wilma')
        n.d.x = config_manager.Namespace()
        n.d.x.add_option('size')
        c = config_manager.ConfigurationManager(
            [n],
            use_admin_controls=True,
            use_auto_help=False,
            argv_source=[]
        )
        self.assertEqual(c._get_option('a'), n.a)
        self.assertEqual(c._get_option('b').name, 'b')
        self.assertEqual(c._get_option('c.fred'), n.c.fred)
        self.assertEqual(c._get_option('c.wilma'), n.c.wilma)
        self.assertEqual(c._get_option('d.fred'), n.d.fred)
        self.assertEqual(c._get_option('d.wilma'), n.d.wilma)
        self.assertEqual(c._get_option('d.wilma'), n.d.wilma)
        self.assertEqual(c._get_option('d.x.size'), n.d.x.size)

    #--------------------------------------------------------------------------
    def test_output_summary(self):
        """test_output_summary: the output from help"""
        n = config_manager.Namespace()
        n.add_option('aaa', False, 'the a', short_form='a')
        n.add_option('bee', True)
        n.b = 17
        n.c = config_manager.Namespace()
        n.c.add_option('fred', doc='husband from Flintstones')
        n.d = config_manager.Namespace()
        n.d.add_option('fred', doc='male neighbor from I Love Lucy')
        n.d.x = config_manager.Namespace()
        n.d.x.add_option('size', 100, 'how big in tons', short_form='s')
        n.d.x.add_option('password', 'secrets', 'the password')
        c = config_manager.ConfigurationManager(
            [n],
            use_admin_controls=True,
            use_auto_help=False,
            argv_source=[],
        )
        s = StringIO()
        c.output_summary(output_stream=s)
        r = s.getvalue()
        self.assertTrue('OPTIONS:\n' in r)

        options = r.split('OPTIONS:\n')[1]
        s.close()

        padding = '\n' + ' ' * 4
        expect = [
            ('-a, --aaa', 'the a%s(default: False)' % padding),
            ('--b', '(default: 17)'),
            ('--bee', '(default: True)'),
            ('--c.fred', 'husband from Flintstones'),
            ('--d.fred', 'male neighbor from I Love Lucy'),
            ('--d.x.password', 'the password%s(default: *********)' % padding),
            ('-s, --d.x.size', 'how big in tons%s(default: 100)' % padding),
        ]
        point = -1  # used to assert the sort order
        for i, (start, end) in enumerate(expect):
            self.assertTrue(
                point < options.find(start) < options.find(end),
                expect[i]
            )
            point = options.find(end)

    #--------------------------------------------------------------------------
    def test_output_summary_header(self):
        """a config with an app_name, app_version and app_description is
        printed on the output summary.
        """
        n = config_manager.Namespace()
        n.add_option('aaa', False, 'the a', short_form='a')
        c = config_manager.ConfigurationManager(
            n,
            use_admin_controls=True,
            use_auto_help=False,
            argv_source=[],
        )

        def get_output(conf):
            s = StringIO()
            conf.output_summary(output_stream=s)
            return s.getvalue()

        output = get_output(c)
        assert 'OPTIONS:' in output
        self.assertTrue('Application:' not in output)

        c.app_name = 'foobar'
        output = get_output(c)
        assert 'OPTIONS:' in output
        self.assertTrue('Application: foobar' in output)

        c.app_version = '1.0'
        output = get_output(c)
        assert 'OPTIONS:' in output
        self.assertTrue('Application: foobar 1.0' in output)

        c.app_description = "This ain't your mama's app"
        output = get_output(c)
        assert 'OPTIONS:' in output
        self.assertTrue('Application: foobar 1.0\n' in output)
        self.assertTrue("This ain't your mama's app\n\n" in output)

    #--------------------------------------------------------------------------
    def test_eval_as_converter(self):
        """does eval work as a to string converter on an Option object?"""
        n = config_manager.Namespace()
        n.add_option('aaa', doc='the a', default='', short_form='a')
        self.assertEqual(n.aaa.value, '')

    #--------------------------------------------------------------------------
    def test_RequiredConfig_get_required_config(self):

        class Foo:
            required_config = {'foo': True}

        class Bar:
            required_config = {'bar': False}

        class Poo:
            pass

        class Combined(config_manager.RequiredConfig, Foo, Poo, Bar):
            pass

        result = Combined.get_required_config()
        self.assertEqual(result.foo.value, True)
        self.assertEqual(result.bar.value, False)

        c = Combined()
        c.config_assert({'foo': True, 'bar': False})

        self.assertRaises(AssertionError, c.config_assert, ({},))

    #--------------------------------------------------------------------------
    def test_app_name_from_app_obj(self):
        class MyApp(config_manager.RequiredConfig):
            app_name = 'fred'
            app_version = '1.0'
            app_description = "my app"

            def __init__(inner_self, config):
                inner_self.config = config

        n = config_manager.Namespace()
        n.admin = config_manager.Namespace()
        n.add_option(
            'application',
            MyApp,
            'the app object class'
        )
        c = config_manager.ConfigurationManager(
            [n],
            use_admin_controls=True,
            use_auto_help=False,
            argv_source=[]
        )
        self.assertEqual(c.app_name, MyApp.app_name)
        self.assertEqual(c.app_version, MyApp.app_version)
        self.assertEqual(c.app_description, MyApp.app_description)

    #--------------------------------------------------------------------------
    def test_help_out(self):
        class MyApp(config_manager.RequiredConfig):
            app_name = 'fred'
            app_version = '1.0'
            app_description = "my app"
            required_config = config_manager.Namespace()
            required_config.add_option(
                'password',
                'fred',
                'the password',
                short_form='p'
            )
            required_config.add_option(
                'password_wo_default',
                doc='This one has no default'
            )
            required_config.add_option(
                'password_wo_docstr',
                default='Something'
            )

            def __init__(inner_self, config):
                inner_self.config = config

        n = config_manager.Namespace()
        n.admin = config_manager.Namespace()
        n.add_option(
            'application',
            MyApp,
            'the app object class',
            short_form='a'
        )

        class MyConfigManager(config_manager.ConfigurationManager):
            def output_summary(inner_self):
                output_stream = StringIO()
                r = super(MyConfigManager, inner_self).output_summary(
                    output_stream=output_stream,
                    block_password=False
                )
                r = output_stream.getvalue()
                output_stream.close()
                self.assertTrue('Application: fred 1.0' in r)
                self.assertTrue('my app\n\n' in r)
                self.assertTrue('OPTIONS:\n' in r)
                self.assertTrue('  --help' in r and 'print this' in r)
                self.assertTrue('print this (default: True)' not in r)
                self.assertTrue('  --password' in r)
                self.assertTrue('(default: *********)' in r)
                self.assertTrue('  --application' not in r)

        def my_exit():
            pass

        old_sys_exit = sys.exit
        sys.exit = my_exit
        try:
            MyConfigManager(
                n,
                [getopt],
                use_admin_controls=True,
                use_auto_help=True,
                argv_source=['--password=wilma', '--help']
            )
        finally:
            sys.exit = old_sys_exit

    #--------------------------------------------------------------------------
    def test_write_gets_called(self):
        class MyApp(config_manager.RequiredConfig):
            app_name = 'fred'
            app_version = '1.0'
            app_description = "my app"
            required_config = config_manager.Namespace()
            required_config.add_option('password', 'fred', 'the password')

            def __init__(inner_self, config):
                inner_self.config = config

        n = config_manager.Namespace()
        n.admin = config_manager.Namespace()
        n.add_option(
            'application',
            MyApp,
            'the app object class'
        )

        class MyConfigManager(config_manager.ConfigurationManager):
            def __init__(inner_self, *args, **kwargs):
                inner_self.write_called = False
                super(MyConfigManager, inner_self).__init__(*args, **kwargs)

            def dump_conf(inner_self):
                inner_self.dump_conf_called = True

        def my_exit():
            pass
        old_sys_exit = sys.exit
        sys.exit = my_exit
        try:
            c = MyConfigManager(
                n,
                [getopt],
                use_admin_controls=True,
                use_auto_help=True,
                argv_source=[
                    '--password=wilma',
                    '--admin.dump_conf=x.ini'
                ]
            )
            self.assertEqual(c.dump_conf_called, True)
        finally:
            sys.exit = old_sys_exit

    #--------------------------------------------------------------------------
    def test_get_options(self):
        class MyApp(config_manager.RequiredConfig):
            app_name = 'fred'
            app_version = '1.0'
            app_description = "my app"
            required_config = config_manager.Namespace()
            required_config.add_option('password', 'fred', 'the password')
            required_config.sub = config_manager.Namespace()
            required_config.sub.add_option(
                'name',
                'ethel',
                'the name'
            )

            def __init__(inner_self, config):
                inner_self.config = config

        n = config_manager.Namespace()
        n.admin = config_manager.Namespace()
        n.add_option(
            'application',
            MyApp,
            'the app object class'
        )

        c = config_manager.ConfigurationManager(
            n,
            use_admin_controls=True,
            use_auto_help=False,
            argv_source=[]
        )
        r = sorted(c._get_options())
        e = sorted([
            ('admin.print_conf', 'print_conf', None),
            ('admin.dump_conf', 'dump_conf', ''),
            ('admin.conf', 'conf', None),
            ('admin.strict', 'strict', False),
            ('application', 'application', MyApp),
            ('password', 'password', 'fred'),
            ('sub.name', 'name', 'ethel')
        ])
        for expected, result in zip(e, r):
            expected_key, expected_name, expected_default = expected
            result_key, result_option = result
            self.assertEqual(expected_key, result_key)
            self.assertEqual(expected_name, result_option.name)
            self.assertEqual(expected_default, result_option.default)

    #--------------------------------------------------------------------------
    def test_log_config(self):
        class MyApp(config_manager.RequiredConfig):
            app_name = 'fred'
            app_version = '1.0'
            app_description = "my app"
            required_config = config_manager.Namespace()
            required_config.add_option('password', 'fred', 'the password')
            required_config.sub = config_manager.Namespace()
            required_config.sub.add_option(
                'name',
                'ethel',
                'the name'
            )

            def __init__(inner_self, config):
                inner_self.config = config

        n = config_manager.Namespace()
        n.add_option(
            'application',
            MyApp,
            'the app object class'
        )

        c = config_manager.ConfigurationManager(
            n,
            [getopt],
            use_admin_controls=True,
            use_auto_help=False,
            argv_source=['--sub.name=wilma']
        )

        class FakeLogger(object):
            def __init__(self):
                self.log = []

            def info(self, *args):
                self.log.append(args[0] % args[1:])

        fl = FakeLogger()
        c.log_config(fl)
        e = [
            "app_name: fred",
            "app_version: 1.0",
            "current configuration:",
            "application: <class 'configman.tests.test_config_manager.MyApp'>",
            "password: *********",
            "sub.name: wilma"
        ]
        for expected, received in zip(e, fl.log):
            self.assertEqual(expected, received)

    #--------------------------------------------------------------------------
    def test_extra_commandline_parameters(self):
        class MyApp(config_manager.RequiredConfig):
            app_name = 'fred'
            app_version = '1.0'
            app_description = "my app"
            required_config = config_manager.Namespace()
            required_config.add_option('password', 'fred', 'the password')
            required_config.sub = config_manager.Namespace()
            required_config.sub.add_option(
                'name',
                'ethel',
                'the name'
            )

            def __init__(inner_self, config):
                inner_self.config = config

        n = config_manager.Namespace()
        n.admin = config_manager.Namespace()
        n.add_option(
            'application',
            MyApp,
            'the app object class'
        )

        c = config_manager.ConfigurationManager(
            n,
            [getopt],
            use_admin_controls=True,
            use_auto_help=False,
            argv_source=[
                '--sub.name=wilma',
                'argument 1',
                'argument 2',
                'argument 3'
            ]
        )
        expected = ['argument 1',
                    'argument 2',
                    'argument 3']
        self.assertEqual(c.args, expected)

    #--------------------------------------------------------------------------
    def test_print_conf_called(self):
        class MyApp(config_manager.RequiredConfig):
            app_name = 'fred'
            app_version = '1.0'
            app_description = "my app"
            required_config = config_manager.Namespace()
            required_config.add_option('password', 'fred', 'the password')
            required_config.sub = config_manager.Namespace()
            required_config.sub.add_option(
                'name',
                'ethel',
                'the name'
            )

            def __init__(inner_self, config):
                inner_self.config = config

        n = config_manager.Namespace()
        n.admin = config_manager.Namespace()
        n.add_option(
            'application',
            MyApp,
            'the app object class'
        )

        class MyConfigManager(config_manager.ConfigurationManager):
            def __init__(inner_self, *args, **kwargs):
                inner_self.write_called = False
                super(MyConfigManager, inner_self).__init__(*args, **kwargs)

            def print_conf(inner_self):
                inner_self.print_conf_called = True

        c = MyConfigManager(n,
                            [getopt],
                            use_admin_controls=True,
                            use_auto_help=False,
                            quit_after_admin=False,
                            argv_source=['--admin.print_conf=ini',
                                         'argument 1',
                                         'argument 2',
                                         'argument 3'])
        self.assertEqual(c.print_conf_called, True)

    #--------------------------------------------------------------------------
    def test_non_compliant_app_object(self):
        # the MyApp class doesn't define required config
        class MyApp():
            app_name = 'fred'
            app_version = '1.0'
            app_description = "my app"

            def __init__(inner_self, config):
                inner_self.config = config

        n = config_manager.Namespace()
        n.admin = config_manager.Namespace()
        n.add_option(
            'application',
            MyApp,
            'the app object class'
        )

        c = config_manager.ConfigurationManager(
            n,
            [getopt],
            use_admin_controls=True,
            use_auto_help=False,
            argv_source=[
                'argument 1',
                'argument 2',
                'argument 3'
            ]
        )
        conf = c.get_config()
        self.assertEqual(conf.keys(), ['admin', 'application'])

    #--------------------------------------------------------------------------
    def test_print_conf(self):
        n = config_manager.Namespace()

        class MyConfigManager(config_manager.ConfigurationManager):
            def __init__(inner_self, *args, **kwargs):
                inner_self.write_called = False
                super(MyConfigManager, inner_self).__init__(*args, **kwargs)

            def print_conf(self):
                temp_stdout = sys.stdout
                sys.stdout = 17
                try:
                    super(MyConfigManager, self).print_conf()
                finally:
                    sys.stdout = temp_stdout

            def write_conf(inner_self, file_type, opener, skip_keys=None):
                self.assertEqual(file_type, 'ini')
                with opener() as f:
                    self.assertEqual(f, 17)

        MyConfigManager(
            n,
            [getopt],
            use_admin_controls=True,
            use_auto_help=False,
            quit_after_admin=False,
            argv_source=['--admin.print_conf=ini',
                         'argument 1',
                         'argument 2',
                         'argument 3'],
            config_pathname='fred')

    #--------------------------------------------------------------------------
    def test_dump_conf(self):
        n = config_manager.Namespace()

        class MyConfigManager(config_manager.ConfigurationManager):
            def __init__(inner_self, *args, **kwargs):
                inner_self.write_called = False
                super(MyConfigManager, inner_self).__init__(*args, **kwargs)

            def write_conf(inner_self, file_type, opener, skip_keys=None):
                self.assertEqual(file_type, 'ini')
                self.assertEqual(opener.args, ('fred.ini', 'w'))

        MyConfigManager(
            n,
            [getopt],
            use_admin_controls=True,
            use_auto_help=False,
            quit_after_admin=False,
            argv_source=['--admin.dump_conf=fred.ini',
                         'argument 1',
                         'argument 2',
                         'argument 3'],
            config_pathname='fred'
        )

    #--------------------------------------------------------------------------
    def test_dump_conf_bad_extension(self):
        n = config_manager.Namespace()

        self.assertRaises(
            UnknownFileExtensionException,
            config_manager.ConfigurationManager,
            n,
            [getopt],
            use_admin_controls=True,
            use_auto_help=False,
            quit_after_admin=False,
            argv_source=[
                '--admin.dump_conf=/tmp/fred.xxx',
                'argument 1',
                'argument 2',
                'argument 3'
            ],
            config_pathname='fred'
        )
        self.assertFalse(os.path.exists('/tmp/fred.xxx'))

    #--------------------------------------------------------------------------
    def test_print_conf_some_options_excluded(self):
        n = config_manager.Namespace()
        n.add_option('gender',
                     default='Male',
                     doc='What kind of genitalia?')
        n.add_option('salary',
                     default=10000,
                     doc='How much do you earn?',
                     exclude_from_print_conf=True
                     )

        old_stdout = sys.stdout
        temp_output = StringIO()
        sys.stdout = temp_output
        try:
            config_manager.ConfigurationManager(
                n,
                [getopt],
                use_admin_controls=True,
                use_auto_help=False,
                quit_after_admin=False,
                argv_source=['--admin.print_conf=ini'],
                config_pathname='fred'
            )
        finally:
            sys.stdout = old_stdout

        printed = temp_output.getvalue()
        self.assertTrue('gender' in printed)
        self.assertTrue('salary' not in printed)

    #--------------------------------------------------------------------------
    def test_dump_conf_some_options_excluded(self):
        n = config_manager.Namespace()
        n.add_option('gender',
                     default='Male',
                     doc='What kind of genitalia?',
                     exclude_from_print_conf=True)
        n.add_option('salary',
                     default=10000,
                     doc='How much do you earn?',
                     exclude_from_dump_conf=True
                     )

        try:
            config_manager.ConfigurationManager(
                n,
                [getopt],
                use_admin_controls=True,
                use_auto_help=False,
                quit_after_admin=False,
                argv_source=['--admin.dump_conf=foo.conf'],
                config_pathname='fred'
            )

            printed = open('foo.conf').read()
            self.assertTrue('gender' in printed)
            self.assertTrue('salary' not in printed)

        finally:
            if os.path.isfile('foo.conf'):
                os.remove('foo.conf')

    #--------------------------------------------------------------------------
    def test_config_pathname_set(self):

        class MyConfigManager(config_manager.ConfigurationManager):
            def __init__(inner_self, *args, **kwargs):
                inner_self.write_called = False
                super(MyConfigManager, inner_self).__init__(*args, **kwargs)

            def get_config_pathname(self):
                temp_fn = os.path.isdir
                os.path.isdir = lambda x: False
                try:
                    r = super(MyConfigManager, self)._get_config_pathname()
                finally:
                    os.path.isdir = temp_fn
                return r

        self.assertRaises(NoHandlerForType,
                          MyConfigManager,
                          use_admin_controls=True,
                          use_auto_help=False,
                          quit_after_admin=False,
                          argv_source=['argument 1',
                                       'argument 2',
                                       'argument 3'],
                          config_pathname='fred')

    #--------------------------------------------------------------------------
    def test_ConfigurationManager_block_password(self):
        function = config_manager.ConfigurationManager._block_password
        self.assertEqual(function('foo', 'bar', 'peter', block_password=False),
                         ('foo', 'bar', 'peter'))
        self.assertEqual(function('foo', 'bar', 'peter', block_password=True),
                         ('foo', 'bar', 'peter'))
        self.assertEqual(function('foo', 'password', 'peter',
                                  block_password=True),
                         ('foo', 'password', '*********'))
        self.assertEqual(function('foo', 'my_password', 'peter',
                                  block_password=True),
                         ('foo', 'my_password', '*********'))

    #--------------------------------------------------------------------------
    def test_do_aggregations(self):
        def aggregation_test(all_config, local_namespace, args):
            self.assertTrue('password' in all_config)
            self.assertTrue('sub1' in all_config)
            self.assertTrue('name' in all_config.sub1)
            self.assertTrue('name' in local_namespace)
            self.assertTrue('spouse' in local_namespace)
            self.assertEqual(len(args), 2)
            return (
                '%s married %s using password %s but divorced because of %s.'
                % (
                    local_namespace.name,
                    local_namespace.spouse,
                    all_config.password,
                    args[1]
                )
            )

        class MyApp(config_manager.RequiredConfig):
            app_name = 'fred'
            app_version = '1.0'
            app_description = "my app"
            required_config = config_manager.Namespace()
            required_config.add_option('password', '@$*$&26Ht', 'the password')
            required_config.namespace('sub1')
            required_config.sub1.add_option('name', 'ethel', 'the name')
            required_config.sub1.add_option('spouse', 'fred', 'the spouse')
            required_config.sub1.add_aggregation('statement', aggregation_test)

            def __init__(inner_self, config):
                inner_self.config = config

        n = config_manager.Namespace()
        n.admin = config_manager.Namespace()
        n.add_option(
            'application',
            MyApp,
            'the app object class'
        )

        c = config_manager.ConfigurationManager(
            n,
            [getopt],
            use_admin_controls=True,
            use_auto_help=False,
            argv_source=[
                '--sub1.name=wilma',
                'arg1',
                'arg2'
            ]
        )
        config = c.get_config()
        self.assertEqual(config.sub1.statement,
                         'wilma married fred using password @$*$&26Ht '
                         'but divorced because of arg2.')

    #--------------------------------------------------------------------------
    def test_context(self):

        class AggregatedValue(object):

            def __init__(self, value):
                self.value = value

            def close(self):
                self.value = None

        def aggregation_test(all_config, local_namespace, args):
            self.assertTrue('password' in all_config)
            self.assertTrue('sub1' in all_config)
            self.assertTrue('name' in all_config.sub1)
            self.assertTrue('name' in local_namespace)
            self.assertTrue('spouse' in local_namespace)
            self.assertEqual(len(args), 2)
            return AggregatedValue('%s married %s using password %s but '
                                   'divorced because of %s.' %
                                   (local_namespace.name,
                                    local_namespace.spouse,
                                    all_config.password,
                                    args[1]))

        class MyApp(config_manager.RequiredConfig):
            app_name = 'fred'
            app_version = '1.0'
            app_description = "my app"
            required_config = config_manager.Namespace()
            required_config.add_option('password', '@$*$&26Ht', 'the password')
            required_config.namespace('sub1')
            required_config.sub1.add_option('name', 'ethel', 'the name')
            required_config.sub1.add_option('spouse', 'fred', 'the spouse')
            required_config.sub1.add_aggregation('statement', aggregation_test)

            def __init__(inner_self, config):
                inner_self.config = config

        n = config_manager.Namespace()
        n.add_option('application',
                     MyApp,
                     'the app object class')

        c = config_manager.ConfigurationManager(
            n,
            [getopt],
            use_admin_controls=False,
            use_auto_help=False,
            argv_source=[
                '--sub1.name=wilma',
                'arg1',
                'arg2'
            ]
        )

        with c.context() as config:
            statement = config.sub1.statement
            self.assertEqual(statement.value,
                             'wilma married fred using password @$*$&26Ht '
                             'but divorced because of arg2.')
        self.assertTrue(statement.value is None)

    #--------------------------------------------------------------------------
    def test_failing_aggregate_error_bubbling(self):
        """Reproduces and assures this issue
        https://github.com/mozilla/configman/issues/21
        """
        class AggregatedValue(object):

            def __init__(self, value):
                self.value = value

            def close(self):
                self.value = None

        class SomeException(Exception):
            pass

        def aggregation_test(all_config, local_namespace, args):
            # the aggregator might be broken
            raise SomeException('anything')

        class MyApp(config_manager.RequiredConfig):
            app_name = 'fred'
            app_version = '1.0'
            app_description = "my app"
            required_config = config_manager.Namespace()
            required_config.add_aggregation('statement', aggregation_test)

        n = config_manager.Namespace()
        n.admin = config_manager.Namespace()
        n.add_option(
            'application',
            MyApp,
            'the app object class'
        )

        c = config_manager.ConfigurationManager(
            n,
            [getopt],
            use_admin_controls=True,
            use_auto_help=False,
            argv_source=[]
        )

        contextmanager_ = c.context()
        self.assertRaises(SomeException, contextmanager_.__enter__)

    #--------------------------------------------------------------------------
    def test_namespaces_with_conflicting_class_converters(self):
        rc = Namespace()
        rc.namespace('source')
        rc.source.add_option(
            'cls',
            default='configman.tests.test_config_manager.T1',
            from_string_converter=class_converter
        )
        rc.namespace('destination')
        rc.destination.add_option(
            'cls',
            default='configman.tests.test_config_manager.T2',
            from_string_converter=class_converter
        )
        c = config_manager.ConfigurationManager(
            rc,
            [
                {
                    'source': {
                        'cls': 'configman.tests.test_config_manager.T2'
                    },
                    'destination': {
                        'cls': 'configman.tests.test_config_manager.T3'
                    }
                },
                {
                    'source': {
                        'cls': 'configman.tests.test_config_manager.T1'
                    },
                    'destination': {
                        'cls': 'configman.tests.test_config_manager.T2'
                    }
                },
                {
                    'source': {
                        'cls': 'configman.tests.test_config_manager.T3'
                    },
                    'destination': {
                        'cls': 'configman.tests.test_config_manager.T1'
                    }
                },
            ],
            use_admin_controls=True,
            use_auto_help=False,
            argv_source=[]
        )
        conf = c.get_config()
        self.assertEqual(len(conf), 3)
        self.assertEqual(conf.keys(), ['source', 'destination', 'admin'])
        self.assertEqual(len(conf.source), 3)
        self.assertEqual(conf.source.c, 33)
        self.assertEqual(conf.source.cls, T3)
        self.assertEqual(len(conf.source.ccc), 1)
        self.assertEqual(conf.source.ccc.x, 99)
        self.assertEqual(len(conf.destination), 2)
        self.assertEqual(conf.destination.a, 11)
        self.assertEqual(conf.destination.cls, T1)

    #--------------------------------------------------------------------------
    def _common_app_namespace_setup(self):
        class MyApp(config_manager.RequiredConfig):
            app_name = 'fred'
            app_version = '1.0'
            app_description = "my app"
            required_config = config_manager.Namespace()
            required_config.namespace('toplevel')
            required_config.toplevel.add_option('password', 'fred',
                                                'the password')

        n = config_manager.Namespace()
        n.admin = config_manager.Namespace()
        n.add_option(
            'application',
            MyApp,
            'the app object class'
        )
        return n

    #--------------------------------------------------------------------------
    def test_admin_conf_missing_file_ioerror(self):
        """if you specify an `--admin.conf=...` file that doesn't exist it
        should not let you get away with it.
        """
        n = self._common_app_namespace_setup()

        self.assertRaises(
            IOError,
            config_manager.ConfigurationManager,
            (n,),
            argv_source=['--admin.conf=x.ini']
        )

        # but check we can still do it if the file exists
        open('x.ini', 'w').write(
            '[toplevel]\n'
            'password=something\n'
        )
        try:
            c = config_manager.ConfigurationManager(
                (n,),
                argv_source=['--admin.conf=x.ini']
            )
            with c.context() as config:
                self.assertEqual(config.toplevel.password, 'something')
        finally:
            os.remove('x.ini')

    #--------------------------------------------------------------------------
    def test_bad_options(self):
        """tests _check_for_mismatches"""
        rc = Namespace()
        rc.namespace('source')
        rc.source.add_option(
            'cls',
            default='configman.tests.test_config_manager.T1',
            from_string_converter=class_converter
        )
        rc.namespace('destination')
        rc.destination.add_option(
            'cls',
            default='configman.tests.test_config_manager.T2',
            from_string_converter=class_converter
        )
        self.assertRaises(  # 'classy' is not an option
            NotAnOptionError,
            config_manager.ConfigurationManager,
            rc,
            [
                {
                    'admin': {
                        'strict': True
                    }
                },
                {
                    'source': {
                        'cls': 'configman.tests.test_config_manager.T2'
                    },
                    'destination': {
                        'cls': 'configman.tests.test_config_manager.T3'
                    }
                },
                {
                    'source': {
                        'cls': 'configman.tests.test_config_manager.T1'
                    },
                    'destination': {
                        'cls': 'configman.tests.test_config_manager.T2'
                    }
                },
                {
                    'source': {
                        'classy': 'configman.tests.test_config_manager.T3'
                    },
                    'destination': {
                        'cls': 'configman.tests.test_config_manager.T1'
                    }
                },
            ],
        )
        self.assertRaises(  # 'sourness' not a namespace
            NotAnOptionError,
            config_manager.ConfigurationManager,
            rc,
            [
                {
                    'admin': {
                        'strict': True
                    }
                },
                {
                    'source': {
                        'cls': 'configman.tests.test_config_manager.T2'
                    },
                    'destination': {
                        'cls': 'configman.tests.test_config_manager.T3'
                    }
                },
                {
                    'sourness': {
                        'cls': 'configman.tests.test_config_manager.T1'
                    },
                    'destination': {
                        'cls': 'configman.tests.test_config_manager.T2'
                    }
                },
                {
                    'source': {
                        'cls': 'configman.tests.test_config_manager.T3'
                    },
                    'destination': {
                        'cls': 'configman.tests.test_config_manager.T1'
                    }
                },
            ],
        )

        # make sure commandline data sources always behave stictly even when
        # strict is set to False
        import getopt
        self.assertRaises(  # 'alpha' is not an option
            NotAnOptionError,
            config_manager.ConfigurationManager,
            rc,
            [
                {'admin': {'strict': False}},  # not strict, we allow anything
                {
                    'source': {
                        'cls': 'configman.tests.test_config_manager.T2'
                    },
                    'destination': {
                        'cls': 'configman.tests.test_config_manager.T3'
                    }
                },
                {
                    'source': {
                        'cls': 'configman.tests.test_config_manager.T1'
                    },
                    'destination': {
                        'cls': 'configman.tests.test_config_manager.T2'
                    }
                },
                # commandline sources need to ignore when strict=False and
                # raise NotAnOptionError anyway - we don't want to allow
                # arbitrary  switches on the command line.
                getopt,
            ],
            argv_source=['--alpha']
        )

    #--------------------------------------------------------------------------
    def test_acquisition(self):
        """define a common key in two sub-namespaces.  Then offer only a value
        from the base namespace.  Both sub-namespace Options should have the
        end value from the base value namespace."""
        rc = Namespace()
        rc.namespace('source')
        rc.source.add_option('cls',
                             default='configman.tests.test_config_manager.T1',
                             from_string_converter=class_converter)
        rc.namespace('destination')
        rc.destination.add_option(
            'cls',
            default='configman.tests.test_config_manager.T2',
            from_string_converter=class_converter
        )
        cm = config_manager.ConfigurationManager(
            rc,
            [
                {'cls': 'configman.tests.test_config_manager.T2'},
            ],
        )
        c = cm.get_config()
        self.assertEqual(c.source.cls, T2)
        self.assertEqual(c.destination.cls, T2)

    #--------------------------------------------------------------------------
    def test_admin_conf_all_handlers_fail(self):
        """no handler found produces empty message"""
        n = self._common_app_namespace_setup()

        # make a config file that nothing will understand
        open('x.fred', 'w').write(
            '[toplevel]\n'
            'password=something\n'
        )
        try:
            self.assertRaises(
                NoHandlerForType,
                config_manager.ConfigurationManager,
                (n,),
                argv_source=['--admin.conf=x.fred']
            )
        finally:
            os.remove('x.fred')

    #--------------------------------------------------------------------------
    def test_admin_conf_fail_message_gets_through(self):
        """make sure AllHandlersFailedException message gets through"""
        n = self._common_app_namespace_setup()

        # make a config file that fails to load in its proper handler
        open('x.ini', 'w').write(
            'this makes no sense as an ini file'
        )
        try:
            config_manager.ConfigurationManager(
                (n,),
                argv_source=['--admin.conf=x.ini']
            )
            assert False, "where's the missing exception?"
        except AllHandlersFailedException, x:
            self.assertTrue('ConfigParser cannot load' in str(x))
            if 'configobj' in sys.modules.keys():
                self.assertTrue('ConfigObj cannot load' in str(x))
        finally:
            os.remove('x.ini')

    #--------------------------------------------------------------------------
    def test_get_option_definitions(self):
        n = self._common_app_namespace_setup()
        n.add_option('silly', default=1)
        n.add_aggregation('strange', lambda x, y: 4)
        n.add_aggregation('weird', lambda x, y: 11)
        n.add_option('concrete', default=68)

        cm = config_manager.ConfigurationManager(
            (n,),
            argv_source=[]
        )
        opts = cm.get_option_names()
        for an_opt in opts:
            self.assertTrue(
                isinstance(cm.option_definitions[an_opt], Option)
            )
        self.assertEqual(len(opts), 9)  # there must be exactly 9 options

    #--------------------------------------------------------------------------
    @mock.patch('configman.config_manager.warnings')
    def test_warn_on_one_excess_options(self, mocked_warnings):
        if 'configobj' not in sys.modules.keys():
            raise SkipTest

        n = self._common_app_namespace_setup()
        n.add_option('foo')
        open('x.ini', 'w').write(
            'foo=FOO\n'
            'bar=BAR\n'
        )
        try:
            config_manager.ConfigurationManager(
                (n,),
                argv_source=['--admin.conf=x.ini']
            )
            mocked_warnings.warn.assert_called_once_with(
                'Invalid options: bar'
            )
        finally:
            os.remove('x.ini')

    #--------------------------------------------------------------------------
    @mock.patch('configman.config_manager.warnings')
    def test_warn_on_multiple_excess_options(self, mocked_warnings):
        if 'configobj' not in sys.modules.keys():
            raise SkipTest

        n = self._common_app_namespace_setup()
        n.add_option('foo')
        open('x.ini', 'w').write(
            'foo=FOO\n'
            'bar=BAR\n'
            'baz=BAZ\n'
        )
        try:
            config_manager.ConfigurationManager(
                (n,),
                argv_source=['--admin.conf=x.ini']
            )
            mocked_warnings.warn.assert_called_once_with(
                'Invalid options: bar, baz'
            )
        finally:
            os.remove('x.ini')

    #--------------------------------------------------------------------------
    def test_overlay_bug(self):
        # for Options that already exist and have been seen by the overlay
        # process, make sure that expanding a class doesn't just overwrite
        # the values back to their original defaults

        r = Namespace()
        r.add_option('fred', default=0)
        r.add_option(
            'class',
            default=int,
            from_string_converter=class_converter
        )

        # this class will bring in an Option that already exists called "fred".
        # Since overlay is done before expansion, "fred" should get set to 99.
        # Then expansion will bring in A's "fred" with a value of 77.  We need
        # make sure that the overlay process then puts its back to 99.
        class A(RequiredConfig):
            required_config = Namespace()
            required_config.add_option('fred', default='77')

        cm = config_manager.ConfigurationManager(
            [r],
            [{'fred': 21}, {'class': A}, {'fred': 99}]
        )
        cn = cm.get_config()
        self.assertEqual(cn.fred, 99)

    #--------------------------------------------------------------------------
    def test_overlay_reference_value_from_bug(self):
        # for Options that already exist and have been seen by the overlay
        # process, make sure that expanding a class doesn't just overwrite
        # the values back to their original defaults

        r = Namespace()
        r.add_option('fred', default=0, reference_value_from='a')
        r.add_option(
            'class',
            default=int,
            from_string_converter=class_converter
        )

        # this class will bring in an Option that already exists called "fred".
        # Since overlay is done before expansion, "fred" should get set to 99.
        # Then expansion will bring in A's "fred" with a value of 77.  We need
        # make sure that the overlay process then puts its back to 99.
        class A(RequiredConfig):
            required_config = Namespace()
            required_config.add_option(
                'fred',
                default='77',
                reference_value_from='a'
            )

        cm = config_manager.ConfigurationManager(
            [r],
            [{'a.fred': 21}, {'class': A}, {'a.fred': 99}]
        )
        cn = cm.get_config()
        self.assertEqual(cn.fred, 99)

