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
import tempfile
from cStringIO import StringIO
import contextlib

import configman.datetime_util as dtu
import configman.config_manager as config_manager

from configman import Namespace
from configman.config_exceptions import NotAnOptionError

try:
    #from ..value_sources.for_configobj import ValueSource
    from ..value_sources import for_configobj
except ImportError:
    # this module is optional.  If it doesn't exsit, that's ok, we'll just
    # igrore the tests
    pass
else:

    def stringIO_context_wrapper(a_stringIO_instance):
        @contextlib.contextmanager
        def stringIS_context_manager():
            yield a_stringIO_instance
        return stringIS_context_manager

    class TestCase(unittest.TestCase):
        def _some_namespaces(self):
            """set up some namespaces"""
            n = config_manager.Namespace(doc='top')
            n.add_option('aaa', '2011-05-04T15:10:00', 'the a',
              short_form='a',
              from_string_converter=dtu.datetime_from_ISO_string
            )
            n.c = config_manager.Namespace(doc='c space')
            n.c.add_option('fred', 'stupid, deadly', 'husband from Flintstones')
            n.c.add_option('wilma', "waspish's", 'wife from Flintstones')
            n.d = config_manager.Namespace(doc='d space')
            n.d.add_option('fred', "crabby", 'male neighbor from I Love Lucy')
            n.d.add_option('ethel', 'silly',
                           'female neighbor from I Love Lucy')
            n.x = config_manager.Namespace(doc='x space')
            n.x.add_option('size', 100, 'how big in tons', short_form='s')
            n.x.add_option('password', 'secret "message"', 'the password')
            return n

        def test_for_configobj_basics(self):
            """test basic use of for_configobj"""
            tmp_filename = os.path.join(tempfile.gettempdir(), 'test.ini')
            open(tmp_filename, 'w').write("""
# comment
name=Peter
awesome=
# comment
[othersection]
foo=bar  # other comment
        """)

            try:
                o = for_configobj.ValueSource(tmp_filename)
                r = {'othersection': {'foo': 'bar'},
                     'name': 'Peter',
                     'awesome': ''}
                assert o.get_values(None, None) == r
                # in the case of this implementation of a ValueSource,
                # the two parameters to get_values are dummies.  That may
                # not be true for all ValueSource implementations
                self.assertEqual(o.get_values(0, False), r)
                self.assertEqual(o.get_values(1, True), r)
                self.assertEqual(o.get_values(2, False), r)
                self.assertEqual(o.get_values(3, True), r)

            finally:
                if os.path.isfile(tmp_filename):
                    os.remove(tmp_filename)

        def test_for_configobj_basics_2(self):
            tmp_filename = os.path.join(tempfile.gettempdir(), 'test.ini')
            open(tmp_filename, 'w').write("""
# comment
name=Peter
awesome=
# comment
[othersection]
foo=bar  # other comment
        """)

            try:
                o = for_configobj.ValueSource(tmp_filename)
                c = config_manager.ConfigurationManager([],
                                            use_admin_controls=True,
                                            #use_config_files=False,
                                            use_auto_help=False,
                                            argv_source=[])

                self.assertEqual(o.get_values(c, False),
                                 {'othersection': {'foo': 'bar'},
                                 'name': 'Peter',
                                 'awesome': ''})
                self.assertEqual(o.get_values(c, True),
                                 {'othersection': {'foo': 'bar'},
                                 'name': 'Peter',
                                 'awesome': ''})
            finally:
                if os.path.isfile(tmp_filename):
                    os.remove(tmp_filename)

        # this test will be added back in the future
        def donttest_for_configobj_basics_3(self):
            n = Namespace()
            n.add_option("name", default='lars')
            n.add_option("awesome", default='lars')
            n.namespace('othersection')
            n.othersection.add_option('foo', default=23)
            tmp_filename = os.path.join(tempfile.gettempdir(), 'test.ini')
            open(tmp_filename, 'w').write("""
# comment
name=Peter
awesome=
# comment
[othersection]
bad_option=bar  # other comment
        """)

            try:

                self.assertRaises(
                    NotAnOptionError,
                    config_manager.ConfigurationManager,
                    [n],
                    [tmp_filename],
                )
            finally:
                if os.path.isfile(tmp_filename):
                    os.remove(tmp_filename)

        def test_write_ini(self):
            n = self._some_namespaces()
            c = config_manager.ConfigurationManager(
              [n],
              use_admin_controls=True,
              #use_config_files=False,
              use_auto_help=False,
              argv_source=[]
            )
            expected = \
"""# name: aaa
# doc: the a
# converter: configman.datetime_util.datetime_from_ISO_string
# Inspect the automatically written value below to make sure it is valid
#   as a Python object for its intended converter function.
aaa='2011-05-04T15:10:00'

[c]

    # name: fred
    # doc: husband from Flintstones
    # converter: str
    fred='stupid, deadly'

    # name: wilma
    # doc: wife from Flintstones
    # converter: str
    wilma=waspish's

[d]

    # name: ethel
    # doc: female neighbor from I Love Lucy
    # converter: str
    ethel=silly

    # name: fred
    # doc: male neighbor from I Love Lucy
    # converter: str
    fred=crabby

[x]

    # name: password
    # doc: the password
    # converter: str
    password=secret "message"

    # name: size
    # doc: how big in tons
    # converter: int
    size=100
"""
            out = StringIO()
            c.write_conf(for_configobj, opener=stringIO_context_wrapper(out))
            received = out.getvalue()
            out.close()
            self.assertEqual(expected.strip(), received.strip())

        def test_write_ini_with_migration(self):
            n = self._some_namespaces()
            n.namespace('o')
            n.o.add_option('password', 'secret "message"', 'the password')
            c = config_manager.ConfigurationManager(
              [n],
              [{'migration': True}],
              use_admin_controls=True,
              use_auto_help=False,
              argv_source=[]
            )
            expected = \
"""# name: aaa
# doc: the a
# converter: configman.datetime_util.datetime_from_ISO_string
# Inspect the automatically written value below to make sure it is valid
#   as a Python object for its intended converter function.
aaa='2011-05-04T15:10:00'

# name: password
# doc: the password
# converter: str
# The following value is common for more than one section below. Its value
#   may be set here for all or it can be overridden in its original section
password=secret "message"

[c]

    # name: fred
    # doc: husband from Flintstones
    # converter: str
    fred='stupid, deadly'

    # name: wilma
    # doc: wife from Flintstones
    # converter: str
    wilma=waspish's

[d]

    # name: ethel
    # doc: female neighbor from I Love Lucy
    # converter: str
    ethel=silly

    # name: fred
    # doc: male neighbor from I Love Lucy
    # converter: str
    fred=crabby

[o]

    # name: password
    # doc: the password
    # converter: str
    # The following value has been automatically commented out because
    #   the option is found in other sections and the defaults are the same.
    #   The common value can be found in the lowest level section. Uncomment
    #   to override that lower level value
    #password=secret "message"

[x]

    # name: password
    # doc: the password
    # converter: str
    # The following value has been automatically commented out because
    #   the option is found in other sections and the defaults are the same.
    #   The common value can be found in the lowest level section. Uncomment
    #   to override that lower level value
    #password=secret "message"

    # name: size
    # doc: how big in tons
    # converter: int
    size=100
"""
            out = StringIO()
            c.write_conf(for_configobj, opener=stringIO_context_wrapper(out))
            received = out.getvalue()
            out.close()
            self.assertEqual(expected.strip(), received.strip())

            values = c.get_config()
            self.assertEqual(values.x.size, 100)
            self.assertEqual(values.x.password, 'secret "message"')
            self.assertEqual(values.o.password, 'secret "message"')
            self.assertRaises(
                KeyError,
                lambda: values.d.password == 'secret "message"'
            )
            self.assertRaises(
                KeyError,
                lambda: values.password == 'secret "message"'
            )

            # try the round trip
            tmp_filename = os.path.join(tempfile.gettempdir(), 'test.ini')
            open(tmp_filename, 'w').write(received)
            try:
                c = config_manager.ConfigurationManager(
                  [n],
                  [tmp_filename],
                  use_admin_controls=True,
                  use_auto_help=False,
                  argv_source=[]
                )
                values = c.get_config()
                self.assertEqual(values.x.size, 100)
                self.assertEqual(values.x.password, 'secret "message"')
                self.assertEqual(values.o.password, 'secret "message"')
                self.assertRaises(
                    KeyError,
                    lambda: values.d.password == 'secret "message"'
                )
                self.assertRaises(
                    KeyError,
                    lambda: values.password == 'secret "message"'
                )
            finally:
                if os.path.isfile(tmp_filename):
                    os.remove(tmp_filename)

        def test_write_ini_with_migration_turned_off(self):
            n = self._some_namespaces()
            n.namespace('o')
            n.o.add_option('password', 'secret "message"', 'the password')
            c = config_manager.ConfigurationManager(
              [n],
              values_source_list=[{'admin.migration': False}],
              use_admin_controls=True,
              use_auto_help=False,
              argv_source=[]
            )
            expected = \
"""# name: aaa
# doc: the a
# converter: configman.datetime_util.datetime_from_ISO_string
# Inspect the automatically written value below to make sure it is valid
#   as a Python object for its intended converter function.
aaa='2011-05-04T15:10:00'

[c]

    # name: fred
    # doc: husband from Flintstones
    # converter: str
    fred='stupid, deadly'

    # name: wilma
    # doc: wife from Flintstones
    # converter: str
    wilma=waspish's

[d]

    # name: ethel
    # doc: female neighbor from I Love Lucy
    # converter: str
    ethel=silly

    # name: fred
    # doc: male neighbor from I Love Lucy
    # converter: str
    fred=crabby

[o]

    # name: password
    # doc: the password
    # converter: str
    password=secret "message"

[x]

    # name: password
    # doc: the password
    # converter: str
    password=secret "message"

    # name: size
    # doc: how big in tons
    # converter: int
    size=100
"""
            out = StringIO()
            c.write_conf(for_configobj, opener=stringIO_context_wrapper(out))
            received = out.getvalue()
            out.close()
            self.assertEqual(expected.strip(), received.strip())

        def test_configobj_includes_inside_sections(self):
            include_file_name = ''
            ini_file_name = ''
            try:
                with tempfile.NamedTemporaryFile(
                  'w',
                  suffix='ini',
                  delete=False
                ) as f:
                    include_file_name = f.name
                    contents = (
                      'dbhostname=myserver\n'
                      'dbname=some_database\n'
                      'dbuser=dwight\n'
                      'dbpassword=secrets\n'
                    )
                    f.write(contents)

                with tempfile.NamedTemporaryFile(
                  'w',
                  suffix='ini',
                  delete=False
                ) as f:
                    ini_file_name = f.name
                    contents = (
                      '[source]\n'
                      '+include %s\n'
                      '\n'
                      '[destination]\n'
                      '+include %s\n'
                      % (include_file_name, include_file_name)
                    )
                    f.write(contents)
                o = for_configobj.ValueSource(ini_file_name)
                expected_dict = {
                  'source': {
                    'dbhostname': 'myserver',
                    'dbname': 'some_database',
                    'dbuser': 'dwight',
                    'dbpassword': 'secrets'
                  },
                  'destination': {
                    'dbhostname': 'myserver',
                    'dbname': 'some_database',
                    'dbuser': 'dwight',
                    'dbpassword': 'secrets'
                  }
                }
                self.assertEqual(o.get_values(1, True), expected_dict)
            finally:
                if os.path.isfile(include_file_name):
                    os.remove(include_file_name)
                if os.path.isfile(ini_file_name):
                    os.remove(ini_file_name)

        def test_configobj_includes_outside_a_section(self):
            include_file_name = ''
            ini_file_name = ''
            try:
                with tempfile.NamedTemporaryFile(
                  'w',
                  suffix='ini',
                  delete=False
                ) as f:
                    include_file_name = f.name
                    contents = (
                      'dbhostname=myserver\n'
                      'dbname=some_database\n'
                      'dbuser=dwight\n'
                      'dbpassword=secrets\n'
                    )
                    f.write(contents)

                with tempfile.NamedTemporaryFile(
                  'w',
                  suffix='ini',
                  delete=False
                ) as f:
                    ini_file_name = f.name
                    contents = (
                      '+include %s\n'
                      '\n'
                      '[destination]\n'
                      'x = y\n'
                      'foo=bar'
                      % include_file_name
                    )
                    f.write(contents)
                o = for_configobj.ValueSource(ini_file_name)
                expected_dict = {
                  'dbhostname': 'myserver',
                  'dbname': 'some_database',
                  'dbuser': 'dwight',
                  'dbpassword': 'secrets',
                  'destination': {
                    'x': 'y',
                    'foo': 'bar'
                  }
                }
                self.assertEqual(o.get_values(1, True), expected_dict)
            finally:
                if os.path.isfile(include_file_name):
                    os.remove(include_file_name)
                if os.path.isfile(ini_file_name):
                    os.remove(ini_file_name)

        def test_configobj_relative_includes(self):
            include_file_name = ''
            ini_file_name = ''
            try:
                db_creds_dir = tempfile.mkdtemp()
                db_creds_basename = os.path.basename(db_creds_dir)
                ini_repo_dir = tempfile.mkdtemp()
                with tempfile.NamedTemporaryFile(
                  'w',
                  suffix='ini',
                  dir=db_creds_dir,
                  delete=False
                ) as f:
                    include_file_name = f.name
                    include_file_basename = os.path.basename(f.name)
                    contents = (
                      'dbhostname=myserver\n'
                      'dbname=some_database\n'
                      'dbuser=dwight\n'
                      'dbpassword=secrets\n'
                    )
                    f.write(contents)

                with tempfile.NamedTemporaryFile(
                  'w',
                  suffix='ini',
                  dir=ini_repo_dir,
                  delete=False
                ) as f:
                    ini_file_name = f.name
                    contents = (
                      '+include ../%s/%s\n'
                      '\n'
                      '[destination]\n'
                      '+include ../%s/%s\n'
                      % (db_creds_basename, include_file_basename,
                         db_creds_basename, include_file_basename)
                    )
                    f.write(contents)
                o = for_configobj.ValueSource(ini_file_name)
                expected_dict = {
                  'dbhostname': 'myserver',
                  'dbname': 'some_database',
                  'dbuser': 'dwight',
                  'dbpassword': 'secrets',
                  'destination': {
                    'dbhostname': 'myserver',
                    'dbname': 'some_database',
                    'dbuser': 'dwight',
                    'dbpassword': 'secrets',
                  }
                }
                self.assertEqual(o.get_values(1, True), expected_dict)
            finally:
                if os.path.isfile(include_file_name):
                    os.remove(include_file_name)
                if os.path.isfile(ini_file_name):
                    os.remove(ini_file_name)
                if os.path.isdir(db_creds_dir):
                    os.rmdir(db_creds_dir)
                if os.path.isdir(ini_repo_dir):
                    os.rmdir(ini_repo_dir)

        def test_configobj_relative_paths(self):
            include_file_name = ''
            ini_file_name = ''
            try:
                db_creds_dir = tempfile.mkdtemp()
                ini_repo_dir = tempfile.mkdtemp()
                with tempfile.NamedTemporaryFile(
                  'w',
                  suffix='ini',
                  dir=db_creds_dir,
                  delete=False
                ) as f:
                    include_file_name = f.name
                    include_file_basename = os.path.basename(f.name)
                    contents = (
                      'dbhostname=myserver\n'
                      'dbname=some_database\n'
                      'dbuser=dwight\n'
                      'dbpassword=secrets\n'
                    )
                    f.write(contents)
                with tempfile.NamedTemporaryFile(
                  'w',
                  suffix='ini',
                  dir=db_creds_dir,
                  delete=False
                ) as f:
                    ini_file_name = f.name
                    contents = (
                      '+include %s\n'
                      % include_file_basename
                    )
                    f.write(contents)
                o = for_configobj.ValueSource(ini_file_name)
                expected_dict = {
                  'dbhostname': 'myserver',
                  'dbname': 'some_database',
                  'dbuser': 'dwight',
                  'dbpassword': 'secrets',
                }
                self.assertEqual(o.get_values(1, True), expected_dict)
            finally:
                if os.path.isfile(include_file_name):
                    os.remove(include_file_name)
                if os.path.isfile(ini_file_name):
                    os.remove(ini_file_name)
                if os.path.isdir(db_creds_dir):
                    os.rmdir(db_creds_dir)
                if os.path.isdir(ini_repo_dir):
                    os.rmdir(ini_repo_dir)
