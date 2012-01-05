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
import yaml
import tempfile
from cStringIO import StringIO


import configman.config_manager as config_manager
import configman.datetime_util as dtu
from configman.value_sources.for_yaml import ValueSource


class TestCase(unittest.TestCase):

    def test_for_yaml_basics(self):
        tmp_filename = os.path.join(tempfile.gettempdir(), 'test.yaml')
        j = {'fred': 'wilma',
             'number': 23,
            }
        with open(tmp_filename, 'w') as f:
            yaml.dump(j, f)
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
        yrec = yaml.load(received)

        expect_to_find = { "aaa": '2011-05-04T15:10:00' }
        self.assertEqual(yrec, expect_to_find)

