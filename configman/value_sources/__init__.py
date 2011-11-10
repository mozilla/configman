import collections
import inspect
import sys

import exceptions as ex

# replace with dynamic discovery and loading
#import for_argparse
#import for_xml
import for_getopt
import for_json
import for_configparse
import for_configobj
import for_conf
import for_mapping

# please replace with dynamic discovery
for_handlers = [for_mapping,
                for_getopt,
                for_json,
                for_configobj if for_configobj.can_handle else for_configparse,
                for_conf
               ]


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
            raise ex.NoHandlerForType("no hander for %s is available" %
                                       str(candidate))
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
            try:
                type_handler_dispatch[a_type_supported].append(a_handler)
            except TypeError:
                # likely this is an instance of a handleable type that is not
                # hashable. Replace it with its base type and try to continue.
                type_handler_dispatch[type(a_type_supported)].append(a_handler)
    except AttributeError:
        # this module has no can_handle attribute, therefore cannot really
        # be a handler and an error should be raised
        raise ex.ModuleHandlesNothingException(
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
            except ex.ValueException, x:
                # a failure is not necessarily fatal, we need to try all of
                # the handlers.  It's only fatal when they've all failed
                error_history.append(str(x))
        if wrapped_source is None:
            errors = '; '.join(error_history)
            raise ex.AllHandlersFailedException(errors)
        wrapped_sources.append(wrapped_source)
    return wrapped_sources

def write(file_name_extension,
          option_iterator,
          output_stream=sys.stdout):
    try:
        file_extension_dispatch[file_name_extension](option_iterator,
                                                     output_stream)
    except KeyError:
        raise ex.UnknownFileExtensionException("%s isn't a registered file"
                                               " name extension" %
                                               file_name_extension)
