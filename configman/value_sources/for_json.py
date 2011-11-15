import json
import collections
import sys

from .. import converters as conv
from ..namespace import Namespace

from source_exceptions import (ValueException, NotEnoughInformationException,
                               NoHandlerForType)

can_handle = (basestring,
              json
             )

file_name_extension = 'json'


class LoadingJsonFileFailsException(ValueException):
    pass


class ValueSource(object):

    def __init__(self, source, the_config_manager=None):
        self.values = None
        if source is json:
            try:
                app = the_config_manager.get_option_by_name('_application')
                source = "%s.%s" % (app.value.app_name, file_name_extension)
            except (AttributeError, KeyError):
                raise NotEnoughInformationException("Can't setup an json "
                                                       "file without knowing "
                                                       "the file name")
        if (isinstance(source, basestring) and
           source.endswith(file_name_extension)):
            try:
                with open(source) as fp:
                    self.values = json.load(fp)
            except Exception, x:
                # FIXME: this magically merges two otherwise interesting
                # exceptions:
                #  IOError and ValueError.
                # If you get a LoadingJsonFileFailsException exception you
                # won't know for certain what caused in. File missing or file
                # badly formatted.
                raise LoadingJsonFileFailsException("Cannot load json: %s" %
                                                    str(x))
        else:
            raise NoHandlerForType("json can't handle: %s" %
                                      str(source))

    def get_values(self, config_manager, ignore_mismatches):
        return self.values

    @staticmethod
    def recursive_default_dict():
        return collections.defaultdict(ValueSource.recursive_default_dict)

    @staticmethod
    def write(option_iter, output_stream=sys.stdout):
        json_dict = ValueSource.recursive_default_dict()
        for qkey, key, val in option_iter():
            if isinstance(val, Namespace):
                continue
            d = json_dict
            for x in qkey.split('.'):
                d = d[x]
            for okey, oval in val.__dict__.iteritems():
                try:
                    d[okey] = conv.to_string_converters[type(oval)](oval)
                except KeyError:
                    d[okey] = str(oval)
        json.dump(json_dict, output_stream)
