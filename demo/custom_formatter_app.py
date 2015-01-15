#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

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
