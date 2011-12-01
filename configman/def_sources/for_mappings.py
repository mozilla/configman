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

import collections

from .. import converters
from .. import namespace
from .. import option


#------------------------------------------------------------------------------
def setup_definitions(source, destination):
    for key, val in source.items():
        if key.startswith('__'):
            continue  # ignore these
        if isinstance(val, option.Option):
            destination[key] = val
            if not val.name:
                val.name = key
            val.set_value(val.default)
        elif isinstance(val, option.Aggregation):
            destination[key] = val
        elif isinstance(val, collections.Mapping):
            if 'name' in val and 'default' in val:
                # this is an Option in the form of a dict, not a Namespace
                params = converters.str_dict_keys(val)
                destination[key] = option.Option(**params)
            elif 'function' in val:  # this is an Aggregation
                params = converters.str_dict_keys(val)
                destination[key] = option.Aggregation(**params)
            else:
                # this is a Namespace
                if key not in destination:
                    try:
                        destination[key] = namespace.Namespace(doc=val._doc)
                    except AttributeError:
                        destination[key] = namespace.Namespace()
                # recurse!
                setup_definitions(val, destination[key])
        elif isinstance(val, (int, long, float, str, unicode)):
            destination[key] = option.Option(name=key,
                                      doc=key,
                                      default=val)
