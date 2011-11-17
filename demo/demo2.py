#!/usr/bin/env python

"""This sample application demonstrates a simple way to use configman."""
# this second demo shows how to use configman in the same manner that one would
# use other libraries like argparse.  We have a collection of functions that
# embody the business logic of the application.  We setup configuration
# parameters that will control the command line and config file forms.  Then
# we run the application.
# In this case, there is no need for a 'main' function.  The action done by the
# application is specified in configuration.  The last line of the file invokes
# the action.

import os
import getopt
import configman as cm
import configman.converters as conv


# the following three functions are the business logic of the application.
def echo(x):
    print x


def backwards(x):
    print x[::-1]


def upper(x):
    print x.upper()

action_dispatch = {'echo': echo,
                   'backwards': backwards,
                   'upper': upper
                  }


def action_converter(action):
    try:
        return action_dispatch[action]
    except KeyError:
        try:
            f = conv.class_converter(action)
        except Exception:
            raise Exception("'%s' is not a valid action" % action)
        if f in action_dispatch.values():
            return f
        raise Exception("'%s' is not a valid action" % action)

# create the definitions for the parameters that are to come from
# the command line or config file.
definition_source = cm.Namespace()
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

# create an iterable collection of value sources
# the order is important as these will supply values for the sources defined
# in the_definition_source. The values will be overlain in turn.  First the
# os.environ values will be applied.  Then any values from an ini file
# parsed by ConfigParse.  Finally any values supplied on the command line will
# be applied.
value_sources = ('demo2.ini', os.environ, getopt)

# set up the manager with the definitions and values
c = cm.ConfigurationManager(definition_source,
                            value_sources,
                            app_name='demo2',
                            app_description=__doc__)

# fetch the DotDict version of the values
config = c.get_config()

# use the config
config.action(config.text)
