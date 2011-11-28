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
import collections

import configman.config_manager as config_manager
import configman.dotdict as dd
import configman.def_sources as defsrc


class TestCase(unittest.TestCase):

    def test_setup_definitions_1(self):
        d = dd.DotDict()

        def fake_mapping_func(source, destination):
            self.assertTrue(isinstance(source, collections.Mapping))
            self.assertEqual(d, destination)
        saved_original = defsrc.definition_dispatch.copy()
        try:
            defsrc.definition_dispatch[collections.Mapping] = fake_mapping_func
            s = {}
            defsrc.setup_definitions(s, d)
            s = dd.DotDict()
            defsrc.setup_definitions(s, d)
            s = config_manager.Namespace()
            defsrc.setup_definitions(s, d)
        finally:
            defsrc.definition_dispatch = saved_original

    def test_setup_definitions_2(self):
        d = dd.DotDict()

        def fake_mapping_func(source, destination):
            self.assertTrue(source is collections)
            self.assertEqual(d, destination)
        saved_original = defsrc.definition_dispatch.copy()
        try:
            defsrc.definition_dispatch[type(collections)] = fake_mapping_func
            s = collections
            defsrc.setup_definitions(s, d)
        finally:
            defsrc.definition_dispatch = saved_original

    def test_setup_definitions_3(self):
        d = dd.DotDict()

        def fake_mapping_func(source, destination):
            self.assertTrue(isinstance(source, str))
            self.assertEqual(d, destination)
        saved_original = defsrc.definition_dispatch.copy()
        try:
            defsrc.definition_dispatch[str] = fake_mapping_func
            s = "{}"
            defsrc.setup_definitions(s, d)
        finally:
            defsrc.definition_dispatch = saved_original
