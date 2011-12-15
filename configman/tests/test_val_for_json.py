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
import json
import tempfile
from cStringIO import StringIO


import configman.config_manager as config_manager
import configman.datetime_util as dtu
from configman.value_sources.for_json import ValueSource
#from ..value_sources.for_json import ValueSource


def bbb_minus_one(config, local_config, args):
    return config.bbb - 1


class TestCase(unittest.TestCase):

    def test_for_json_basics(self):
        tmp_filename = os.path.join(tempfile.gettempdir(), 'test.json')
        j = {'fred': 'wilma',
             'number': 23,
            }
        with open(tmp_filename, 'w') as f:
            json.dump(j, f)
        try:
            jvs = ValueSource(tmp_filename)
            vals = jvs.get_values(None, True)
            self.assertEqual(vals['fred'], 'wilma')
            self.assertEqual(vals['number'], 23)
        finally:
            if os.path.isfile(tmp_filename):
                os.remove(tmp_filename)

    def test_write_json(self):
        n = config_manager.Namespace(doc='top')
        n.add_option('aaa', '2011-05-04T15:10:00', 'the a',
          short_form='a',
          from_string_converter=dtu.datetime_from_ISO_string
        )

        def value_iter():
            yield 'aaa', 'aaa', n.aaa

        s = StringIO()
        ValueSource.write(value_iter, output_stream=s)
        received = s.getvalue()
        s.close()
        jrec = json.loads(received)

        expect_to_find = {
          "short_form": "a",
          "default": "2011-05-04T15:10:00",
          "doc": "the a",
          "value": "2011-05-04T15:10:00",
          "from_string_converter":
              "configman.datetime_util.datetime_from_ISO_string",
          "name": "aaa"
        }
        self.assertEqual(jrec['aaa'], expect_to_find)

    def test_json_round_trip(self):
        n = config_manager.Namespace(doc='top')
        n.add_option('aaa', '2011-05-04T15:10:00', 'the a',
          short_form='a',
          from_string_converter=dtu.datetime_from_ISO_string
        )
        expected_date = dtu.datetime_from_ISO_string('2011-05-04T15:10:00')
        n.add_option('bbb', '37', 'the a',
          short_form='a',
          from_string_converter=int
        )
        n.add_option('write', 'json')
        n.add_aggregation('bbb_minus_one', bbb_minus_one)
        #t = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False)
        name = '/tmp/test.json'
        import functools
        opener = functools.partial(open, name, 'w')
        c1 = config_manager.ConfigurationManager([n], [],
                            use_admin_controls=True,
                            use_auto_help=False,
                            app_name='/tmp/test',
                            app_version='0',
                            app_description='',
                            argv_source=[])
        c1.write_conf('json', opener)
        d1 = {'bbb': 88}
        d2 = {'bbb': '-99'}
        try:
            with open(name) as jfp:
                j = json.load(jfp)
            c2 = config_manager.ConfigurationManager((j,), (d1, d2),
                                        use_admin_controls=True,
                                        use_auto_help=False,
                                        argv_source=[])
            config = c2.get_config()
            self.assertEqual(config.aaa, expected_date)
            self.assertEqual(config.bbb, -99)
            self.assertEqual(config.bbb_minus_one, -100)

        finally:
            os.unlink(name)
