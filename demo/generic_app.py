#! /usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import getopt
import os.path
import inspect

import configman as cm
from configman import ConfigurationManager, Namespace
from configman import ConfigFileFutureProxy, environment, command_line
from configman.converters import class_converter


# This main function will load an application object, initialize it and then
# call its 'main' function
def main(app_object=None):
    if isinstance(app_object, basestring):
        app_object = class_converter(app_object)

    # the only config parameter is a special one that refers to a class or
    # module that defines an application.  In order to qualify, a class must
    # have a constructor that accepts a DotDict derivative as the sole
    # input parameter.  It must also have a 'main' function that accepts no
    # parameters.  For a module to be acceptable, it must have a main
    # function that accepts a DotDict derivative as its input parameter.
    app_definition = Namespace()
    app_definition.add_option('application',
                              doc='the fully qualified module or class of the '
                                  'application',
                              default=app_object,
                              from_string_converter=class_converter
                             )
    app_name = getattr(app_object, 'app_name', 'unknown')
    app_version = getattr(app_object, 'app_version', '0.0')
    app_description = getattr(app_object, 'app_description', 'no idea')


    # create an iterable collection of value sources
    # the order is important as these will supply values for the sources
    # defined in the_definition_source. The values will be overlain in turn.
    # First the os.environ values will be applied.  Then any values from an ini
    # file parsed by getopt.  Finally any values supplied on the command line
    # will be applied.
    value_sources = (ConfigFileFutureProxy,  # alias for allowing the user
                                             # to specify a config file on
                                             # the command line
                     environment,  # alias for os.environ
                     command_line) # alias for getopt

    # set up the manager with the definitions and values
    # it isn't necessary to provide the app_name because the
    # app_object passed in or loaded by the ConfigurationManager will alredy
    # have that information.
    config_manager = ConfigurationManager(app_definition,
                                          value_sources,
                                          app_name=app_name,
                                          app_version=app_version,
                                          app_description=app_description,
                                         )
    config = config_manager.get_config()

    app_object = config.admin.application

    if isinstance(app_object, type):
        # invocation of the app if the app_object was a class
        instance = app_object(config)
        instance.main()
    elif inspect.ismodule(app_object):
        # invocation of the app if the app_object was a module
        app_object.main(config)
    elif inspect.isfunction(app_object):
        # invocation of the app if the app_object was a function
        app_object(config)

if __name__ == '__main__':
    main()
