import opt.Option as opt

#==============================================================================
class Namespace(DotDict):
    #--------------------------------------------------------------------------
    def __init__(self, doc=''):
        super(Namespace, self).__init__()
        object.__setattr__(self, '_doc', doc)  # force into attributes

    #--------------------------------------------------------------------------
    def __setattr__(self, name, value):
        if type(value) in [int, float, str,
                           unicode, dt.datetime, dt.timedelta]:
            o = opt.Option(name=name, default=value, value=value)
        else:
            o = value
        if type(o) not in (opt.Option, Namespace):
            raise NotAnOptionError('Namespace can only hold instances of '
                                   'opt.Option or Namespace, an attempt to assign '
                                   'a %s has been detected' % type(value))
        self.__setitem__(name, o)

    #--------------------------------------------------------------------------
    def option(self,
               name,
               doc=None,
               default=None,
               from_string_converter=None,
               short_form=None,):
        an_option = opt.Option(name=name,
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
            self[prefix] = candidate = opt.Option()
            candidate.name = prefix
        candidate_type = type(candidate)
        if candidate_type == Namespace:
            candidate.set_value(name_parts[1], value, strict)
        else:
            candidate.set_value(value)


