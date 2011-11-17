#! /usr/bin/env python

import ConfigParser
import getopt
import os.path
import inspect

import configman as cm
import configman.converters as conv


# This main function will load an application object, initialize it and then
# call its 'main' function
def main(app_object=None):
    if isinstance(app_object, basestring):
        app_object = conv.class_converter(app_object)

    # the only config parameter is a special one that refers to a class or
    # module that defines an application.  In order to qualify, a class must
    # have a constructor that accepts a DotDict derivative as the sole
    # input parameter.  It must also have a 'main' function that accepts no
    # parameters.  For a module to be acceptable, it must have a main
    # function that accepts a DotDict derivative as its input parameter.
    app_definition = cm.Namespace()
    app_definition.add_option('_application',
                              doc='the fully qualified module or '
                                  'class of the application',
                              default=app_object,
                              from_string_converter=conv.class_converter
                             )

    # create an iterable collection of value sources
    # the order is important as these will supply values for the sources
    # defined in the_definition_source. The values will be overlain in turn.
    # First the os.environ values will be applied.  Then any values from an ini
    # file parsed by getopt.  Finally any values supplied on the command line
    # will be applied.
    value_sources = (ConfigParser,
                     os.environ,
                     getopt)

    # set up the manager with the definitions and values
    # it isn't necessary to provide the app_name because the
    # app_object passed in or loaded by the ConfigurationManager will alredy
    # have that information.
    config_manager = cm.ConfigurationManager(app_definition,
                                             value_sources,
                                             )
    config = config_manager.get_config()

    app_object = config._application

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
