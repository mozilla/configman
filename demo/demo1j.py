#!/usr/bin/env python

"""This sample application demonstrates the external way to use configman."""
# this varient of the first demo shows how to use configman with the
# definitions of the configuration parameters entirely in an external json
# file.  Just like the original demo1, we have a collection of functions that
# embody the business logic of the application.  We setup configuration
# parameters that will control the command line and config file forms.  Then
# we run the application.

import sys
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

# set up the manager with the option definitions along with the 'app_name' and
# 'app_description'.  They will both be used later to create  the output of the
# automatically created '--help' command line switch.
# By default, when assigning values to the options loaded from the json file,
# the ConfigurationManager will take, in turn: the default from the definition,
# any values loaded from a config file specified by the --admin.conf command
# line switch, values from the os environment and finally overrides from the
# commandline.
c = cm.ConfigurationManager(definition_source,
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
