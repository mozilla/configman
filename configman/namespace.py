# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function

import six

from configman.dotdict import DotDict
from configman.option import Option, Aggregation


#==============================================================================
class Namespace(DotDict):

    #--------------------------------------------------------------------------
    def __init__(self, doc='', initializer=None):
        super(Namespace, self).__init__(initializer=initializer)
        object.__setattr__(self, '_doc', doc)  # force into attributes
        object.__setattr__(self, '_reference_value_from', False)

    #--------------------------------------------------------------------------
    def __setattr__(self, name, value):
        if isinstance(value, (Option, Namespace, Aggregation)):
            # then they know what they're doing already
            o = value
        else:
            o = Option(name=name, default=value, value=value)
        super(Namespace, self).__setattr__(name, o)

    #--------------------------------------------------------------------------
    def add_option(self, name, *args, **kwargs):
        """add an option to the namespace.   This can take two forms:
              'name' is a string representing the name of an option and the
              kwargs are its parameters, or 'name' is an instance of an Option
              object
        """
        if isinstance(name, Option):
            an_option = name
            name = an_option.name
        else:
            an_option = Option(name, *args, **kwargs)

        current_namespace = self
        name_parts = name.split('.')
        for a_path_component in name_parts[:-1]:
            if a_path_component not in current_namespace:
                current_namespace[a_path_component] = Namespace()
            current_namespace = current_namespace[a_path_component]
        an_option.name = name_parts[-1]

        setattr(current_namespace, an_option.name, an_option)
        return an_option

    #--------------------------------------------------------------------------
    def add_aggregation(self, name, function, secret=False):
        an_aggregation = Aggregation(name, function, secret)
        setattr(self, name, an_aggregation)
        return an_aggregation

    #--------------------------------------------------------------------------
    def namespace(self, name, doc=''):
        # ensure that all new sub-namespaces are of the same type as the parent
        a_namespace = self.__class__(doc=doc)
        setattr(self, name, a_namespace)
        return a_namespace

    #--------------------------------------------------------------------------
    def set_value(self, name, value, strict=True):
        name_parts = name.split('.', 1)
        prefix = name_parts[0]
        try:
            candidate = getattr(self, prefix)
        except KeyError:
            if strict:
                raise
            candidate = Option(name)
            setattr(self, prefix, candidate)
        candidate_type = type(candidate)
        if candidate_type == Namespace:
            candidate.set_value(name_parts[1], value, strict)
        else:
            candidate.set_value(value)

    #--------------------------------------------------------------------------
    def safe_copy(self, reference_value_from=None):
        new_namespace = Namespace()
        if self._reference_value_from:
            new_namespace.ref_value_namespace()
        for key, opt in six.iteritems(self):
            if isinstance(opt, Option):
                new_namespace[key] = opt.copy()
                # assign a new reference_value if one has not been defined
                if not new_namespace[key].reference_value_from:
                    new_namespace[key].reference_value_from = \
                        reference_value_from
            elif isinstance(opt, Aggregation):
                new_namespace.add_aggregation(
                    opt.name,
                    opt.function
                )
            elif isinstance(opt, Namespace):
                new_namespace[key] = opt.safe_copy()
        return new_namespace

    #--------------------------------------------------------------------------
    def ref_value_namespace(self):
        """tag this namespace as having been created by the referenced value
        from system for collecting common resources together."""
        # awkward syntax - because the base class DotDict hijacks the
        # the __setattr__ method, this is the only way to actually force a
        # value to become an attribute rather than member of the dict
        object.__setattr__(self, '_reference_value_from', True)
