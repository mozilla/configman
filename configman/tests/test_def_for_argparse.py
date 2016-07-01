# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function

from unittest import TestCase
from mock import patch

import six
from six import StringIO

try:
    import argparse
except ImportError:
    try:
        from unittest import SkipTest
    except ImportError:
        from nose.plugins.skip import SkipTest
    raise SkipTest

from configman import ArgumentParser
from configman.dotdict import DotDict

expected_value = {
    "test_expansion_subparsers_1":
"""usage: highwater [-h] [--admin.print_conf ADMIN.PRINT_CONF]
                 [--admin.dump_conf ADMIN.DUMP_CONF] [--admin.strict]
                 [--admin.expose_secrets] [--admin.conf ADMIN.CONF] [--foo]
                 [--egg EGG]
                 {a,b} ...

positional arguments:
  {a,b}                 sub-command help
    a                   a help
    b                   b help

optional arguments:
  -h, --help            show this help message and exit
  --admin.print_conf ADMIN.PRINT_CONF
                        write current config to stdout (json, py, conf, env,
                        ini)
  --admin.dump_conf ADMIN.DUMP_CONF
                        a pathname to which to write the current config
  --admin.strict        mismatched options generate exceptions rather than
                        just warnings
  --admin.expose_secrets
                        should options marked secret get written out or
                        hidden?
  --admin.conf ADMIN.CONF
                        the pathname of the config file (path/filename)
  --foo                 foo help
  --egg EGG             eggs
""",

    "test_expansion_subparsers_2":
"""usage: highwater a [-h] [--admin.print_conf ADMIN.PRINT_CONF]
                   [--admin.dump_conf ADMIN.DUMP_CONF] [--admin.strict]
                   [--admin.expose_secrets] [--admin.conf ADMIN.CONF]
                   [--fff FFF]
                   bar

positional arguments:
  bar                   bar help

optional arguments:
  -h, --help            show this help message and exit
  --admin.print_conf ADMIN.PRINT_CONF
                        write current config to stdout (json, py, conf, env,
                        ini)
  --admin.dump_conf ADMIN.DUMP_CONF
                        a pathname to which to write the current config
  --admin.strict        mismatched options generate exceptions rather than
                        just warnings
  --admin.expose_secrets
                        should options marked secret get written out or
                        hidden?
  --admin.conf ADMIN.CONF
                        the pathname of the config file (path/filename)
  --fff FFF             a fff help
""",
    "test_expansion_subparsers_3":
"""usage: highwater b [-h] [--admin.print_conf ADMIN.PRINT_CONF]
                   [--admin.dump_conf ADMIN.DUMP_CONF] [--admin.strict]
                   [--admin.expose_secrets] [--admin.conf ADMIN.CONF]
                   [--baz {X,Y,Z}] [--fff {X,Y,Z}]

optional arguments:
  -h, --help            show this help message and exit
  --admin.print_conf ADMIN.PRINT_CONF
                        write current config to stdout (json, py, conf, env,
                        ini)
  --admin.dump_conf ADMIN.DUMP_CONF
                        a pathname to which to write the current config
  --admin.strict        mismatched options generate exceptions rather than
                        just warnings
  --admin.expose_secrets
                        should options marked secret get written out or
                        hidden?
  --admin.conf ADMIN.CONF
                        the pathname of the config file (path/filename)
  --baz {X,Y,Z}         baz help
  --fff {X,Y,Z}         b fff help
""",
    "test_expansion_subparsers_4":
"""usage: highwater [--admin.print_conf ADMIN.PRINT_CONF]
                 [--admin.dump_conf ADMIN.DUMP_CONF] [--admin.strict]
                 [--admin.expose_secrets] [--admin.conf ADMIN.CONF] [--foo]
                 [--egg EGG]
                 {a,b} ...
highwater: error: argument sub_command: invalid choice: 'c' (choose from 'a', 'b')
""",
    "test_expansion_subparsers_5":
"""usage: highwater a [-h] [--admin.print_conf ADMIN.PRINT_CONF]
                   [--admin.dump_conf ADMIN.DUMP_CONF] [--admin.strict]
                   [--admin.expose_secrets] [--admin.conf ADMIN.CONF]
                   [--fff FFF]
                   bar
highwater a: error: too few arguments
""",
    "test_expansion_subparsers_6":
"""usage: highwater [-h] [--admin.print_conf ADMIN.PRINT_CONF]
                 [--admin.dump_conf ADMIN.DUMP_CONF] [--admin.strict]
                 [--admin.expose_secrets] [--admin.conf ADMIN.CONF] [--foo]
                 [--egg EGG]
                 {a,b} ...
highwater: error: unrecognized arguments: --baz Y
""",
    "test_expansion_subparsers_7":
"""usage: highwater [-h] [--admin.print_conf ADMIN.PRINT_CONF]
                 [--admin.dump_conf ADMIN.DUMP_CONF] [--admin.strict]
                 [--admin.expose_secrets] [--admin.conf ADMIN.CONF] [--foo]
                 [--egg EGG]
                 {a,b} ...
highwater: error: unrecognized arguments: 16
""",
    "test_expansion_subparsers_defaults_values_1":
    DotDict({
        'foo': None,
        'egg': None,
        'sub_command': 'a',
        'bar': 16,
        'fff': None,
        'admin.print_conf': None,
        'admin.dump_conf': '',
        'admin.strict': False,
        'admin.expose_secrets': False,
        'admin.conf': './highwater.ini',
    }),
    "test_expansion_subparsers_defaults_values_2":
    DotDict({
        'foo': None,
        'egg': None,
        'sub_command': 'a',
        'bar': 16,
        'fff': 9,
        'admin.print_conf': None,
        'admin.dump_conf': '',
        'admin.strict': False,
        'admin.expose_secrets': False,
        'admin.conf': './highwater.ini',
    }),
    "test_expansion_subparsers_defaults_values_3":
    DotDict({
        'foo': None,
        'egg': None,
        'sub_command': 'b',
        'baz': None,
        'fff': 'X',
        'admin.print_conf': None,
        'admin.dump_conf': '',
        'admin.strict': False,
        'admin.expose_secrets': False,
        'admin.conf': './highwater.ini',
    }),
}


#==============================================================================
class TestCaseForDefSourceArgparse(TestCase):

    #--------------------------------------------------------------------------
    def setup_argparse(self):
        parser = ArgumentParser(prog='hell')
        parser.add_argument(
            '-s',
            action='store',
            dest='simple_value',
            help='Store a simple value'
        )
        parser.add_argument(
            '--missing_from_help',
            action='store',
            dest='missing_from_help',
            help='should not be seen in help',
            suppress_help=True,
        )
        parser.add_argument(
            '-c',
            action='store_const',
            dest='constant_value',
            const='value-to-store',
            help='Store a constant value'
        )
        parser.add_argument(
            '-t',
            action='store_true',
            default=False,
            dest='boolean_switch',
            help='Set a switch to true'
        )
        parser.add_argument(
            '-f',
            action='store_false',
            default=False,
            dest='boolean_switch',
            help='Set a switch to false'
        )
        parser.add_argument(
            '-a',
            action='append',
            dest='collection',
            default=[],
            help='Add repeated values to a list',
        )
        parser.add_argument(
            '-A',
            action='append_const',
            dest='const_collection',
            const='value-1-to-append',
            default=[],
            help='Add different values to list'
        )
        parser.add_argument(
            '-B',
            action='append_const',
            dest='const_collection',
            const='value-2-to-append',
            help='Add different values to list'
        )
        parser.add_argument(
            '--version',
            action='version',
            version='%(prog)s 1.0'
        )
        return parser

    #--------------------------------------------------------------------------
    def test_parser_setup(self):
        parser = self.setup_argparse()
        config = parser.parse_args(args=[])

        self.assertEqual(len(config), 7)

        self.assertEqual(config.simple_value, None)
        self.assertEqual(config.constant_value, None)
        self.assertEqual(config.boolean_switch, False)
        self.assertEqual(config.collection, [])
        self.assertEqual(config.const_collection, [])

    #--------------------------------------------------------------------------
    def test_parser_1(self):
        parser = self.setup_argparse()
        config = parser.parse_args(args=['-s', '3', ])

        self.assertEqual(len(config), 7)

        self.assertEqual(config.simple_value, '3')
        self.assertEqual(config.constant_value, None)
        self.assertEqual(config.boolean_switch, False)
        self.assertEqual(config.collection, [])
        self.assertEqual(config.const_collection, [])

    #--------------------------------------------------------------------------
    def test_parser_2(self):
        parser = self.setup_argparse()
        config = parser.parse_args(args=['-c', ])

        self.assertEqual(len(config), 7)

        self.assertEqual(config.simple_value, None)
        self.assertEqual(config.constant_value, 'value-to-store')
        self.assertEqual(config.boolean_switch, False)
        self.assertEqual(config.collection, [])
        self.assertEqual(config.const_collection, [])

    #--------------------------------------------------------------------------
    def test_parser_3(self):
        parser = self.setup_argparse()
        config = parser.parse_args(args=['-t', ])

        self.assertEqual(len(config), 7)

        self.assertEqual(config.simple_value, None)
        self.assertEqual(config.constant_value, None)
        self.assertEqual(config.boolean_switch, True)
        self.assertEqual(config.collection, [])
        self.assertEqual(config.const_collection, [])

    #--------------------------------------------------------------------------
    def test_parser_4(self):
        parser = self.setup_argparse()
        config = parser.parse_args(args=['-f', ])

        self.assertEqual(len(config), 7)

        self.assertEqual(config.simple_value, None)
        self.assertEqual(config.constant_value, None)
        self.assertEqual(config.boolean_switch, False)
        self.assertEqual(config.collection, [])
        self.assertEqual(config.const_collection, [])

    #--------------------------------------------------------------------------
    def test_parser_5(self):
        parser = self.setup_argparse()
        config = parser.parse_args(args=['-a', '1'])

        self.assertEqual(len(config), 7)

        self.assertEqual(config.simple_value, None)
        self.assertEqual(config.constant_value, None)
        self.assertEqual(config.boolean_switch, False)
        self.assertEqual(config.collection, ['1'])
        self.assertEqual(config.const_collection, [])

    #--------------------------------------------------------------------------
    def test_parser_6(self):
        parser = self.setup_argparse()
        config = parser.parse_args(args=['-a', '1', '-a', '2'])

        self.assertEqual(len(config), 7)

        self.assertEqual(config.simple_value, None)
        self.assertEqual(config.constant_value, None)
        self.assertEqual(config.boolean_switch, False)
        self.assertEqual(config.collection, ['1', '2'])
        self.assertEqual(config.const_collection, [])

    #--------------------------------------------------------------------------
    def test_parser_7(self):
        parser = self.setup_argparse()
        config = parser.parse_args(args=['-A', ])

        self.assertEqual(len(config), 7)

        self.assertEqual(config.simple_value, None)
        self.assertEqual(config.constant_value, None)
        self.assertEqual(config.boolean_switch, False)
        self.assertEqual(config.collection, [])
        self.assertEqual(config.const_collection, ['value-1-to-append'])

    #--------------------------------------------------------------------------
    def test_parser_8(self):
        parser = self.setup_argparse()
        config = parser.parse_args(args=['-B', ])

        self.assertEqual(len(config), 7)

        self.assertEqual(config.simple_value, None)
        self.assertEqual(config.constant_value, None)
        self.assertEqual(config.boolean_switch, False)
        self.assertEqual(config.collection, [])
        self.assertEqual(config.const_collection, ['value-2-to-append'])

    #--------------------------------------------------------------------------
    def test_parser_9(self):
        parser = self.setup_argparse()
        config = parser.parse_args(args=['-A', '-B'])

        #self.assertEqual(len(config), 7)

        self.assertEqual(config.simple_value, None)
        self.assertEqual(config.constant_value, None)
        self.assertEqual(config.boolean_switch, False)
        self.assertEqual(config.collection, [])
        self.assertEqual(
            config.const_collection,
            ['value-1-to-append', 'value-2-to-append']
        )

    #--------------------------------------------------------------------------
    def test_parser_10(self):
        parser = self.setup_argparse()
        config = parser.parse_args(args=[
            '-A', '-B', '-a', '1', '-s', 'a', '-c', '-t', '-a', '2',
        ])

        self.assertEqual(config.simple_value, 'a')
        self.assertEqual(config.constant_value, 'value-to-store')
        self.assertEqual(config.boolean_switch, True)
        self.assertEqual(config.collection, ['1', '2'])
        self.assertEqual(
            config.const_collection,
            ['value-1-to-append', 'value-2-to-append']
        )

    #--------------------------------------------------------------------------
    def setup_subparser(self):
        parser = ArgumentParser(prog='highwater')
        parser.add_argument('--foo', action='store_true', help='foo help', dest='foo')
        parser.add_argument('--egg', action='store', help='eggs', type=str)
        subparsers = parser.add_subparsers(help='sub-command help', dest='sub_command')
        parser_a = subparsers.add_parser('a', help='a help')
        parser_a.add_argument('bar', type=int, help='bar help')
        parser_a.add_argument('--fff', type=int, help='a fff help')
        parser_b = subparsers.add_parser('b', help='b help')
        parser_b.add_argument('--baz', choices='XYZ', help='baz help')
        parser_b.add_argument('--fff', choices='XYZ', help='b fff help')

        return parser

    #--------------------------------------------------------------------------
    @patch('sys.stdout', new_callable=StringIO)
    def impl_for_subparser_stdout_with_exit(self, args, expected, mock_stdout):
        parser = self.setup_subparser()
        self.assertRaises(
            SystemExit,
            parser.parse_args,
            args
        )
        # Skip in py3 because of random argparse --help sorting
        if six.PY2:
            x = mock_stdout.getvalue()
            self.assertEqual(
                sorted(expected),
                sorted(x),
                'case: %s failed - %s != %s' % (args,  expected,  x)
            )

    #--------------------------------------------------------------------------
    @patch('sys.stdout', new_callable=StringIO)
    def impl_for_subparser_stdout(self, args, expected, mock_stdout):
        parser = self.setup_subparser()
        parser.parse_args(args=args)
        x = mock_stdout.getvalue()
        self.assertEqual(
            sorted(expected),
            sorted(x),
            'case: %s failed - %s != %s' % (args,  expected,  x)
        )

    #--------------------------------------------------------------------------
    @patch('sys.stderr', new_callable=StringIO)
    def impl_for_subparser_stderr_with_exit(self, args, expected, mock_stderr):
        parser = self.setup_subparser()
        self.assertRaises(
            SystemExit,
            parser.parse_args,
            args
        )
        # Skip in py3 because of random argparse --help sorting
        if six.PY2:
            x = mock_stderr.getvalue()
            self.assertEqual(
                sorted(expected),
                sorted(x),
                'case: %s failed - %s != %s' % (args,  expected,  x)
            )

    #--------------------------------------------------------------------------
    @patch('sys.stderr', new_callable=StringIO)
    def impl_for_subparser_stderr(self, args, expected, mock_stderr):
        parser = self.setup_subparser()
        parser.parse_args(args=args)
        x = mock_stderr.getvalue()
        self.assertEqual(
            sorted(expected),
            sorted(x),
            'case: %s failed - %s != %s' % (args,  expected,  x)
        )

    #--------------------------------------------------------------------------
    def test_expansion_subparsers_stdout_with_exit(self):
        tests = (
            (['--help'], expected_value['test_expansion_subparsers_1']),
            (['a', '--help'], expected_value['test_expansion_subparsers_2']),
            (['b', '--help'], expected_value['test_expansion_subparsers_3']),
        )
        for args, expected in tests:
            self.impl_for_subparser_stdout_with_exit(args, expected)

    #--------------------------------------------------------------------------
    def test_expansion_subparsers_stderr_with_exit(self):
        tests = (
            (['c'], expected_value['test_expansion_subparsers_4']),
            (['a', '-fff'], expected_value['test_expansion_subparsers_5']),
            (['a', '16', '--fff', '21', '--baz', 'Y'], expected_value['test_expansion_subparsers_6']),
            (['b', '16', '--fff', 'X'], expected_value['test_expansion_subparsers_7']),
        )
        for args, expected in tests:
            self.impl_for_subparser_stderr_with_exit(args, expected)

    #--------------------------------------------------------------------------
    def test_expansion_subparsers_values(self):
        tests = (
            (['a', '16'], expected_value['test_expansion_subparsers_defaults_values_1']),
            (['a', '16', '--fff=9'], expected_value['test_expansion_subparsers_defaults_values_2']),
            (['a', '16', '--fff', '9'], expected_value['test_expansion_subparsers_defaults_values_2']),
            (['b', '--fff', 'X'], expected_value['test_expansion_subparsers_defaults_values_3']),
        )
        parser = self.setup_subparser()
        for args, expected in tests:
            result = parser.parse_args(args=args)
            self.assertEqual(dict(result), dict(expected), '%s failed' % args)
