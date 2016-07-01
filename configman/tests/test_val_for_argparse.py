# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function

from unittest import TestCase

try:
    import argparse
    command_line = argparse
except ImportError:
    try:
        from unittest import SkipTest
    except ImportError:
        from nose.plugins.skip import SkipTest
    raise SkipTest

from mock import Mock

from functools import partial

from configman import Namespace, ConfigurationManager
from configman.converters import (
    class_converter,
    boolean_converter,
    list_converter,
    list_to_str,
)

from configman.def_sources.for_argparse import ArgumentParser
from configman.value_sources.for_argparse import (
    #issubclass_with_no_type_error,
    ValueSource,
)


#------------------------------------------------------------------------------
def quote_stripping_list_of_ints(a_string):
    quoteless = a_string.strip('\'"')
    return list_converter(
        quoteless,
        item_separator=' ',
        item_converter=int
    )


#==============================================================================
class TestCaseForValSourceArgparse(TestCase):

    #--------------------------------------------------------------------------
    def setup_value_source(self, type_of_value_source=ValueSource):
        conf_manager = Mock()
        conf_manager.argv_source = []

        arg = ArgumentParser()
        arg.add_argument(
            '--wilma',
            dest='wilma',
        )
        arg.add_argument(
            dest='dwight',
            nargs='*',
            type=int
        )
        vs = type_of_value_source(arg, conf_manager)
        return vs

    #--------------------------------------------------------------------------
    def setup_configman_namespace(self):
        n = Namespace()
        n.add_option(
            'alpha',
            default=3,
            doc='the first parameter',
            is_argument=True
        )
        n.add_option(
            'beta',
            default='the second',
            doc='the first parameter',
            short_form='b',
        )
        n.add_option(
            'gamma',
            default="1 2 3",
            from_string_converter=quote_stripping_list_of_ints,
            to_string_converter=partial(
                list_to_str,
                delimiter=' '
            ),
            secret=True,
        )
        n.add_option(
            'delta',
            default=False,
            from_string_converter=boolean_converter
        )
        return n

    #--------------------------------------------------------------------------
    def test_basic_01_defaults(self):
        option_definitions = self.setup_configman_namespace()
        cm = ConfigurationManager(
            definition_source=option_definitions,
            values_source_list=[command_line],
            argv_source=[],
            use_auto_help=False,
        )
        config = cm.get_config()

        expected = {
            "alpha": 3,
            "beta": "the second",
            "gamma": [1, 2, 3],
            "delta": False,
            "admin.print_conf": None,
            "admin.dump_conf": '',
            "admin.strict": False,
            "admin.expose_secrets": False
        }

        for k in config.keys_breadth_first():
            self.assertEqual(config[k], expected[k])

    #--------------------------------------------------------------------------
    def test_basic_02_change_all(self):
        option_definitions = self.setup_configman_namespace()
        cm = ConfigurationManager(
            definition_source=option_definitions,
            values_source_list=[command_line],
            argv_source=[
                "16",
                "-b=THE SECOND",
                '--gamma="88 99 111 333"',
                "--delta",
            ],
            use_auto_help=False,
        )
        config = cm.get_config()

        expected = {
            "alpha": 16,
            "beta": 'THE SECOND',
            "gamma": [88, 99, 111, 333],
            "delta": True,
            "admin.print_conf": None,
            "admin.dump_conf": '',
            "admin.strict": False,
            "admin.expose_secrets": False
        }

        for k in config.keys_breadth_first():
            self.assertEqual(config[k], expected[k])

    #--------------------------------------------------------------------------
    def test_basic_03_with_some_admin(self):
        option_definitions = self.setup_configman_namespace()
        cm = ConfigurationManager(
            definition_source=option_definitions,
            values_source_list=[command_line],
            argv_source=[
                "0",
                "--admin.expose_secrets",
                '--gamma="-1 -2 -3 -4 -5 -6"',
                "--delta",
                "--admin.strict",
            ],
            use_auto_help=False,
        )
        config = cm.get_config()

        expected = {
            "alpha": 0,
            "beta": 'the second',
            "gamma": [-1, -2, -3, -4, -5, -6],
            "delta": True,
            "admin.print_conf": None,
            "admin.dump_conf": '',
            "admin.strict": True,
            "admin.expose_secrets": True
        }

        for k in config.keys_breadth_first():
            self.assertEqual(config[k], expected[k])

    #--------------------------------------------------------------------------
    def test_basic_04_argparse_doesnt_dominate(self):
        option_definitions = self.setup_configman_namespace()
        other_value_source = {
            "gamma": [38, 28, 18, 8]
        }
        cm = ConfigurationManager(
            definition_source=option_definitions,
            values_source_list=[other_value_source, command_line],
            argv_source=[
                "0",
                "--admin.expose_secrets",
                "--delta",
                "--admin.strict",
            ],
            use_auto_help=False,
        )
        config = cm.get_config()

        expected = {
            "alpha": 0,
            "beta": 'the second',
            "gamma": [38, 28, 18, 8],
            "delta": True,
            "admin.print_conf": None,
            "admin.dump_conf": '',
            "admin.strict": True,
            "admin.expose_secrets": True
        }

        for k in config.keys_breadth_first():
            self.assertEqual(config[k], expected[k])

    #--------------------------------------------------------------------------
    def test_basic_05_argparse_overrides_when_appropriate(self):
        option_definitions = self.setup_configman_namespace()
        other_value_source = {
            "gamma": [38, 28, 18, 8]
        }
        cm = ConfigurationManager(
            definition_source=option_definitions,
            values_source_list=[other_value_source, command_line],
            argv_source=[
                "0",
                "--admin.expose_secrets",
                "--delta",
                "--admin.strict",
                '--gamma="8 18 28 38"',
            ],
            use_auto_help=False,
        )
        config = cm.get_config()

        expected = {
            "alpha": 0,
            "beta": 'the second',
            "gamma": [8, 18, 28, 38],
            "delta": True,
            "admin.print_conf": None,
            "admin.dump_conf": '',
            "admin.strict": True,
            "admin.expose_secrets": True
        }

        for k in config.keys_breadth_first():
            self.assertEqual(config[k], expected[k])

    #--------------------------------------------------------------------------
    def test_basic_06_argparse_class_expansion(self):
        option_definitions = self.setup_configman_namespace()
        other_value_source = {
            "gamma": [38, 28, 18, 8]
        }
        other_definition_source = Namespace()
        other_definition_source.add_option(
            "a_class",
            default="configman.tests.test_val_for_modules.Alpha",
            from_string_converter=class_converter
        )
        cm = ConfigurationManager(
            definition_source=[option_definitions, other_definition_source],
            values_source_list=[other_value_source, command_line],
            argv_source=[
                "0",
                "--admin.expose_secrets",
                "--delta",
                "--admin.strict",
                '--gamma="8 18 28 38"',
                '--a_class=configman.tests.test_val_for_modules.Beta'
            ],
            use_auto_help=False,
        )
        config = cm.get_config()

        expected = {
            "alpha": 0,
            "beta": 'the second',
            "gamma": [8, 18, 28, 38],
            "delta": True,
            "admin.print_conf": None,
            "admin.dump_conf": '',
            "admin.strict": True,
            "admin.expose_secrets": True,
            "a_class": class_converter(
                "configman.tests.test_val_for_modules.Beta"
            ),
            "b": 23
        }

        for k in config.keys_breadth_first():
            self.assertEqual(config[k], expected[k])

    #--------------------------------------------------------------------------
    def test_basic_07_argparse_multilevel_class_expansion(self):
        option_definitions = self.setup_configman_namespace()
        other_value_source = {
            "gamma": [38, 28, 18, 8]
        }
        other_definition_source = Namespace()
        other_definition_source.add_option(
            "a_class",
            default="configman.tests.test_val_for_modules.Alpha",
            from_string_converter=class_converter
        )
        cm = ConfigurationManager(
            definition_source=[option_definitions, other_definition_source],
            values_source_list=[other_value_source, command_line],
            argv_source=[
                "0",
                "--admin.expose_secrets",
                "--delta",
                '--gamma="8 18 28 38"',
                '--a_class=configman.tests.test_val_for_modules.Delta',
                '--messy=34'
            ],
            use_auto_help=False,
        )
        config = cm.get_config()

        expected = {
            "alpha": 0,
            "beta": 'the second',
            "gamma": [8, 18, 28, 38],
            "delta": True,
            "admin.print_conf": None,
            "admin.dump_conf": '',
            "admin.strict": False,
            "admin.expose_secrets": True,
            "a_class": class_converter(
                "configman.tests.test_val_for_modules.Delta"
            ),
            "messy": 34,
            "dd": class_converter(
                "configman.tests.test_val_for_modules.Beta"
            ),
            'b': 23,
        }

        for k in config.keys_breadth_first():
            self.assertEqual(config[k], expected[k])
