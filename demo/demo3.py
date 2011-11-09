#!/usr/bin/env python

"""This sample application demonstrates the app class way to use configman."""
# there are two ways to invoke this app:
#    .../generic_app.py --_application=demo3.Demo3App
#    .../demo3.py
# this demo differs from demo2.py in the manner in which it works with
# configman. Rather than being a linear procedure, this app defines a app
# class with five features:
#   1) the app class derives from 'RequiredConfig'.  This instruments the class
#      with the mechanism for discovery of required configuration parameters.
#   2) closely aligned with point 1, this class defines a class level constant
#      called 'required_config' that sets up Namespaces and Options to define
#      the configuration requirements.
#   3) the app class defines three class level constants that identify the app.
#      'app_name', 'app_version', 'app_description'
#   4) the app class defines a constructor that accepts a DotDict derivative
#      of configuration values.
#   5) the app class defines a parameterless 'main' function that executes the
#      business logic of the application

import configman as cm
import configman.config_manager as config_man


# the following class embodies the business logic of the application.
class Demo3App(config_man.RequiredConfig):

    app_name = 'demo3_app'
    app_version = '0.1'
    app_description = __doc__

    # create the definitions for the parameters that are to come from
    # the command line or config file.
    required_config = cm.Namespace()
    required_config.add_option('text', 'Socorro Forever', 'the input value',
                               short_form='t')

    def __init__(self, config):
        self.text = config.text
        self.action_fn = Demo3App.action_converter(config.action)

    def main(self):
        self.action_fn(self.text)

    @staticmethod
    def echo_action(x):
        print x

    @staticmethod
    def backwards_action(x):
        print x[::-1]

    @staticmethod
    def upper_action(x):
        print x.upper()

    @staticmethod
    def action_converter(action):
        try:
            return getattr(Demo3App, "%s_action" % action)
        except AttributeError:
            raise Exception("'%s' is not a valid action" % action)

# normally, all the parameters are defined within the class, but
# the methods of this class itself are used in the configuration parameters.
# Python doesn't allow reference to class members until the class is entirely
# defined.  This tag along code injects the final config parameter after
# the class has been fully defined
list_of_actions = [x[:-7] for x in dir(Demo3App) if x.endswith('_action')]
doc_string = 'the action to take [%s]' % ', '.join(list_of_actions)
Demo3App.required_config.add_option('action', 'echo', doc_string,
                                short_form='a')

# if you'd rather invoke the app directly with its source file, this will
# allow it.
if __name__ == "__main__":
    import generic_app
    generic_app.main(Demo3App)
