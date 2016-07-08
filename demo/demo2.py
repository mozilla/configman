#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""This sample application demonstrates a simple way to use configman."""
# this second demo shows how to use configman in the same manner that one would
# use other libraries like argparse.  We have a collection of functions that
# embody the business logic of the application.  We setup configuration
# parameters that will control the command line and config file forms.  Then
# we run the application.
# In this case, there is no need for a 'main' function.  The action done by the
# application is specified in configuration.  The last line of the file invokes
# the action.
from __future__ import absolute_import, division, print_function
from configman import ConfigurationManager, Namespace
from configman import environment, command_line
from configman.converters import class_converter


# the following three functions are the business logic of the application.
def echo(x):
    print(x)


def backwards(x):
    print(x[::-1])


def upper(x):
    print(x.upper())

action_dispatch = {'echo': echo,
                   'backwards': backwards,
                   'upper': upper
                  }


def action_converter(action):
    try:
        return action_dispatch[action]
    except KeyError:
        try:
            f = class_converter(action)
        except Exception:
            raise Exception("'%s' is not a valid action" % action)
        if f in action_dispatch.values():
            return f
        raise Exception("'%s' is not a valid action" % action)

# create the definitions for the parameters that are to come from
# the command line or config file.
definition_source = Namespace()
definition_source.add_option('text',
                                 'Socorro Forever',
                                 'the text input value',
                                 short_form='t')
# this application doesn't have a main function. This parameter
# definition sets up what function will be executed on invocation of
# of this script.
definition_source.add_option('action',
                                 'echo',
                                 'the action to take [%s]' %
                                    ', '.join(action_dispatch),
                                short_form='a',
                                from_string_converter=action_converter)

# this time, we're not going to accept the default list of value sources for
# the definitions created above.  'value_sources' is a sequence of objects that
# can be interpretted by the ConfigurationManager as a source of values for the
# options.  Each source will be queried in turn for values.  Values gleaned
# from sources on the left may be overridden by values from sources to the
# right.  In this example, we're hard coding the the demo2.ini file as a
# source of values.  The user will not be given the opporuntity to specify a
# config file of their own.  After reading the hard coded config file, the
# ConfigurationManager will apply values it got from the environment and then,
# finally, apply values that it gets from the command line.
value_sources = ('demo2.ini', environment, command_line)
# the value_sources sequence can contian any object that is a derivation of the
# type collections.Mapping, a module, or instances of any of the registered
# handlers. cm.environment is just an alias for os.environ.  cm.command_line is
# an alias for the 'getopt' module, a registerd handler.

# set up the manager with the definitions and values
c = ConfigurationManager(definition_source,
                         value_sources,
                         app_name='demo2',
                         app_description=__doc__)

# fetch the DotDict version of the values
config = c.get_config()

# use the config
config.action(config.text)
