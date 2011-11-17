#!/usr/bin/env python

"""This sample application demonstrates the simlpest way to use configman."""
# this first demo shows how to use configman in the same manner that one would
# use other libraries like argparse.  We have a collection of functions that
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

# create the definitions for the parameters that are to come from
# the command line or config file.  First we create a container called a
# namespace for the configuration parameters.
definition_source = cm.Namespace()
# now we start adding options to the container. This first option
# defines on the command line '--text' and '-t' swiches.  For configuration
# files, this defines a top level entry of 'text' and assigns the value
# 'Socorro Forever' to it.
definition_source.add_option('text',
                             'Socorro Forever',
                             'the text input value',
                             short_form='t')
# this second option definition defines the command line switches '--action'
# and '-a'
definition_source.add_option('action',
                             'echo',
                             'the action to take [echo, backwards, upper]',
                             short_form='a')

# create an iterable collection of value sources
# the order is important as these will supply values for the sources defined
# in the_definition_source. The values will be overlain in turn.  First the
# os.environ values will be applied.  Then any values from an ini file
# parsed by ConfigParse.  Finally any values supplied on the command line will
# be applied.
value_sources = ('demo1.ini', os.environ, getopt)

# set up the manager with the definitions and values
# we set the sources for definition and value sources, and then define the
# 'app_name' and 'app_description'.  The former will be used to define the
# default basename for any configuration files that we may want to have the
# application write.  Both the former and the latter will be used to create
# the output of the automatically created '--help' command line switch.
c = cm.ConfigurationManager(definition_source,
                            value_sources,
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
