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
import contextlib
from cStringIO import StringIO

from ..value_sources import for_conf
from ..option import Option
from configman import Namespace, ConfigurationManager
import configman.datetime_util as dtu

def stringIO_context_wrapper(a_stringIO_instance):
    @contextlib.contextmanager
    def stringIS_context_manager():
        yield a_stringIO_instance
    return stringIS_context_manager


class TestCase(unittest.TestCase):

    def _some_namespaces(self):
        """set up some namespaces"""
        n = Namespace(doc='top')
        n.add_option('aaa', '2011-05-04T15:10:00', 'the a',
          short_form='a',
          from_string_converter=dtu.datetime_from_ISO_string
        )
        n.c = Namespace(doc='c space')
        n.c.add_option('fred', 'stupid', 'husband from Flintstones')
        n.c.add_option('wilma', 'waspish', 'wife from Flintstones')
        n.c.e = Namespace(doc='e space')
        n.c.e.add_option('dwight',
                         default=97,
                         doc='my uncle')
        n.c.add_option('dwight',
                       default=98,
                       doc='your uncle')
        n.d = Namespace(doc='d space')
        n.d.add_option('fred', 'crabby', 'male neighbor from I Love Lucy')
        n.d.add_option('ethel', 'silly',
                       'female neighbor from I Love Lucy')
        n.x = Namespace(doc='x space')
        n.x.add_option('size', 100, 'how big in tons', short_form='s')
        n.x.add_option('password', 'secret', 'the password')
        return n

    def test_for_conf_basics(self):
        tmp_filename = os.path.join(tempfile.gettempdir(), 'test.conf')
        with open(tmp_filename, 'w') as f:
            f.write('# comment\n')
            f.write('limit=20\n')
            f.write('\n')
        try:
            o = for_conf.ValueSource(tmp_filename)
            assert o.values == {'limit': '20'}, o.values
            # in the case of this implementation of a ValueSource,
            # the two parameters to get_values are dummies.  That may
            # not be true for all ValueSource implementations
            self.assertEqual(o.get_values(1, False), {'limit': '20'})
            self.assertEqual(o.get_values(2, True), {'limit': '20'})
        finally:
            if os.path.isfile(tmp_filename):
                os.remove(tmp_filename)

    def donttest_for_conf_nested_namespaces(self):
        n = self._some_namespaces()
        cm = ConfigurationManager(n,
                                  values_source_list=[],
                                 )
        out = StringIO()
        cm.write_conf(for_conf, opener=stringIO_context_wrapper(out))
        received = out.getvalue()
        out.close()
        expected = """# name: aaa
# doc: the a
# converter: configman.datetime_util.datetime_from_ISO_string
aaa=2011-05-04T15:10:00

#-------------------------------------------------------------------------------
# c - c space

# name: c.dwight
# doc: your uncle
# converter: int
c.dwight=98

# name: c.fred
# doc: husband from Flintstones
# converter: str
c.fred=stupid

# name: c.wilma
# doc: wife from Flintstones
# converter: str
c.wilma=waspish

#-------------------------------------------------------------------------------
# e - e space

# name: c.e.dwight
# doc: my uncle
# converter: int
c.e.dwight=97

#-------------------------------------------------------------------------------
# d - d space

# name: d.ethel
# doc: female neighbor from I Love Lucy
# converter: str
d.ethel=silly

# name: d.fred
# doc: male neighbor from I Love Lucy
# converter: str
d.fred=crabby

#-------------------------------------------------------------------------------
# x - x space

# name: x.password
# doc: the password
# converter: str
x.password=secret

# name: x.size
# doc: how big in tons
# converter: int
x.size=100"""
        self.assertEqual(received.strip(), expected)

        strio = StringIO(expected)
        n.c.dwight.default = 3823
        n.c.e.dwight = 'fred'
        cm2 = ConfigurationManager(n,
                                   [stringIO_context_wrapper(strio)],
                                   use_admin_controls=False,
                                   use_auto_help=False)
        result = cm2.get_config()
        self.assertEqual(len(result), 4)
        self.assertEqual(sorted(result.keys()), ['aaa', 'c', 'd', 'x'])
        self.assertEqual(len(result.c), 4)
        self.assertEqual(sorted(result.c.keys()), ['dwight',
                                                   'e',
                                                   'fred',
                                                   'wilma'
                                                   ])
        self.assertEqual(result.c.dwight, 98)
        self.assertEqual(len(result.c.e), 1)
        self.assertEqual(result.c.e.dwight, '97')

    # this test will be used in the future
    def donttest_write_flat_with_migration(self):
        n = Namespace()
        n.add_option('x', default=13, doc='the x')
        n.add_option('y', default=-1, doc='the y')
        n.add_option('z', default='fred', doc='the z')
        n.namespace('o')
        n.o.add_option('x', default=13, doc='the x')
        c = ConfigurationManager(
          [n],
          use_admin_controls=True,
          use_auto_help=False,
          argv_source=[]
        )
        out = StringIO()
        c.write_conf(for_conf, opener=stringIO_context_wrapper(out))
        result = out.getvalue()
        expected = (
            "# name: x\n"
            "# doc: the x\n"
            "# converter: int\n"
            "# x='13'\n"
            "\n"
            "# name: y\n"
            "# doc: the y\n"
            "# converter: int\n"
            "y='-1'\n"
            "\n"
            "# name: z\n"
            "# doc: the z\n"
            "# converter: str\n"
            "z='fred'\n"
            "\n"
            "#-------------------------------------------------------------------------------\n"
            "# o - \n"
            "\n"
            "# name: o.x\n"
            "# doc: the x\n"
            "# converter: int\n"
            "# o.x='13'\n"
            "\n"
        )
        self.assertEqual(expected, result,
                         "exepected\n%s\nbut got\n%s" % (expected, result))
