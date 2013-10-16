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
This sample app demonstrates how you can easily set custom to and from string
converters on options.

To test this app, run::

    python custom_formatter_app.py --admin.print_conf=ini

or::

    python custom_formatter_app.py --admin.print_conf=conf

Note how it converts the `option1` and `option2` to nice strings. Next, make
an ini file and edit it::

    python custom_formatter_app.py --admin.print_conf=ini > config.ini
    vi config.ini

Change one of the defaults for `option1` or `option2`. Then run::

    python custom_formatter_app.py --admin.conf=config.ini

Expect the values to change.
"""

from configman import RequiredConfig, Namespace


def decoder(string):
    return dict([e.strip() for e in x.split(':')] for x in string.split(','))


def encoder(value):
    return ', '.join('%s: %s' % (k.strip(), v.strip()) for (k, v) in value.items())


class CustomFormatterApp(RequiredConfig):

    app_name = 'custom_formatter_app'
    app_version = '0.1'
    app_description = __doc__

    # create the definitions for the parameters that are to come from
    # the command line or config file.
    required_config = Namespace()
    required_config.add_option(
        'option1',
        doc='Option 1',
        default='foo: FOO, bar: BAR',
        from_string_converter=decoder,
        to_string_converter=encoder
    )
    required_config.add_option(
        'option2',
        doc='Option 2',
        default={'baz': 'BAZ'},
        from_string_converter=decoder,
        to_string_converter=encoder
    )

    def __init__(self, config):
        self.config = config

    def main(self):
        print self.config.option1['foo']
        print self.config.option2['baz']


if __name__ == "__main__":
    import generic_app
    generic_app.main(CustomFormatterApp)
