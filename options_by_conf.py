class OptionsByConfFile(object):

    def __init__(self, filename, opener=open):
        self.values = {}
        with opener(filename) as f:
            previous_key = None
            for line in f:
                if line.strip().startswith('#') or not line.strip():
                    continue
                if line[0] in ' \t' and previous_key:
                    line = line[1:]
                    self.values[previous_key] = '%s%s' % \
                                        (self.values[previous_key],
                                         line.rstrip())
                    continue
                try:
                    key, value = line.split("=", 1)
                    self.values[key.strip()] = value.strip()
                    previous_key = key
                except ValueError:
                    self.values[line] = ''

    def get_values(self, config_manager, ignore_mismatches):
        return self.values
