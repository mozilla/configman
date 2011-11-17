#!/usr/bin/env python

"""This sample application demonstrates the external way to use configman."""
# this varient of the first demo shows how to use configman with the
# definitions of the configuration parameters entirely in an external json
# file.  Just like the original demo1, we have a collection of functions that
# embody the business logic of the application.  We setup configuration
# parameters that will control the command line and config file forms.  Then
# we run the application.

import os
import sys
import getopt
import configman as cm


# the following three functions are the business logic of the application.
def echo(x):
    print x


def backwards(x):
    print x[::-1]


def upper(x):
    print x.upper()

# create an iterable collection of definition sources
# internally, this list will be appended to, so a tuple won't do.
# the definitions are in the json file listed below.
definition_source = 'demo1j.json'

# create an iterable collection of value sources
# the order is important as these will supply values for the sources defined
# in the_definition_source. The values will be overlain in turn.  Each of the
# configuration parameters will have the default values defined in the json
# file.  In the overlay process, first the os.environ values will be applied.
# Then any values from an ini file parsed by ConfigParse.  Finally any values
# supplied on the command line will be applied.  Notice that the json file
# doesn't participate as value source, its values already form the base
# values.  Adding it to this tuple wolud mean that the default get applied
# a second time and would override any values from the sources to the left in
# the tuple.
value_sources = ('demo1j.ini', os.environ, getopt)

# set up the manager with the definitions and values
# we set the sources for definition and value sources, and then define the
# 'app_name' and 'app_description'.  The former will be used to define the
# default basename for any configuration files that we may want to have the
# application write.  Both the former and the latter will be used to create
# the output of the automatically created '--help' command line switch.
c = cm.ConfigurationManager(definition_source,
                            value_sources,
                            app_name='demo1j',
                            app_description=__doc__)

# fetch the DOM-like instance that gives access to the configuration info
config = c.get_config()

# use the config
if config.action == 'echo':
    echo(config.text)
elif config.action == 'backwards':
    backwards(config.text)
elif config.action == 'upper':
    upper(config.text)
else:
    print >>sys.stderr, config.action, "is not a valid action"
