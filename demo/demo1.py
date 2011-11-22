#!/usr/bin/env python

"""This sample application demonstrates the simlpest way to use configman."""
# this first demo shows how to use configman in the same manner that one would
# use other libraries like argparse.  We have a collection of functions that
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

# create the definitions for the parameters that are to come from
# the command line or config file.  First we create a container called a
# namespace for the configuration parameters.
definition_source = cm.Namespace()
# now we start adding options to the container. This first option
# defines on the command line '--text' and '-t' swiches.  For configuration
# files, this defines a top level entry of 'text' and assigns the value
# 'Socorro Forever' to it.
definition_source.add_option('text',
                             default='Socorro Forever',
                             doc='the text input value',
                             short_form='t')
# this second option definition defines the command line switches '--action'
# and '-a'
definition_source.add_option('action',
                             default='echo',
                             doc='the action to take [echo, backwards, upper]',
                             short_form='a')

# set up the manager with the option definitions along with the 'app_name' and
# 'app_description'.  They will both be used later to create  the output of the
# automatically created '--help' command line switch.
# By default, when assigning values to the options defined above, the
# ConfigurationManager will take, in turn: the default from the definition,
# any values loaded from a config file specified by the --admin.conf command
# line switch, values from the os environment and finally overrides from the
# commandline.
c = cm.ConfigurationManager(definition_source,
                            app_name='demo1',
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
