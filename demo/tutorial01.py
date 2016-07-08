#!/usr/bin/env python
from __future__ import absolute_import, division, print_function

def backwards(x):
    return x[::-1]

if __name__ == '__main__':
    import sys
    output_string = ' '.join(sys.argv[1:])
    print(backwards(output_string))
