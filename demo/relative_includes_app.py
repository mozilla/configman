#!/usr/bin/env python
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
#    Gabi Thume, gabithume@gmail.com
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

"""
This sample app uses .ini files with `+include` directives
to prove that it's possible to use relative paths.
"""

from configman import RequiredConfig, Namespace


# the following class embodies the business logic of the application.
class RelativeIncludesApp(RequiredConfig):

    app_name = 'relative_includes_app'
    app_version = '0.1'
    app_description = __doc__

    # create the definitions for the parameters that are to come from
    # the command line or config file.
    required_config = Namespace()
    required_config.add_option(
        'option1', 'Option 1',
    )
    required_config.add_option(
        'option2', 'Option 2',
    )
    required_config.add_option(
        'option3', 'Option 3',
    )

    def __init__(self, config):
        self.config = config

    def main(self):
        print "Option 1:",
        print self.config.option1
        print "Option 2:",
        print self.config.option2
        print "Option 3:",
        print self.config.option3


def create_environment():
    import os
    f0 = '/tmp/relative_includes.ini'
    f1 = '/tmp/relative_includes_one.ini'
    f2 = '/tmp/relative_includes_two.ini'
    f3 = '/tmp/relative_includes_three.ini'
    if not os.path.isfile(f1):
        with open(f1, 'w') as f:
            f.write(
                'option1=Option One\n'
            )
    if not os.path.isfile(f2):
        with open(f2, 'w') as f:
            f.write(
                'option2=Option Two\n'
            )
    if not os.path.isfile(f3):
        with open(f3, 'w') as f:
            f.write(
                'option3=Option Three\n'
            )
    if not os.path.isfile(f0):
        with open(f0, 'w') as f:
            f.write(
                "application='%s'\n" % RelativeIncludesApp.__name__
            )
            f.write(
                "+include %s\n" % f1
            )
            f.write(
                "+include ./%s\n" % os.path.basename(f2)
            )
            f.write(
                "+include %s\n" % os.path.basename(f3)
            )
        return f0

if __name__ == "__main__":
    f = create_environment()
    if f:
        print "Now run:\n\tpython %s --admin.conf=%s\n" % (__file__, f)
    else:
        import generic_app
        generic_app.main(RelativeIncludesApp)
