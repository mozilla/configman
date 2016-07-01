#!/usr/bin/env python
from __future__ import absolute_import, division, print_function
from configman import Namespace, ConfigurationManager

def backwards(x, capitalize=False):
    return x[::-1]

import re
vowels_regex = re.compile('[AEIOUY]', re.IGNORECASE)

def devowel(x):
    return vowels_regex.sub('', x)

def define_config():
    definition = Namespace()
    definition.add_option(
      name='devowel',
      default=False
    )
    return definition

if __name__ == '__main__':
    definition = define_config()
    config_manager = ConfigurationManager(definition)
    config = config_manager.get_config()
    output_string = ' '.join(config_manager.args)
    if config.devowel:
        output_string = devowel(output_string)
    print(backwards(output_string))
