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
        an_option = Option(name, *args, **kwargs)
        setattr(self, name, an_option)

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
    def safe_copy(self):
        new_namespace = Namespace()
        for key, opt in self.iteritems():
            if isinstance(opt, Option):
                new_namespace[key] = opt.copy()
            elif isinstance(opt, Aggregation):
                new_namespace.add_aggregation(
                    opt.name,
                    opt.function
                )
            elif isinstance(opt, Namespace):
                new_namespace[key] = opt.safe_copy()
        return new_namespace
