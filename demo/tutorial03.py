#!/usr/bin/env python

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
      default=False,
      doc='Removes all vowels (including Y)',
      short_form='d'
    )
    definition.add_option(
      name='file',
      default='',
      doc='file name for the input text',
      short_form='f'
    )
    return definition

if __name__ == '__main__':
    definition = define_config()
    config_manager = ConfigurationManager(definition)
    config = config_manager.get_config()
    if config.file:
        with open(config.file) as f:
            output_string = f.read().strip()
    else:
        output_string = ' '.join(config_manager.args)
    if config.devowel:
        output_string = devowel(output_string)
    print backwards(output_string)
