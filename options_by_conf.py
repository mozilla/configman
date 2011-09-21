#==============================================================================
class OptionsByConfFile(object):
    #--------------------------------------------------------------------------
    def __init__(self, filename, open=open):
        self.filename = filename
        self.values = {}
        try:
            with open(self.filename) as f:
                previous_key = None
                for l in f:
                    if l[0] in ' \t' and previous_key:
                        l = l[1:]
                        self.values[previous_key] = '%s%s' % \
                                            (self.values[previous_key], l)
                        continue
                    l = l.strip()
                    if not l:
                        continue
                    if l[0] in '#':
                        continue
                    try:
                        parts = l.split("=", 1)
                        key, value = parts
                        self.values[key.strip()] = value.strip()
                        previous_key = key
                    except ValueError:
                        self.values[parts[0]] = ''
        except IOError:
            pass

    #--------------------------------------------------------------------------
    def get_values(self, config_manager, ignore_mismatches):
        return self.values


