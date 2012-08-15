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

import collections
import inspect
import sys

from source_exceptions import (NoHandlerForType, ModuleHandlesNothingException,
                               AllHandlersFailedException,
                               UnknownFileExtensionException,
                               ValueException)

from ..config_file_future_proxy import ConfigFileFutureProxy

# replace with dynamic discovery and loading
#import for_argparse
#import for_xml
import for_getopt
import for_json
import for_conf
import for_mapping
import for_configparse

# please replace with dynamic discovery
for_handlers = [for_mapping,
                for_getopt,
                for_json,
                for_conf,
                for_configparse,
               ]
try:
    import for_configobj
    for_handlers.append(for_configobj)
except ImportError:
    # the module configobj is not present
    pass


# create a dispatch table of types/objects to modules.  Each type should have
# a list of modules that can handle that type.
class DispatchByType(collections.defaultdict):
    def get_handlers(self, candidate):
        handlers_set = set()
        for key, handler_list in self.iteritems():
            if (self._is_instance_of(candidate, key) or (candidate is key) or
                    (inspect.ismodule(key) and candidate is key)):
                handlers_set.update(handler_list)
        if not handlers_set:
            raise NoHandlerForType("no hander for %s is available" %
                                   candidate)
        return handlers_set

    @staticmethod
    def _is_instance_of(candidate, some_type):
        try:
            return isinstance(candidate, some_type)
        except TypeError:
            return False


type_handler_dispatch = DispatchByType(list)
for a_handler in for_handlers:
    try:
        for a_type_supported in a_handler.can_handle:
            type_handler_dispatch[a_type_supported].append(a_handler)
    except AttributeError:
        # this module has no can_handle attribute, therefore cannot really
        # be a handler and an error should be raised
        raise ModuleHandlesNothingException(
                                        "%s has no 'can_handle' attribute"
                                        % str(a_handler))

file_extension_dispatch = {}
for a_handler in for_handlers:
    try:
        file_extension_dispatch[a_handler.file_name_extension] = \
                                                    a_handler.ValueSource.write
    except AttributeError:
        # this handler doesn't have a 'file_name_extension' or ValueSource
        # therefore it is not eligibe for the write file dispatcher
        pass


def wrap(value_source_list, a_config_manager):
    wrapped_sources = []
    for a_source in value_source_list:
        if a_source is ConfigFileFutureProxy:
            a_source = a_config_manager._get_option('admin.conf').value
        handlers = type_handler_dispatch.get_handlers(a_source)
        wrapped_source = None
        error_history = []
        for a_handler in handlers:
            try:
                #print "the source:", a_source
                #print "the handler:", a_handler
                wrapped_source = a_handler.ValueSource(a_source,
                                                       a_config_manager)
                break
            except ValueException, x:
                # a failure is not necessarily fatal, we need to try all of
                # the handlers.  It's only fatal when they've all failed
                error_history.append(str(x))
        if wrapped_source is None:
            errors = '; '.join(error_history)
            raise AllHandlersFailedException(errors)
        wrapped_sources.append(wrapped_source)
    return wrapped_sources

def has_registration_for(config_file_type):
    return config_file_type in file_extension_dispatch


def write(config_file_type,
          option_iterator,
          opener):
    if isinstance(config_file_type, basestring):
        try:
            writer_fn = file_extension_dispatch[config_file_type]
        except KeyError:
            raise UnknownFileExtensionException("%s isn't a registered file"
                                                   " name extension" %
                                                   config_file_type)
        with opener() as output_stream:
            writer_fn(option_iterator, output_stream)
    else:
        # this is the case where we've not gotten a file extension, but a
        # for_handler module.  Use the module's ValueSource's write method
        with opener() as output_stream:
            config_file_type.ValueSource.write(option_iterator, output_stream)


def get_admin_options_from_command_line(config_manager):
    command_line_value_source = for_getopt.ValueSource(for_getopt.getopt,
                                                       config_manager)
    values = command_line_value_source.get_values(config_manager,
                                                  ignore_mismatches=True)
    return dict([(key, val) for key, val in values.iteritems()
                                          if key.startswith('admin.')])
