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

from configman import option, dotdict, namespace
from configman.def_sources import for_mappings


class TestCase(unittest.TestCase):

    def test_setup_definitions_1(self):
        s = dotdict.DotDict()
        s.x = option.Option('x', 17, 'the x')
        s.n = {'name': 'n', 'doc': 'the n', 'default': 23}
        s.__forbidden__ = option.Option('__forbidden__',
                                        'no, you cannot',
                                         38)
        s.t = namespace.Namespace()
        s.t.add_option('kk', 999, 'the kk')
        s.w = 89
        s.z = None
        s.t2 = namespace.Namespace('empty namespace')
        d = dotdict.DotDict()
        for_mappings.setup_definitions(s, d)
        self.assertTrue(len(d) == 5)
        self.assertTrue(isinstance(d.x, option.Option))
        self.assertTrue(isinstance(d.n, option.Option))
        self.assertTrue(d.n.name == 'n')
        self.assertTrue(d.n.default == 23)
        self.assertTrue(d.n.doc == 'the n')
        self.assertTrue(isinstance(d.t, namespace.Namespace))
        self.assertTrue(d.t.kk.name == 'kk')
        self.assertTrue(d.t.kk.default == 999)
        self.assertTrue(d.t.kk.doc == 'the kk')
        self.assertTrue(isinstance(d.w, namespace.Option))
        self.assertTrue(d.w.name == 'w')
        self.assertTrue(d.w.default == 89)
        self.assertTrue(d.w.doc == 'w')
        self.assertTrue(isinstance(d.t2, namespace.Namespace))
        self.assertTrue(len(d.t2) == 0)
