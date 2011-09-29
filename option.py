import converters as conv
from exceptions import CannotConvertError


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
        if from_string_converter is None:
            if default is not None:
                # take a qualified guess from the default value
                from_string_converter = self._deduce_converter(default)
        if isinstance(from_string_converter, basestring):
            from_string_converter = conv.class_converter(from_string_converter)
        self.from_string_converter = from_string_converter
        if value is None:
            value = default
        self.set_value(value)

    #--------------------------------------------------------------------------
    def _deduce_converter(self, default):
        default_type = type(default)
        return conv.from_string_converters.get(default_type, default_type)

    #--------------------------------------------------------------------------
    def set_value(self, val):
        if isinstance(val, basestring):
            try:
                self.value = self.from_string_converter(val)
            except TypeError:
                self.value = val
            except ValueError:
                raise CannotConvertError(val)
        else:
            self.value = val
