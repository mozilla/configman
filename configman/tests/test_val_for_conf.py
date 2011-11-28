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
import StringIO as sio

from ..value_sources import for_conf
from ..option import Option


class TestCase(unittest.TestCase):

    def test_OptionsByConfFile_basics(self):
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
            # XXX (peterbe): commented out because I'm not sure if
            # OptionsByConfFile get_values() should depend on the configuration
            # manager it is given as first argument or not.
            #c = config_manager.ConfigurationManager([],
                                        #manager_controls=False,
                                        ##use_config_files=False,
                                        #use_auto_help=False,
                                        #argv_source=[])
            #self.assertEqual(o.get_values(c, True), {})
            #self.assertRaises(config_manager.NotAnOptionError,
            #                  o.get_values, c, False)
            #c.option_definitions.option('limit', default=0)
            #self.assertEqual(o.get_values(c, False), {'limit': '20'})
            #self.assertEqual(o.get_values(c, True), {'limit': '20'})
        finally:
            if os.path.isfile(tmp_filename):
                os.remove(tmp_filename)

    def test_write_flat_1(self):
        def iter_source():
            yield 'x', 'x', Option('x', default=13, doc='the x')
            yield 'y', 'y', Option('y', default=-1, doc='the y')
            yield 'z', 's', Option('z', default='fred', doc='the z')
        out = sio.StringIO()
        for_conf.ValueSource.write(iter_source, out)
        result = out.getvalue()
        expected = ("# name: x\n"
                    "# doc: the x\n"
                    "# converter: int\n"
                    "x=13\n\n"
                    "# name: y\n"
                    "# doc: the y\n"
                    "# converter: int\n"
                    "y=-1\n\n"
                    "# name: z\n"
                    "# doc: the z\n"
                    "# converter: str\n"
                    "z=fred\n\n"
                    )
        self.assertEqual(expected, result,
                         "exepected %s\nbut got\n%s" % (expected, result))
        #config.write_conf(output_stream=out)
