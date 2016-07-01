# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function

import unittest
import os
import contextlib


from configman.datetime_util import (
    datetime_from_ISO_string
)
from configman.namespace import Namespace
from configman.config_manager import ConfigurationManager
from configman.config_file_future_proxy import ConfigFileFutureProxy

from configman import command_line


#--------------------------------------------------------------------------
def stringIO_context_wrapper(a_stringIO_instance):
    @contextlib.contextmanager
    def stringIS_context_manager():
        yield a_stringIO_instance
    return stringIS_context_manager


#==========================================================================
class TestCase(unittest.TestCase):
    def _some_namespaces(self):
        """set up some namespaces"""
        n = Namespace(doc='top')
        n.add_option(
            'aaa',
            '2011-05-04T15:10:00',
            'the a',
            short_form='a',
            from_string_converter=datetime_from_ISO_string
        )
        n.c = Namespace(doc='c space')
        n.c.add_option(
            'dwight',
            'stupid, deadly',
            'husband from Flintstones'
        )
        n.c.add_option('wilma', "waspish's", 'wife from Flintstones')
        n.d = Namespace(doc='d space')
        n.d.add_option('dwight', "crabby", 'male neighbor from I Love Lucy')
        n.d.add_option(
            'ethel',
            'silly',
            'female neighbor from I Love Lucy'
        )
        n.x = Namespace(doc='x space')
        n.x.add_option('size', 100, 'how big in tons', short_form='s')
        n.x.add_option('password', 'secret "message"', 'the password')
        return n

    #----------------------------------------------------------------------
    def test_no_config_and_not_required(self):
        ConfigurationManager(
            definition_source=self._some_namespaces(),
            values_source_list=[ConfigFileFutureProxy],
            app_name='dwight',
            config_pathname='.',
            config_optional=True,
        )

    #----------------------------------------------------------------------
    def test_no_config_and_config_required(self):
        self.assertRaises(
            IOError,
            ConfigurationManager,
            definition_source=self._some_namespaces(),
            values_source_list=[ConfigFileFutureProxy],
            app_name='dwight',
            config_pathname='.',
            config_optional=False,
        )

    #----------------------------------------------------------------------
    def test_configdir_exists_but_no_config_and_not_required(self):
        temp_config_dir = '/tmp'
        ConfigurationManager(
            definition_source=self._some_namespaces(),
            values_source_list=[ConfigFileFutureProxy],
            app_name='dwight',
            config_pathname=temp_config_dir,
            config_optional=True,
        )

    #----------------------------------------------------------------------
    def test_configdir_exists_but_no_config_and_config_required(self):
        temp_config_dir = '/tmp'
        self.assertRaises(
            IOError,
            ConfigurationManager,
            definition_source=self._some_namespaces(),
            values_source_list=[ConfigFileFutureProxy],
            app_name='dwight',
            config_pathname=temp_config_dir,
            config_optional=False,
        )

    #----------------------------------------------------------------------
    def test_configdir_and_default_config_exists_and_config_not_required(self):
        temp_config_dir = '/tmp'
        with open('/tmp/dwight.ini', 'w') as f:
            f.write('')
        try:
            ConfigurationManager(
                definition_source=self._some_namespaces(),
                values_source_list=[ConfigFileFutureProxy],
                app_name='dwight',
                config_pathname=temp_config_dir,
                config_optional=True,
            )
        finally:
            os.unlink('/tmp/dwight.ini')

    #----------------------------------------------------------------------
    def test_configdir_exists_and_default_config_exists_and_config_required(
        self
    ):
        temp_config_dir = '/tmp'
        with open('/tmp/dwight.ini', 'w') as f:
            f.write('[x]\n    size=42')
        try:
            cm = ConfigurationManager(
                definition_source=self._some_namespaces(),
                values_source_list=[ConfigFileFutureProxy],
                app_name='dwight',
                config_pathname=temp_config_dir,
                config_optional=False,
            )
            self.assertEqual(cm.get_config()['x.size'], 42)
        finally:
            os.unlink('/tmp/dwight.ini')

    #----------------------------------------------------------------------
    def test_overridden_configfile_doesnt_exist(
        self
    ):
        temp_config_dir = '/tmp'
        with open('/tmp/dwight.ini', 'w') as f:
            f.write('')
        try:
            self.assertRaises(
                IOError,
                ConfigurationManager,
                definition_source=self._some_namespaces(),
                values_source_list=[
                    ConfigFileFutureProxy,
                    command_line
                ],
                argv_source=['--admin.conf=wilma.ini'],
                app_name='dwight',
                config_pathname=temp_config_dir,
                config_optional=False,
            )
        finally:
            os.unlink('/tmp/dwight.ini')

    def test_default_config_exists_config_required_overridden_correctly(
        self
    ):
        temp_config_dir = '/tmp'
        with open('/tmp/dwight.ini', 'w') as f:
            f.write('[x]\n    size=42')
        try:
            with open('/tmp/wilma.ini', 'w') as f:
                f.write('[x]\n    size=666')
            try:
                cm = ConfigurationManager(
                    definition_source=self._some_namespaces(),
                    values_source_list=[
                        ConfigFileFutureProxy,
                        command_line
                    ],
                    argv_source=['--admin.conf=/tmp/wilma.ini'],
                    app_name='dwight',
                    config_pathname=temp_config_dir,
                    config_optional=False,
                )
                self.assertEqual(cm.get_config()['x.size'], 666)
            finally:
                os.unlink('/tmp/wilma.ini')
        finally:
            os.unlink('/tmp/dwight.ini')

    def test_configdir_default_config_config_required_overridden_correctly_2(
        self
    ):
        temp_config_dir = '/tmp'
        with open('/tmp/dwight.ini', 'w') as f:
            f.write('')
        try:
            with open('./wilma.ini', 'w') as f:
                f.write('')
            try:
                ConfigurationManager(
                    definition_source=self._some_namespaces(),
                    values_source_list=[
                        ConfigFileFutureProxy,
                        command_line
                    ],
                    argv_source=['--admin.conf=./wilma.ini'],
                    app_name='dwight',
                    config_pathname=temp_config_dir,
                    config_optional=False,
                )
            finally:
                os.unlink('./wilma.ini')
        finally:
            os.unlink('/tmp/dwight.ini')

    def test_configdir_default_config_config_required_overridden_incorrectly_2(
        self
    ):
        temp_config_dir = '/tmp'
        with open('/tmp/dwight.ini', 'w') as f:
            f.write('')
        try:
            with open('/tmp/wilma.ini', 'w') as f:
                f.write('')
            try:
                self.assertRaises(
                    IOError,
                    ConfigurationManager,
                    definition_source=self._some_namespaces(),
                    values_source_list=[
                        ConfigFileFutureProxy,
                        command_line
                    ],
                    argv_source=['--admin.conf=wilma.ini'],
                    app_name='dwight',
                    config_pathname=temp_config_dir,
                    config_optional=False,
                )
            finally:
                os.unlink('/tmp/wilma.ini')
        finally:
            os.unlink('/tmp/dwight.ini')
