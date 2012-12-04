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

from configman.value_sources.for_mapping import ValueSource
from configman.dotdict import DotDict


class TestCase(unittest.TestCase):

    def test_for_mapping(self):
        d = {'fred': 'wilma',
             'number': 23,
            }
        d_as_value_source = ValueSource(d)
        vals = d_as_value_source.get_values()
        self.assertEqual(vals.fred, 'wilma')
        self.assertEqual(vals.number, 23)
        self.assertFalse(d_as_value_source.always_ignore_mismatches)

    def test_for_dotdict(self):
        d = DotDict({'fred': 'wilma',
             'number': 23,
            })
        d.subdict = DotDict()
        d.subdict.fred = 'ethel'
        d_as_value_source = ValueSource(d)
        vals = d_as_value_source.get_values()
        self.assertEqual(vals.fred, 'wilma')
        self.assertEqual(vals.number, 23)
        self.assertEqual(vals.subdict.fred, 'ethel')
        self.assertFalse(d_as_value_source.always_ignore_mismatches)

    def test_for_environ(self):
        environ_as_value_source = ValueSource(os.environ)
        vals = environ_as_value_source.get_values()
        # what is guaranteed to be in the environment?
        self.assertTrue(vals.USER)
        self.assertTrue(environ_as_value_source.always_ignore_mismatches)

    def test_for_modules(self):
        os_as_value_source = ValueSource(os)
        vals = os_as_value_source.get_values()
        self.assertTrue(vals.path)
        self.assertTrue(vals.path.split)

