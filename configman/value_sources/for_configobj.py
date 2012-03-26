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

import sys
import collections

import configobj
from configobj import ConfigObj

from source_exceptions import (CantHandleTypeException, ValueException,
                               NotEnoughInformationException)
from ..namespace import Namespace
from ..option import Option
from .. import converters as conv

file_name_extension = 'ini'

can_handle = (configobj,
              ConfigObj,
              basestring,
             )


class LoadingIniFileFailsException(ValueException):
    pass


class ValueSource(object):

    def __init__(self, source,
                 config_manager=None,
                 top_level_section_name=''):
        self.delayed_parser_instantiation = False
        self.top_level_section_name = top_level_section_name
        if source is ConfigObj:
            try:
                app = config_manager._get_option('admin.application')
                source = "%s.%s" % (app.value.app_name, file_name_extension)
            except AttributeError:
                # we likely don't have the admin.application object set up yet.
                # we need to delay the instantiation of the ConfigParser
                # until later.
                if source is None:
                    raise NotEnoughInformationException("Can't setup an ini "
                                                        "file without knowing "
                                                        "the file name")
                self.delayed_parser_instantiation = True
                return
        if (isinstance(source, basestring) and
            source.endswith(file_name_extension)):
            try:
                self.config_obj = ConfigObj(source)
            except Exception, x:
                raise LoadingIniFileFailsException(
                  "ConfigObj cannot load ini: %s" % str(x))
        else:
            raise CantHandleTypeException(
                        "ConfigObj doesn't know how to handle %s." % source)

    def get_values(self, config_manager, ignore_mismatches):
        """Return a nested dictionary representing the values in the ini file.
        In the case of this ValueSource implementation, both parameters are
        dummies."""
        if self.delayed_parser_instantiation:
            try:
                app = config_manager._get_option('admin.application')
                source = "%s%s" % (app.value.app_name, file_name_extension)
                self.config_obj = ConfigObj(source)
                self.delayed_parser_instantiation = False
            except AttributeError:
                # we don't have enough information to get the ini file
                # yet.  we'll ignore the error for now
                return {}
        return self.config_obj

    @staticmethod
    def recursive_default_dict():
        return collections.defaultdict(ValueSource.recursive_default_dict)

    @staticmethod
    def write(option_iter, output_stream=sys.stdout):
        # must construct a dict from the iter
        destination_dict = ValueSource.recursive_default_dict()
        for qkey, key, val in option_iter():
            if isinstance(val, Namespace):
                continue
            d = destination_dict
            for x in qkey.split('.')[:-1]:
                d = d[x]
            if isinstance(val, Option):
                v = val.value
                v_str = conv.to_string_converters[type(v)](v)
                d[key] = v_str
        config = ConfigObj(destination_dict)
        config.write(outfile=output_stream)
