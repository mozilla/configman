import sys
import ConfigParser

import exceptions


class NotEnoughInformationException(exceptions.ValueException):
    pass

file_name_extension = 'ini'

can_handle = (ConfigParser,
              ConfigParser.RawConfigParser,  # just the base class, subclasses
                                             # will be detected too
              basestring,
             )


class ValueSource(dict):

    def __init__(self, source,
                 the_config_manager=None,
                 top_level_section_name='top_level'):
        if source is ConfigParser:
            try:
                app = the_config_manager.get_option_by_name('_application')
                source = "%s%s" % (app.value.app_name, file_name_extension)
            except AttributeError:
                raise NotEnoughInformationException("Can't setup an ini file "
                                                    "without knowing the file "
                                                    "name")
        if isinstance(source, basestring):
            parser = ConfigParser.ConfigParser()
            parser.optionxform = str
            parser.read(source)
            self.configparser = parser
        elif isinstance(source, ConfigParser.RawConfigParser):
            self.configparser = source
        else:
            raise exceptions.CantHandleTypeException("don't know how to handle"
                                                     " %s." % str(source))
        self.top_level_section_name = top_level_section_name

    def get_values(self, config_manager, ignore_mismatches):
        """Return a nested dictionary representing the values in the ini file.
        In the case of this ValueSource implementation, both parameters are
        dummies."""
        options = self
        for a_section in self.configparser.sections():
            if a_section == self.top_level_section_name:
                prefix = ''
            else:
                prefix = "%s." % a_section
            for an_option in self.configparser.options(a_section):
                name = '%s%s' % (prefix, an_option)
                options[name] = self.configparser.get(a_section, an_option)

                # Commented out as a reminder of old code. I can't find any
                # reason why self.configparser.get() would return None
                # /peterbe sept 2011
                #if options[name] == None:
                #
        return options

    @staticmethod
    def write(option_iter, output_stream=sys.stdout):
        print >> output_stream, '[top_level]'
        for qkey, key, val in option_iter():
            if isinstance(val, Namespace):
                print >> output_stream, '[%s]' % key
                print >> output_stream, '# %s\n' % val._doc
            else:
                print >> output_stream, '# name:', qkey
                print >> output_stream, '# doc:', val.doc
                print >> output_stream, '# converter:', \
                   conv.classes_and_functions_to_str(val.from_string_converter)
                val_str = configman.ConfigurationManager.option_value_str(val)
                print >> output_stream, '%s=%s\n' % (key, val_str)

