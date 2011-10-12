import dotdict
from option import Option


class Namespace(dotdict.DotDict):

    def __init__(self, doc=''):
        super(Namespace, self).__init__()
        object.__setattr__(self, '_doc', doc)  # force into attributes

    #--------------------------------------------------------------------------
    def __setattr__(self, name, value):
        if isinstance(value, (Option, Namespace)):
            # then they know what they're doing already
            o = value
        else:
            o = Option(name=name, default=value, value=value)
        self.__setitem__(name, o)

    #--------------------------------------------------------------------------
    def add_option(self, name,
                   default=None,
                   doc=None,
                   from_string_converter=None,
                   short_form=None):
        an_option = Option(name,
                           doc=doc,
                           default=default,
                           from_string_converter=from_string_converter,
                           short_form=short_form)
        self[name] = an_option

    #--------------------------------------------------------------------------
    def namespace(self, name, doc=''):
        self[name] = Namespace(doc=doc)

    #--------------------------------------------------------------------------
    def set_value(self, name, value, strict=True):

        name_parts = name.split('.', 1)
        prefix = name_parts[0]
        try:
            candidate = self[prefix]
        except KeyError:
            if strict:
                raise
            self[prefix] = candidate = Option(name)
        candidate_type = type(candidate)
        if candidate_type == Namespace:
            candidate.set_value(name_parts[1], value, strict)
        else:
            candidate.set_value(value)
