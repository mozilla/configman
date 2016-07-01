# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
import os
import os.path
import unittest
from contextlib import contextmanager
import io
from six.moves import cStringIO as StringIO
import getopt
import six

import mock

import configman.config_manager as config_manager
from configman.option import Option
from configman.dotdict import (
    DotDict,
    DotDictWithAcquisition,
    create_key_translating_dot_dict,
)
from configman import Namespace, RequiredConfig
from configman.config_file_future_proxy import ConfigFileFutureProxy
from configman.converters import class_converter, to_str
from configman.datetime_util import datetime_from_ISO_string
from configman.config_exceptions import NotAnOptionError
from configman.value_sources.source_exceptions import (
    AllHandlersFailedException,
    UnknownFileExtensionException,
)


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
class AClass(RequiredConfig):
    required_config = Namespace()
    required_config.namespace('zzz')
    required_config.zzz.namespace('fff')
    required_config.zzz.fff.add_option(
        'a',
        doc='another a',
        default=3888,
        reference_value_from='xxx.yyy'
    )
    required_config.zzz.fff.add_option(
        'bclass',
        default='configman.tests.test_config_manager.BClass',
        from_string_converter=class_converter
    )


#==============================================================================
class BClass(RequiredConfig):
    required_config = Namespace()
    required_config.namespace('ooo')
    required_config.ooo.add_option(
        'a',
        doc='another a',
        default=9988,
        reference_value_from='xxx.yyy'
    )


#==============================================================================
class TestCase(unittest.TestCase):

    def shortDescription(self):
        # so we can see the path to the failing test
        return None

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
            from_string_converter=datetime_from_ISO_string
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
        ini_data = b"""
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
        ini_data = b"""
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
        ini_data = b"""
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
    def test_overlay_config_12(self):
        """test overlay dict w/deep source dict and reference value links
        with dynamic class loading"""
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
        n.c.add_option(
            'thingy',
            default='configman.tests.test_config_manager.AClass',
            from_string_converter=class_converter
        )
        value_source = {
            'xxx': {
                'yyy': {
                    'a': 2,
                    'extra': 2.89
                }
            }
        }
        c = config_manager.ConfigurationManager(
            [n],
            [
                {'b': 21},
                {'c.a': 399},
                value_source,
            ],
            use_admin_controls=True,
            use_auto_help=False,
            argv_source=[]
        )
        self.assertTrue(isinstance(
            c.option_definitions.b,
            config_manager.Option
        ))
        self.assertEqual(c.option_definitions.a.value, 2)
        self.assertEqual(c.option_definitions.b.value, 21)
        self.assertEqual(c.option_definitions.b.default, 21)
        self.assertEqual(c.option_definitions.b.name, 'b')
        self.assertEqual(c.option_definitions.c.extra.name, 'extra')
        self.assertEqual(c.option_definitions.c.extra.doc, 'the x')
        self.assertEqual(c.option_definitions.c.extra.default, 2.89)
        self.assertEqual(c.option_definitions.c.extra.value, 2.89)
        self.assertEqual(c.option_definitions.c.a.default, 399)
        self.assertEqual(c.option_definitions.c.a.value, 399)
        self.assertEqual(c.option_definitions.c.zzz.fff.a.value, 2)
        self.assertEqual(c.option_definitions.c.zzz.fff.a.default, 2)
        self.assertEqual(c.option_definitions.c.zzz.fff.ooo.a.default, 2)
        self.assertEqual(c.option_definitions.c.zzz.fff.ooo.a.value, 2)

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
    def test_output_summary_with_argument_1(self):
        """test_output_summary: the output from help where one item is a
        non-switch argument with no default value - the help output should
        list that argument by name, shown as not optional"""
        n = config_manager.Namespace()
        n.add_option('application', None, 'the app', is_argument=True)
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
            argv_source=['some_app'],
        )
        s = StringIO()
        c.output_summary(output_stream=s)
        r = s.getvalue()
        self.assertTrue('[OPTIONS]... ' in r)
        self.assertTrue('application' in r)  # yeah, we want to see option

    #--------------------------------------------------------------------------
    def test_output_summary_with_argument_2(self):
        """test_output_summary: the output from help where one item is a
        non-switch argument with no default value - but the non-switch
        with no default has been given a value by a value source.  That
        argument should be shown by help with its value rather than its name
        and its should show it as not optional."""
        n = config_manager.Namespace()
        n.add_option(
            'application',
            None,
            'the app',
            is_argument=True,
            from_string_converter=class_converter
        )
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
            values_source_list=[{
                'application': object  # just want any old class here
            }],
            use_admin_controls=True,
            use_auto_help=False,
            argv_source=[],
        )
        s = StringIO()
        c.output_summary(output_stream=s)
        r = s.getvalue()
        self.assertTrue('OPTIONS:\n' in r)
        self.assertFalse('application' in r)  # we don't want this as an option
        self.assertTrue('object' in r)  # yeah, we want original str value
        self.assertFalse('[ object' in r)  # but not as listed as optional

    #--------------------------------------------------------------------------
    def test_output_summary_with_argument_3(self):
        """test_output_summary: the output from help where one item is a
        non-switch argument with no default value"""
        n = config_manager.Namespace()
        n.add_option('application', 'somevalue', 'the app', is_argument=True)
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
        self.assertTrue('application' in r)  # it ought to be there
        self.assertTrue('[ application' in r)  # listed as optional
        self.assertFalse('[ somevalue' in r)  # by name not by value

    #--------------------------------------------------------------------------
    def test_output_summary_with_secret(self):
        """test the output_summary with a certain field that isn't called
        "password" or anything alike but it shouldn't be exposed anyway."""
        n = config_manager.Namespace()
        n.add_option(
            'secret',
            default='I hate people',
            doc='The secret',
            secret=True
        )
        c = config_manager.ConfigurationManager(
            [n],
            use_admin_controls=True,
            use_auto_help=False,
            argv_source=[],
        )
        s = StringIO()

        self.assertFalse(c.option_definitions.admin.expose_secrets.default)
        self.assertFalse(c.option_definitions.admin.expose_secrets.value)

        c.output_summary(output_stream=s)
        r = s.getvalue()

        self.assertTrue('--secret' in r)
        self.assertFalse('I hate people' in r)

    #--------------------------------------------------------------------------
    def test_output_summary_with_secret_exposed(self):
        """test the output_summary with a certain field that isn't called
        "password" or anything alike but it shouldn't be exposed anyway."""
        n = config_manager.Namespace()
        n.add_option(
            'secret',
            default='I hate people',
            doc='The secret',
            secret=True
        )
        c = config_manager.ConfigurationManager(
            [n],
            use_admin_controls=True,
            use_auto_help=False,
            argv_source=["--admin.expose_secrets"],
        )
        s = StringIO()

        self.assertTrue(c.option_definitions.admin.expose_secrets.default)
        self.assertTrue(c.option_definitions.admin.expose_secrets.value)

        c.output_summary(output_stream=s)
        r = s.getvalue()

        self.assertTrue('--secret' in r)
        self.assertTrue('I hate people' in r)

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
            ('admin.expose_secrets', 'expose_secrets', False),
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
        if six.PY3:
            e[3] = "application: <class 'configman.tests.test_config_manager.TestCase.test_log_config.<locals>.MyApp'>"
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
        self.assertEqual(list(conf.keys()), ['admin', 'application'])

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
        n.add_option(
            'gender',
            default='Male',
            doc='what gender identity?',
        )
        n.add_option(
            'salary',
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
    def test_print_conf_with_secrets(self):
        # the main purpose of this test is to indirectly test the method
        # ConfigurationManager.write_conf
        n = config_manager.Namespace()
        n.add_option(
            'gender',
            default='Male',
            doc='what gender identity?',
        )
        n.add_option(
            'salary',
            default=10000,
            doc='How much do you earn?',
            secret=True,
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
        self.assertTrue('salary' in printed)
        self.assertTrue('*' * 16 in printed)

    #--------------------------------------------------------------------------
    def test_print_conf_with_secrets_exposed(self):
        # the main purpose of this test is to indirectly test the method
        # ConfigurationManager.write_conf
        n = config_manager.Namespace()
        n.add_option(
            'gender',
            default='Male',
            doc='what gender identity?',
        )
        n.add_option(
            'salary',
            default=10000,
            doc='How much do you earn?',
            secret=True,
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
                argv_source=[
                    '--admin.print_conf=ini',
                    '--admin.expose_secrets'
                ],
                config_pathname='fred'
            )
        finally:
            sys.stdout = old_stdout

        printed = temp_output.getvalue()
        self.assertTrue('gender' in printed)
        self.assertTrue('salary' in printed)
        self.assertTrue('*' * 16 not in printed)

    #--------------------------------------------------------------------------
    def test_dump_conf_some_options_excluded(self):
        n = config_manager.Namespace()
        n.add_option('gender',
                     default='Male',
                     doc='what gender identity?',
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
            self.assertTrue('name' in all_config['sub1'])
            self.assertTrue('name' in local_namespace)
            self.assertTrue('spouse' in local_namespace)
            self.assertEqual(len(args), 2)
            return AggregatedValue('%s married %s using password %s but '
                                   'divorced because of %s.' %
                                   (local_namespace['name'],
                                    local_namespace['spouse'],
                                    all_config['password'],
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
            self.assertEqual(
                statement.value,
                'wilma married fred using password @$*$&26Ht '
                'but divorced because of arg2.'
            )
        self.assertTrue(statement.value is None)

        with c.context(mapping_class=dict) as config:
            self.assertTrue(isinstance(config, dict))
            statement = config['sub1']['statement']
            self.assertEqual(
                statement.value,
                'wilma married fred using password @$*$&26Ht '
                'but divorced because of arg2.'
            )
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
        self.assertEqual(list(conf.keys()), ['source', 'destination', 'admin'])
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
        cm = config_manager.ConfigurationManager(
            rc,
            [
                DotDictWithAcquisition(
                    {'cls': 'configman.tests.test_config_manager.T2'}
                ),
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
        with open('x.fred', 'w') as f:
            f.write(
                '[toplevel]\n'
                'password=something\n'
            )
        try:
            self.assertRaises(
                AllHandlersFailedException,
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
        except AllHandlersFailedException as x:
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
            values_source_list=[ConfigFileFutureProxy, getopt],
            argv_source=[],
        )
        opts = cm.get_option_names()
        for an_opt in opts:
            self.assertTrue(
                isinstance(cm.option_definitions[an_opt], Option)
            )
        self.assertEqual(len(opts), 10)  # there must be exactly 10 options

    #--------------------------------------------------------------------------
    @mock.patch('configman.config_manager.warnings')
    def test_warn_on_one_excess_options(self, mocked_warnings):
        assert 'configobj' in sys.modules.keys()

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
        assert 'configobj' in sys.modules.keys()

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
                six.text_type('Invalid options: bar, baz')
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

    #--------------------------------------------------------------------------
    def test_overlay_reference_value_from_bug_2(self):
        # for Options that already exist and have been seen by the overlay
        # process, make sure that expanding a class doesn't just overwrite
        # the values back to their original defaults
        class A(RequiredConfig):
            required_config = Namespace()
            required_config.add_option(
                'fred',
                default='77',
                reference_value_from='a'
            )

        class B(RequiredConfig):
            required_config = Namespace()
            required_config.add_option(
                'a_class',
                default=A,
                from_string_converter=class_converter,
                reference_value_from='a'
            )

        r = Namespace()
        r.add_option(
            'some_class',
            default=A,
            from_string_converter=class_converter,
            reference_value_from='a'
        )
        r.add_option(
            'other_class',
            default=A,
            from_string_converter=class_converter,
            reference_value_from='a'
        )

        cm = config_manager.ConfigurationManager(
            [r],
            [
                {'a.fred': 21},
                {'other_class': B}
            ]
        )
        cn = cm.get_config()
        self.assertEqual(cn.fred, 21)
        self.assertEqual(cn.a.fred, 21)

    #--------------------------------------------------------------------------
    def test_expansion_new_req_as_dict_bug(self):
        # when a class is expanded and that class has required config that is
        # of Mapping that is not a Namespace or DotDict, adding those
        # requirements has been failing.  Test that it now works after a change
        # that converts them to Namespaces during the expansion process.
        class A(RequiredConfig):
            @staticmethod
            def get_required_config():
                return {
                    "alpha": 1,
                    "beta": True,
                    "gamma": "hello",
                }

        r = Namespace()
        r.add_option(
            'some_class',
            default=A,
            from_string_converter=class_converter,
        )

        cm = config_manager.ConfigurationManager(
            definition_source=[r],
            values_source_list=[],
            argv_source=[]
        )
        cn = cm.get_config()

        self.assertEqual(cn.alpha, 1)
        self.assertTrue(cn.beta)
        self.assertEqual(cn.gamma, 'hello')

    #--------------------------------------------------------------------------
    def test_value_source_object_hook_1(self):
        """the definition source defines only keys with underscores.
        the value sources may have hyphens instead of underscores.
        test the use of a translating DotDict varient that changes
        hyphens into underscores """

        class A(RequiredConfig):
            required_config = Namespace()
            required_config.add_option(
                'f_r_e_d',
                default='77',
                reference_value_from='a'
            )

        class B(RequiredConfig):
            required_config = Namespace()
            required_config.add_option(
                'a_class',
                default=A,
                from_string_converter=class_converter,
                reference_value_from='a'
            )

        r = Namespace()
        r.add_option(
            'some_class',
            default=A,
            from_string_converter=class_converter,
            reference_value_from='a'
        )
        r.add_option(
            'other_class',
            default=A,
            from_string_converter=class_converter,
            reference_value_from='a'
        )

        cm = config_manager.ConfigurationManager(
            [r],
            [
                {'a.f-r-e-d': 21},
                {'other-class': B}
            ],
            value_source_object_hook=create_key_translating_dot_dict(
                'HyphenIsUnderScoreDotDict',
                (('-', '_'),),
            )
        )
        cn = cm.get_config()
        self.assertEqual(cn.f_r_e_d, 21)
        self.assertEqual(cn.a.f_r_e_d, 21)
        self.assertTrue(cn.other_class is B)
        self.assertTrue(cn.some_class is A)

    #--------------------------------------------------------------------------
    def test_value_source_object_hook_2(self):
        """the object hook system can be used to post process the value sources
        as they're used in configman.  Define a mapping that insures that all
        values are uppercase"""

        class A(RequiredConfig):
            required_config = Namespace()
            required_config.add_option(
                'fred',
                default='abcdefgh',
                reference_value_from='a'
            )

        class B(RequiredConfig):
            required_config = Namespace()
            required_config.add_option(
                'a_class',
                default=A,
                from_string_converter=class_converter,
                reference_value_from='a'
            )
            required_config.add_option(
                'name',
                default='wilma',
                reference_value_from='a'
            )

        r = Namespace()
        r.add_option(
            'some_class',
            default=A,
            from_string_converter=class_converter,
            reference_value_from='a'
        )
        r.add_option(
            'other_class',
            default=A,
            from_string_converter=class_converter,
            reference_value_from='a'
        )

        class UpperCaseValueDotDict(DotDict):
            def __setattr__(self, key, value):
                if isinstance(value, (six.binary_type, six.text_type)):
                    value = to_str(value)
                    super(UpperCaseValueDotDict, self).__setattr__(
                        key,
                        value.upper()
                    )
                else:
                    super(UpperCaseValueDotDict, self).__setattr__(
                        key,
                        value
                    )

        cm = config_manager.ConfigurationManager(
            [r],
            [
                {
                    'a.fred': 'this should be uppercase',
                    'a.name': 'uppercase'
                },
                {'other_class': B}
            ],
            value_source_object_hook=UpperCaseValueDotDict
        )
        cn = cm.get_config()
        self.assertEqual(cn.fred, "THIS SHOULD BE UPPERCASE")
        self.assertEqual(cn.a.fred, "THIS SHOULD BE UPPERCASE")
        self.assertEqual(cn.name, "UPPERCASE")
        self.assertTrue(cn.other_class is B)
        self.assertTrue(cn.some_class is A)

    #--------------------------------------------------------------------------
    def test_bare_configuration_call(self):
        from configman import configuration

        class AggregatedValue(object):

            def __init__(self, value):
                self.value = value

            def close(self):
                self.value = None

        def aggregation_test(all_config, local_namespace, args):
            self.assertTrue('password' in all_config)
            self.assertTrue('sub1' in all_config)
            self.assertTrue('name' in all_config['sub1'])
            self.assertTrue('name' in local_namespace)
            self.assertTrue('spouse' in local_namespace)
            self.assertEqual(len(args), 2)
            return AggregatedValue('%s married %s using password %s but '
                                   'divorced because of %s.' %
                                   (local_namespace['name'],
                                    local_namespace['spouse'],
                                    all_config['password'],
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

        config = configuration(
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

        self.assertTrue(isinstance(config, DotDictWithAcquisition))
        statement = config['sub1']['statement']
        self.assertEqual(
            statement.value,
            'wilma married fred using password @$*$&26Ht '
            'but divorced because of arg2.'
        )

        config = configuration(
            n,
            [getopt],
            use_admin_controls=False,
            use_auto_help=False,
            argv_source=[
                '--sub1.name=wilma',
                'arg1',
                'arg2'
            ],
            mapping_class=dict
        )

        self.assertTrue(isinstance(config, dict))
        statement = config['sub1']['statement']
        self.assertEqual(
            statement.value,
            'wilma married fred using password @$*$&26Ht '
            'but divorced because of arg2.'
        )

    #--------------------------------------------------------------------------
    def test_configmanger_set_has_changed_successfully(self):

        n = config_manager.Namespace()
        n.add_option(
            name='dwight',
            default=0
        )
        n.add_option(
            name='wilma',
            default=0
        )
        n.add_option(
            name='sarita',
            default=0
        )
        n.add_option(
            name='robert',
            default=0
        )

        config = config_manager.ConfigurationManager(
            n,
            [
                {
                    "dwight": 20,
                },
                {
                    "dwight": 22,
                    "wilma": 10
                },
                {
                    "wilma": 0,
                    "robert": 16,
                },
            ],
            use_admin_controls=False,
            use_auto_help=False,
            argv_source=[]
        )
        self.assertTrue(config.option_definitions.dwight.has_changed)
        self.assertFalse(config.option_definitions.wilma.has_changed)
        self.assertFalse(config.option_definitions.sarita.has_changed)
        self.assertTrue(config.option_definitions.robert.has_changed)
