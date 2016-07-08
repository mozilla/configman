# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function

import collections
import os
import six

from configman.value_sources.source_exceptions import (
    NoHandlerForType,
    ModuleHandlesNothingException,
    AllHandlersFailedException,
    UnknownFileExtensionException,
    ValueException,
)
from configman.orderedset import OrderedSet
from configman.converters import str_to_python_object, to_str

from configman.config_file_future_proxy import ConfigFileFutureProxy
from configman.config_exceptions import CannotConvertError

# replace with dynamic discovery and loading
from configman.value_sources import for_argparse
#from configman.value_sources import or_xml
from configman.value_sources import for_getopt
from configman.value_sources import for_json
from configman.value_sources import for_conf
from configman.value_sources import for_mapping
from configman.value_sources import for_configobj
from configman.value_sources import for_modules

# please replace with dynamic discovery
for_handlers = [
    for_argparse,
    for_mapping,
    for_getopt,
    for_json,
    for_conf,
    for_configobj,
    for_modules,
]


#==============================================================================
# create a dispatch table of types/objects to modules.  Each type should have
# a list of modules that can handle that type.
class DispatchByType(collections.defaultdict):
    #--------------------------------------------------------------------------
    def get_handlers(self, candidate):
        handlers_set = OrderedSet()
        # find exact candidate matches first
        for key, handler_list in six.iteritems(self):
            if candidate is key:
                for a_handler in handler_list:
                    handlers_set.add(a_handler)
        # then find the "instance of" candidate matches
        for key, handler_list in six.iteritems(self):
            if self._is_instance_of(candidate, key):
                for a_handler in handler_list:
                    handlers_set.add(a_handler)
        if not handlers_set:
            raise NoHandlerForType("no hander for %s is available" %
                                   candidate)
        return handlers_set

    #--------------------------------------------------------------------------
    @staticmethod
    def _is_instance_of(candidate, some_type):
        try:
            return isinstance(candidate, some_type)
        except TypeError:
            return False


#------------------------------------------------------------------------------
type_handler_dispatch = DispatchByType(list)
for a_handler in for_handlers:
    try:
        for a_supported_value_source in a_handler.can_handle:
            try:
                type_handler_dispatch[a_supported_value_source].append(
                    a_handler
                )
            except TypeError:
                # likely this is an instance of a handleable type that is not
                # hashable. Replace it with its base type and try to continue.
                type_handler_dispatch[type(a_supported_value_source)].append(
                    a_handler
                )
    except AttributeError:
        # this module has no can_handle attribute, therefore cannot really
        # be a handler and an error should be raised
        raise ModuleHandlesNothingException(
            "%s has no 'can_handle' attribute" % str(a_handler)
        )

file_extension_dispatch = {}
for a_handler in for_handlers:
    try:
        file_extension_dispatch[a_handler.file_name_extension] = (
            a_handler.ValueSource.write
        )
    except AttributeError:
        # this handler doesn't have a 'file_name_extension' or ValueSource
        # therefore it is not eligible for the write file dispatcher
        pass


#------------------------------------------------------------------------------
def wrap_with_value_source_api(value_source_list, a_config_manager):
    wrapped_sources = []
    for a_source in value_source_list:
        if a_source is ConfigFileFutureProxy:
            a_source = a_config_manager._get_option('admin.conf').default
            # raise hell if the config file doesn't exist
            if isinstance(a_source, (six.binary_type, six.text_type)):
                a_source = to_str(a_source)
                config_file_doesnt_exist = not os.path.isfile(a_source)
                if config_file_doesnt_exist:
                    if a_config_manager.config_optional:
                        continue  # no file, it's optional, ignore it
                    raise IOError(a_source)  # no file, it's required, raise
                if a_source == a_config_manager.config_pathname:
                    # the config file has not been set to anything other than
                    # the default value. Force this into be the degenerate case
                    # and skip the wrapping process. We'll read the file later.
                    continue

        if a_source is None:
            # this means the source is degenerate - like the case where
            # the config file name has not been specified
            continue
        handlers = type_handler_dispatch.get_handlers(a_source)
        wrapped_source = None
        error_history = []
        for a_handler in handlers:
            try:
                wrapped_source = a_handler.ValueSource(a_source,
                                                       a_config_manager)
                break
            except (ValueException, CannotConvertError) as x:
                # a failure is not necessarily fatal, we need to try all of
                # the handlers.  It's only fatal when they've all failed
                exception_as_str = str(x)
                if exception_as_str:
                    error_history.append(str(x))
        if wrapped_source is None:
            if error_history:
                errors = '; '.join(error_history)
                raise AllHandlersFailedException(errors)
            else:
                raise NoHandlerForType(type(a_source))
        wrapped_sources.append(wrapped_source)
    return wrapped_sources


#------------------------------------------------------------------------------
def has_registration_for(config_file_type):
    return config_file_type in file_extension_dispatch


#------------------------------------------------------------------------------
def dispatch_request_to_write(
    config_file_type,
    options_mapping,
    opener
):
    if isinstance(config_file_type, (six.binary_type, six.text_type)):
        config_file_type = to_str(config_file_type)
        try:
            writer_fn = file_extension_dispatch[config_file_type]
        except KeyError:
            raise UnknownFileExtensionException(
                "%s isn't a registered file name extension" %
                config_file_type
            )
        with opener() as output_stream:
            writer_fn(options_mapping, output_stream=output_stream)
    else:
        # this is the case where we've not gotten a file extension, but a
        # for_handler module.  Use the module's ValueSource's write method
        with opener() as output_stream:
            config_file_type.ValueSource.write(
                options_mapping,
                output_stream=output_stream
            )


#------------------------------------------------------------------------------
def config_filename_from_commandline(config_manager):
    command_line_value_source = for_getopt.ValueSource(
        for_getopt.getopt,
        config_manager
    )
    values = command_line_value_source.get_values(
        config_manager,
        ignore_mismatches=True
    )
    try:
        config_file_name = values['admin.conf']
    except KeyError:
        return None

    if not os.path.isfile(config_file_name):
        # its not a file, is it a python path?
        try:
            config_object = str_to_python_object(config_file_name)
            return config_object
        except CannotConvertError:
            # ok give up, it's not a file nor a module path
            raise IOError(config_file_name)
    return config_file_name
