import converters as conv

#==============================================================================
class Option(object):
    #--------------------------------------------------------------------------
    def __init__(self,
                 name=None,
                 doc=None,
                 default=None,
                 from_string_converter=None,
                 value=None,
                 short_form=None,
                 *args,
                 **kwargs):
        self.name = name
        self.short_form = short_form
        self.default = default
        self.doc = doc
        self.from_string_converter = from_string_converter
        if value == None:
            value = default
        self.set_value(value, from_string_converter)

    #--------------------------------------------------------------------------
    def deduce_converter(self, from_string_converter=str):
        if from_string_converter in [str, None] and self.default != None:
            type_of_default = type(self.default)
            try:
                self.from_string_converter = \
                    conv.from_string_converters[type_of_default]
            except KeyError:
                self.from_string_converter = str
        else:
            self.from_string_converter = from_string_converter

    #--------------------------------------------------------------------------
    def set_value(self, val, from_string_converter=None):
        if not self.from_string_converter:
            self.deduce_converter(from_string_converter)
        type_of_val = type(val)
        if type_of_val in [str, unicode]:
            try:
                self.value = self.from_string_converter(val)
            except TypeError:
                self.value = val
        else:
            self.value = val

