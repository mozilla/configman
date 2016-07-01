#!/usr/bin/env python
from __future__ import absolute_import, division, print_function
import configman
parser = configman.ArgumentParser()
parser.add_argument("echo")
args = parser.parse_args()
print(args.echo)
