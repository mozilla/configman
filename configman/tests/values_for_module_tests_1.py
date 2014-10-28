"""This is a test module for the configman.value_sources.for_modules
component. It is used only with the configman.tests.test_val_for_modules tests
"""
# WARNING - do not change the first four words of the doc string above.  Those
# words are used in a test in the file configman.tests.test_val_for_modules

import os
import collections

a = 18

b = [1, 2, 3]
b.append(3)

c = set(b)

d = {
    'a': a,
    'b': b,
    'c': c,
    'd': {
        1: 'one',
        2: 'two',
    }
}


def foo(a=None, b=None, c=None):
    return "%s%s%s" % (a, b, c)

from functools import partial
bar = partial(foo, a=a)

class Alpha(object):
    def __init__(self, a=None, b=None, c=None):
        self.a = a
        self.b = b
        self.c = c

    def __str__(self):
        return foo(self.a, self.b, self.c)



x = 23
y = 'this is private'

ignore_symbol_list = ['x', 'y', 'os', 'partial']