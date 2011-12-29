#! /usr/bin/env python
# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is configman
#
# The Initial Developer of the Original Code is
# Mozilla Foundation
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#    K Lars Lohn, lars@mozilla.com
#    Peter Bengtsson, peterbe@mozilla.com
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

import ConfigParser
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
    app_definition.admin = admin = Namespace()
    admin.add_option('application',
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
