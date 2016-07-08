# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function

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
