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

from configman.memoize import memoize

#==============================================================================
class TestCase(unittest.TestCase):

    #--------------------------------------------------------------------------
    def test_memoize_function(self):

        @memoize()
        def foo(a, b, c):
            foo.counter += 1
            return (a, b, c)
        foo.counter = 0

        for i in range(5):
            # repeatable and exactly 10 function calls
            results = [foo(x, x, x) for x in range(10)]
            expected = [(x, x, x) for x in range(10)]
            self.assertEqual(results, expected)
            self.assertEqual(foo.counter, 10)

    #--------------------------------------------------------------------------
    def test_memoize_instance_method(self):

        class A(object):
            def __init__(self):
                self.counter = 0
            @memoize()
            def foo(self, a, b, c):
                self.counter += 1
                return (a, b, c)

        a = A()
        for i in range(5):
            # repeatable and exactly 10 function calls
            results = [a.foo(x, x, x) for x in range(10)]
            expected = [(x, x, x) for x in range(10)]
            self.assertEqual(results, expected)
            self.assertEqual(a.counter, 10)

        b = A()
        # repeatable and exactly 10 function calls
        results = [b.foo(x, x, x) for x in range(10)]
        expected = [(x, x, x) for x in range(10)]
        self.assertEqual(results, expected)
        self.assertEqual(b.counter, 10)

    #--------------------------------------------------------------------------
    def test_memoize_class_method(self):

        class A(object):
            counter = 0

            @classmethod
            @memoize()
            def foo(klass, a, b, c):
                klass.counter += 1
                return (a, b, c)

        for i in range(5):
            # repeatable and exactly 10 function calls
            results = [A.foo(x, x, x) for x in range(10)]
            expected = [(x, x, x) for x in range(10)]
            self.assertEqual(results, expected)
            self.assertEqual(A.counter, 10)

    #--------------------------------------------------------------------------
    def test_memoize_static_method(self):

        class A(object):
            counter = 0

            @staticmethod
            @memoize()
            def foo(a, b, c):
                A.counter += 1
                return (a, b, c)

        for i in range(5):
            # repeatable and exactly 10 function calls
            results = [A.foo(x, x, x) for x in range(10)]
            expected = [(x, x, x) for x in range(10)]
            self.assertEqual(results, expected)
            self.assertEqual(A.counter, 10)





