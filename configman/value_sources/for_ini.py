import ConfigParser


class IniValueSource(object):

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
        options = {}
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
                #    options[name] = True

        return options
