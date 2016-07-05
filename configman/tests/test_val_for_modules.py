# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function

import unittest
import contextlib
import re
import six

from six.moves import cStringIO as StringIO
from datetime import datetime, timedelta, date

from mock import Mock

from configman import (
    RequiredConfig,
    Namespace,
    ConfigurationManager,
    command_line
)
from configman.option import Option
from configman.config_exceptions import CannotConvertError, NotAnOptionError
from configman.value_sources.for_modules import OrderableObj, OrderableTuple, \
    ValueSource
from configman.converters import class_converter


#==============================================================================
class Alpha(RequiredConfig):
    required_config = Namespace()
    required_config.add_option('a', doc='a', default=17)

    #--------------------------------------------------------------------------
    def __init__(self, config):
        self.config = config
        self.a = config.a


#==============================================================================
class Beta(RequiredConfig):
    required_config = Namespace()
    required_config.add_option(
        'b',
        doc='b',
        default=23
    )

    #--------------------------------------------------------------------------
    def __init__(self, config):
        self.config = config
        self.b = config.b


#==============================================================================
class Delta(RequiredConfig):
    required_config = Namespace()
    required_config.add_option(
        'messy',
        doc='messy',
        default=-99
    )
    required_config.add_option(
        'dd',
        doc='dd',
        default=Beta,
        from_string_converter=class_converter
    )


#==========================================================================
class TestCase(unittest.TestCase):
    maxDiff = None

    #--------------------------------------------------------------------------
    def test_basic_import(self):
        config_manager = Mock()
        vs = ValueSource('configman.tests.values_for_module_tests_1')
        v = vs.get_values(config_manager, True)

        self.assertEqual(v['a'], 18)
        self.assertEqual(v['b'], [1, 2, 3, 3])
        self.assertEqual(v['c'], set(v['b']))
        self.assertEqual(v['d']['a'], v['a'])
        self.assertEqual(v['d']['b'], v['b'])
        self.assertEqual(v['d']['c'], v['c'])
        self.assertEqual(v['d']['d'], {1: 'one', 2: 'two'})
        self.assertEqual(v['foo'](1, 2, 3), '123')
        self.assertTrue('partial' not in v)
        self.assertEqual(v['bar'](b=8, c=9), '1889')
        self.assertEqual(str(v['Alpha'](*list(v['c']))), '123')

        self.assertFalse('x' in v)
        self.assertFalse('y' in v)
        self.assertFalse('os' in v)
        self.assertTrue('collections' in v)

        self.assertTrue('__package__' not in list(v.keys()))
        self.assertTrue('__builtins__' not in list(v.keys()))
        self.assertTrue('__doc__' in list(v.keys()))
        self.assertTrue(v.__doc__.startswith('This is a test'))

        from collections import Mapping
        self.assertTrue(v.collections.Mapping is Mapping)
        from types import ModuleType
        self.assertTrue(isinstance(v.collections, ModuleType))

    #--------------------------------------------------------------------------
    def test_failure_1(self):
        """complete failure, the module does not exist"""
        self.assertRaises(
            CannotConvertError,
            ValueSource,
            'configman.tests.values_4_module_tests_1'
        )

    #--------------------------------------------------------------------------
    def test_failure_2(self):
        """wrong format, don't use os style paths, use dotted forms"""
        self.assertRaises(
            CannotConvertError,
            ValueSource,
            'configman/tests/test_val_for_modules.py'
        )

    #--------------------------------------------------------------------------
    def test_as_overlay(self):
        rc = Namespace()
        rc.add_option(
            'a',
            default=23
        )
        rc.add_option(
            'b',
            default='this is b'
        )
        rc.namespace('n')
        rc.n.add_option(
            'x',
            default=datetime(1999, 12, 31, 11, 59)
        )
        rc.n.add_option(
            'y',
            default=timedelta(3)
        )
        rc.n.add_option(
            'z',
            default=date(1650, 10, 2)
        )
        rc.dynamic_load = None

        cm = ConfigurationManager(
            [rc],
            values_source_list=[
                'configman.tests.values_for_module_tests_2',
                'configman.tests.values_for_module_tests_3',
            ]
        )
        config = cm.get_config()

        self.assertEqual(config.a, 99)
        self.assertEqual(config.b, 'now is the time')
        self.assertEqual(config.n.x,  datetime(1960, 5, 4, 15, 10))
        self.assertEqual(config.n.y,  timedelta(1))
        self.assertEqual(config.n.z, date(1960, 5, 4))
        from configman.tests.values_for_module_tests_3 import Alpha
        self.assertEqual(config.dynamic_load, Alpha)
        self.assertEqual(config.host, 'localhost')
        self.assertEqual(config.port, 5432)

    #--------------------------------------------------------------------------
    def test_as_overlay_bad_symbols_with_strict(self):
        rc = Namespace()
        rc.add_option(
            'a',
            default=23
        )
        rc.add_option(
            'b',
            default='this is b'
        )
        rc.namespace('n')
        rc.n.add_option(
            'x',
            default=datetime(1999, 12, 31, 11, 59)
        )
        rc.n.add_option(
            'y',
            default=timedelta(3)
        )
        rc.n.add_option(
            'z',
            default=date(1650, 10, 2)
        )
        rc.dynamic_load = None

        self.assertRaises(
            NotAnOptionError,
            ConfigurationManager,
            [rc],
            values_source_list=[
                'configman.tests.values_for_module_tests_2',
                'configman.tests.values_for_module_tests_4',
                command_line
            ],
            argv_source=['--admin.strict'],
        )

    #--------------------------------------------------------------------------
    def test_write_simple(self):
        rc = Namespace()
        rc.add_option(
            'a',
            default=23
        )
        rc.add_option(
            'b',
            default='this is b'
        )
        rc.namespace('n')
        rc.n.add_option(
            'x',
            default=datetime(1999, 12, 31, 11, 59)
        )
        rc.n.add_option(
            'y',
            default=timedelta(3)
        )
        rc.n.add_option(
            'z',
            default=date(1650, 10, 2)
        )

        cm = ConfigurationManager(
            [rc],
            values_source_list=[
                {
                    'a': 68,
                    'n.x': datetime(1960, 5, 4, 15, 10),
                    'n.y': timedelta(3),
                    'n.z': date(2001, 1, 1)
                }
            ]
        )
        s = StringIO()

        @contextlib.contextmanager
        def s_opener():
            yield s

        cm.write_conf('py', s_opener)
        r = s.getvalue()
        g = {}
        l = {}
        six.exec_(r, g, l)
        self.assertEqual(l['a'], 68)
        self.assertEqual(l['b'], 'this is b')
        self.assertEqual(l['n'].x, datetime(1960, 5, 4, 15, 10))
        self.assertEqual(l['n'].y, timedelta(3))
        self.assertEqual(l['n'].z, date(2001, 1, 1))

    #--------------------------------------------------------------------------
    def test_write_with_imported_module(self):
        import os
        from configman.tests.values_for_module_tests_1 import Alpha, foo, a

        definitions = {
            'os_module': os,
            'a': 17,
            'imported_class': Alpha,
            'imported_function': foo,
            'xxx': {
                'yyy': a,
            }
        }
        cm = ConfigurationManager(
            definitions,
            values_source_list=[],
        )
        s = StringIO()

        @contextlib.contextmanager
        def s_opener():
            yield s

        cm.write_conf('py', s_opener)
        generated_python_module_text = s.getvalue()
        expected = """# generated Python configman file

from configman.dotdict import DotDict
from configman.tests.values_for_module_tests_1 import (
    Alpha,
    foo,
)

import os

# the following symbols will be ignored by configman when
# this module is used as a value source.  This will
# suppress the mismatch warning since these symbols are
# values for options, not option names themselves.
ignore_symbol_list = [
    "Alpha",
    "DotDict",
    "foo",
    "os",
]


# a
a = 17

# imported_class
imported_class = Alpha

# imported_function
imported_function = foo

# os_module
os_module = os

# Namespace: xxx
xxx = DotDict()

# yyy
xxx.yyy = 18
"""
        if six.PY2:
            expected = six.binary_type(expected)
        self.assertEqual(generated_python_module_text, expected)

    #--------------------------------------------------------------------------
    def test_write_with_imported_module_with_internal_mappings(self):
        import os
        from configman.tests.values_for_module_tests_1 import Alpha, foo

        d = {
            'a': 18,
            'b': 'hello',
            'c': [1, 2, 3],
            'd': {
                'host': 'localhost',
                'port': 5432,
            }
        }

        definitions = {
            'os_module': os,
            'a': 17,
            'imported_class': Alpha,
            'imported_function': foo,
            'xxx': {
                'yyy': Option('yyy', default=d)
            },
            'e': None,
        }
        required_config = Namespace()
        required_config.add_option(
            'minimal_version_for_understanding_refusal',
            doc='ignore the Thottleable protocol',
            default={'Firefox': '3.5.4'},
        )

        cm = ConfigurationManager(
            [definitions, required_config],
            values_source_list=[],
        )

        cm.get_config()

        s = StringIO()

        @contextlib.contextmanager
        def s_opener():
            yield s

        cm.write_conf('py', s_opener)
        generated_python_module_text = s.getvalue()

        expected = """# generated Python configman file

from configman.dotdict import DotDict
from configman.tests.values_for_module_tests_1 import (
    Alpha,
    foo,
)

import os

# the following symbols will be ignored by configman when
# this module is used as a value source.  This will
# suppress the mismatch warning since these symbols are
# values for options, not option names themselves.
ignore_symbol_list = [
    "Alpha",
    "DotDict",
    "foo",
    "os",
]


# a
a = 17

# e
e = None

# imported_class
imported_class = Alpha

# imported_function
imported_function = foo

# ignore the Thottleable protocol
minimal_version_for_understanding_refusal = {
    "Firefox": "3.5.4"
}

# os_module
os_module = os

# Namespace: xxx
xxx = DotDict()

xxx.yyy = {
    "a": 18,
    "b": "hello",
    "c": [
        1,
        2,
        3
    ],
    "d": {
        "host": "localhost",
        "port": 5432
    }
}
"""
        self.assertEqual(generated_python_module_text, expected)

    #--------------------------------------------------------------------------
    def test_write_with_imported_module_with_regex(self):
        required_config = Namespace()
        required_config.add_option(
            'identifier',
            doc='just an identifier re',
            default=r'[a-zA-Z][a-zA-Z0-9]*',
            from_string_converter=re.compile
        )
        cm = ConfigurationManager(
            required_config,
            values_source_list=[],
        )
        cm.get_config()

        s = StringIO()

        @contextlib.contextmanager
        def s_opener():
            yield s

        cm.write_conf('py', s_opener)
        generated_python_module_text = s.getvalue()
        expected = """# generated Python configman file



# just an identifier re
identifier = "[a-zA-Z][a-zA-Z0-9]*"
"""
        self.assertEqual(generated_python_module_text, expected)

    #--------------------------------------------------------------------------
    def test_write_skip_aggregations(self):
        required_config = Namespace()
        required_config.add_option(
            'minimal_version_for_understanding_refusal',
            doc='ignore the Thottleable protocol',
            default={'Firefox': '3.5.4'},
        )
        required_config.add_aggregation(
            'an_agg',
            lambda x, y, z: 'I refuse'
        )

        cm = ConfigurationManager(
            required_config,
            values_source_list=[],
        )

        cm.get_config()

        s = StringIO()

        @contextlib.contextmanager
        def s_opener():
            yield s

        cm.write_conf('py', s_opener)
        generated_python_module_text = s.getvalue()

        expected = """# generated Python configman file



# ignore the Thottleable protocol
minimal_version_for_understanding_refusal = {
    "Firefox": "3.5.4"
}
"""
        self.assertEqual(generated_python_module_text, expected)

    #--------------------------------------------------------------------------
    def test_orderable_obj(self):
        d = {
            "a": 1,
            3: 4,
            None: 3
        }
        sorted_list = [y.value for y in sorted([OrderableObj(x) for x in
                       d.keys()])]
        self.assertEqual(sorted_list, [None, 3, 'a'])

    #--------------------------------------------------------------------------
    def test_orderable_tuple(self):
        a = [
            (print, 'foo'),
            [sorted, 'bar'],
        ]

        sorted_list = [y.value for y in sorted([OrderableTuple(x) for x in a])]
        self.assertEqual(sorted_list, [[sorted, 'bar'], (print, 'foo')])
