import sys
try:
    import configobj
except ImportError:
    # no point carrying on
    file_name_extension = 'not in use'
    can_handle = ()
else:
    import ConfigParser

    file_name_extension = 'ini'

    can_handle = (configobj,
                  configobj.ConfigObj,
                  ConfigParser,
                  basestring,
                 )


import collections

from .. import namespace
from .. import converters as conv
from source_exceptions import (NotEnoughInformationException,
                               LoadingIniFileFailsException,
                               CantHandleTypeException)


class ValueSource(object):

    def __init__(self, source,
                 config_manager=None,
                 top_level_section_name='top_level'):
        self.delayed_parser_instantiation = False
        self.top_level_section_name = top_level_section_name
        if source is configobj or source is ConfigParser:
            try:
                app = config_manager.get_option_by_name('_application')
                source = "%s.%s" % (app.value.app_name,
                                    file_name_extension)
            except AttributeError:
                # we likely don't have the _application object set up yet.
                # we need to delay the instantiation of the ConfigParser
                # until later.
                if source is None:
                    raise NotEnoughInformationException(
                                "Can't setup an ini file without knowing "
                                "the file name")
                self.delayed_parser_instantiation = True
                return
        if (isinstance(source, basestring) and
            source.endswith(file_name_extension)):
            try:
                self.config_dict = self._create_parser(source)
            except Exception, x:
                raise LoadingIniFileFailsException("Cannot load ini: %s"
                                                   % str(x))

        elif isinstance(source, ConfigParser.RawConfigParser):
            self.config_dict = source
        else:
            raise CantHandleTypeException(
                        "ConfigParser doesn't know how to handle %s."
                        % str(source))

    @staticmethod
    def _create_parser(source):
        config_dict = configobj.ConfigObj(source)
        return config_dict

    def get_values(self, config_manager, ignore_mismatches):
        """Return a nested dictionary representing the values in the ini
        file. In the case of this ValueSource implementation, both
        parameters are dummies."""
        if self.delayed_parser_instantiation:
            try:
                app = config_manager.get_option_by_name('_application')
                source = "%s%s" % (app.value.app_name, file_name_extension)
                self.config_dict = self._create_parser(source)
                self.delayed_parser_instantiation = False
            except AttributeError:
                # we don't have enough information to get the ini file
                # yet.  we'll ignore the error for now
                return {}
        return self.config_dict

    @staticmethod
    def recursive_default_dict():
        return collections.defaultdict(ValueSource.recursive_default_dict)

    @staticmethod
    def write(option_iter, output_stream=sys.stdout):
        json_dict = ValueSource.recursive_default_dict()
        for qkey, key, val in option_iter():
            if isinstance(val, namespace.Namespace):
                continue
            d = json_dict
            for x in qkey.split('.')[1:]:
                d = d[x]
            try:
                # while the configobj has the ability to convert values
                # into string representations to save in a file, we
                # want to make sure that it uses a conversion that we
                # can deal with later.  For example, we allow values
                # to refer to class, function or modules.  configobj
                # won't convert those into a format that be reconstituted
                # from a string later.  So this code does the conversion
                # of known types into strings before we deligate writing
                # the new ini file to configobj.
                converter_fn = conv.to_string_converters[type(val.value)]
                value = converter_fn(val.value)
            except KeyError:
                value = val.value
            d[key] = value
        config_obj = configobj.ConfigObj()
        config_obj.update(json_dict)
        config_obj.write(output_stream)
