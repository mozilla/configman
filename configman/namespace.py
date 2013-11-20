# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is configman
#
# The Initial Developer of the Original Code is
# Mozilla Foundation
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#    K Lars Lohn, lars@mozilla.com
#    Peter Bengtsson, peterbe@mozilla.com
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

import dotdict
from option import Option, Aggregation


class Namespace(dotdict.DotDict):

    def __init__(self, doc=''):
        super(Namespace, self).__init__()
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

    #--------------------------------------------------------------------------
    def add_aggregation(self, name, function):
        an_aggregation = Aggregation(name, function)
        setattr(self, name, an_aggregation)

    #--------------------------------------------------------------------------
    def namespace(self, name, doc=''):
        setattr(self, name, Namespace(doc=doc))

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
        for key, opt in self.iteritems():
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

