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
import os
import contextlib


import configman.datetime_util as dtu
import configman.config_manager as config_manager

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
        n = config_manager.Namespace(doc='top')
        n.add_option(
            'aaa',
            '2011-05-04T15:10:00',
            'the a',
            short_form='a',
            from_string_converter=dtu.datetime_from_ISO_string
        )
        n.c = config_manager.Namespace(doc='c space')
        n.c.add_option(
            'dwight',
            'stupid, deadly',
            'husband from Flintstones'
        )
        n.c.add_option('wilma', "waspish's", 'wife from Flintstones')
        n.d = config_manager.Namespace(doc='d space')
        n.d.add_option('dwight', "crabby", 'male neighbor from I Love Lucy')
        n.d.add_option(
            'ethel',
            'silly',
            'female neighbor from I Love Lucy'
        )
        n.x = config_manager.Namespace(doc='x space')
        n.x.add_option('size', 100, 'how big in tons', short_form='s')
        n.x.add_option('password', 'secret "message"', 'the password')
        return n

    #----------------------------------------------------------------------
    def test_no_config_and_not_required(self):
        config_manager.ConfigurationManager(
            definition_source=self._some_namespaces(),
            values_source_list=[config_manager.ConfigFileFutureProxy],
            app_name='dwight',
            config_pathname='.',
            config_optional=True,
        )

    #----------------------------------------------------------------------
    def test_no_config_and_config_required(self):
        self.assertRaises(
            IOError,
            config_manager.ConfigurationManager,
            definition_source=self._some_namespaces(),
            values_source_list=[config_manager.ConfigFileFutureProxy],
            app_name='dwight',
            config_pathname='.',
            config_optional=False,
        )

    #----------------------------------------------------------------------
    def test_configdir_exists_but_no_config_and_not_required(self):
        temp_config_dir = '/tmp'
        config_manager.ConfigurationManager(
            definition_source=self._some_namespaces(),
            values_source_list=[config_manager.ConfigFileFutureProxy],
            app_name='dwight',
            config_pathname=temp_config_dir,
            config_optional=True,
        )

    #----------------------------------------------------------------------
    def test_configdir_exists_but_no_config_and_config_required(self):
        temp_config_dir = '/tmp'
        self.assertRaises(
            IOError,
            config_manager.ConfigurationManager,
            definition_source=self._some_namespaces(),
            values_source_list=[config_manager.ConfigFileFutureProxy],
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
            config_manager.ConfigurationManager(
                definition_source=self._some_namespaces(),
                values_source_list=[config_manager.ConfigFileFutureProxy],
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
            cm = config_manager.ConfigurationManager(
                definition_source=self._some_namespaces(),
                values_source_list=[config_manager.ConfigFileFutureProxy],
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
                config_manager.ConfigurationManager,
                definition_source=self._some_namespaces(),
                values_source_list=[
                    config_manager.ConfigFileFutureProxy,
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
                cm = config_manager.ConfigurationManager(
                    definition_source=self._some_namespaces(),
                    values_source_list=[
                        config_manager.ConfigFileFutureProxy,
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
                config_manager.ConfigurationManager(
                    definition_source=self._some_namespaces(),
                    values_source_list=[
                        config_manager.ConfigFileFutureProxy,
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
                    config_manager.ConfigurationManager,
                    definition_source=self._some_namespaces(),
                    values_source_list=[
                        config_manager.ConfigFileFutureProxy,
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
