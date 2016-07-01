# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# this will be expanded in the future when additional command line libraries
# are supported

# at which point we want to make argparse the default, we will eliminate
# this line
from __future__ import absolute_import, division, print_function
import getopt as command_line

try:
    # keep this commented out until we want argparse as the default
    # import argparse as command_line
    from configman.def_sources.for_argparse import ArgumentParser
except ImportError:
    # argparse is not available, we can silently ignore this problem
    pass
