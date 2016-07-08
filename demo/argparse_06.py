#!/usr/bin/env python
from __future__ import absolute_import, division, print_function
import configman
parser = configman.ArgumentParser()
parser.add_argument("--verbose", help="increase output verbosity",
                    action="store_true")
args = parser.parse_args()
if args.verbose:
   print("verbosity turned on")

