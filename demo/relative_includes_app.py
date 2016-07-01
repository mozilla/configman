#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
This sample app uses .ini files with `+include` directives
to prove that it's possible to use relative paths.
"""
from __future__ import absolute_import, division, print_function
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
        print("Option 1:",)
        print(self.config.option1)
        print("Option 2:",)
        print(self.config.option2)
        print("Option 3:",)
        print(self.config.option3)


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
        print("Now run:\n\tpython %s --admin.conf=%s\n" % (__file__, f))
    else:
        import generic_app
        generic_app.main(RelativeIncludesApp)
