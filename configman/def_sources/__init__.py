import collections

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

# TODO: This is a temporary dispatch mechanism.  This whole system
# is to be changed to automatic discovery of the for_* modules

import for_mappings
import for_modules
#import for_list
import for_json
#import for_class

definition_dispatch = {
  collections.Mapping: for_mappings.setup_definitions,
  type(for_modules): for_modules.setup_definitions,
  #list: for_list.setup_definitions,
  str: for_json.setup_definitions,
  unicode: for_json.setup_definitions,
  #type: for_class.setup_definitions,
}


class UnknownDefinitionTypeException(Exception):
    pass


def setup_definitions(source, destination):
    target_setup_func = None
    try:
        target_setup_func = definition_dispatch[type(source)]
    except KeyError:
        for a_key in definition_dispatch.keys():
            if isinstance(source, a_key):
                target_setup_func = definition_dispatch[a_key]
                break
        if not target_setup_func:
            raise UnknownDefinitionTypeException(repr(type(source)))
    target_setup_func(source, destination)
