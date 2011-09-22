import ConfigParser


class OptionsByIniFile(object):

    def __init__(self, source,
                 top_level_section_name='top_level'):
        if isinstance(source, basestring):
            parser = ConfigParser.RawConfigParser()
            parser.optionxform = str
            parser.read(source)
            self.configparser = parser
        else:  # a real config parser was loaded
            self.configparser = source
        self.top_level_section_name = top_level_section_name

    def get_values(self, config_manager, ignore_mismatches):
        sections_list = self.configparser.sections()
        options = {}
        for a_section in sections_list:
            if a_section == self.top_level_section_name:
                prefix = ''
            else:
                prefix = "%s." % a_section
            for an_option in self.configparser.options(a_section):
                name = '%s%s' % (prefix, an_option)
                options[name] = self.configparser.get(a_section, an_option)

                # FIXME: why these two lines? How can they ever happen??
                if options[name] == None:
                    options[name] = True

        return options
