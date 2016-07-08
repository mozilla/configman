#!/usr/bin/env python
from __future__ import absolute_import, division, print_function
import configman
parser = configman.ArgumentParser()
parser.add_argument("square", help="display a square of a given number",
                    type=int)
args = parser.parse_args()
print(args.square**2)
