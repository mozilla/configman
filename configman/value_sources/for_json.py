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

import json
import collections
import sys

from .. import converters as conv
from ..namespace import Namespace
from ..option import Option, Aggregation

from source_exceptions import (ValueException, NotEnoughInformationException,
                               NoHandlerForType)

can_handle = (basestring,
              json
             )

file_name_extension = 'json'


class LoadingJsonFileFailsException(ValueException):
    pass


class ValueSource(object):

    def __init__(self, source, the_config_manager=None):
        self.values = None
        if source is json:
            try:
                app = the_config_manager._get_option(
                                                      'admin.application')
                source = "%s.%s" % (app.value.app_name, file_name_extension)
            except (AttributeError, KeyError):
                raise NotEnoughInformationException("Can't setup an json "
                                                    "file without knowing "
                                                    "the file name")
        if (isinstance(source, basestring) and
           source.endswith(file_name_extension)):
            try:
                with open(source) as fp:
                    self.values = json.load(fp)
            except IOError, x:
                # The file doesn't exist.  That's ok, we'll give warning
                # but this isn't a fatal error
                import warnings
                warnings.warn("%s doesn't exist" % source)
                self.values = {}
            except ValueError:
                raise LoadingJsonFileFailsException("Cannot load json: %s" %
                                                    str(x))
        else:
            raise NoHandlerForType("json can't handle: %s" %
                                      str(source))

    def get_values(self, config_manager, ignore_mismatches):
        return self.values

    @staticmethod
    def recursive_default_dict():
        return collections.defaultdict(ValueSource.recursive_default_dict)

    @staticmethod
    def write(option_iter, output_stream=sys.stdout):
        json_dict = ValueSource.recursive_default_dict()
        for qkey, key, val in option_iter():
            if isinstance(val, Namespace):
                continue
            d = json_dict
            for x in qkey.split('.'):
                d = d[x]
            if isinstance(val, Option):
                for okey, oval in val.__dict__.iteritems():
                    try:
                        d[okey] = conv.to_string_converters[type(oval)](oval)
                    except KeyError:
                        d[okey] = str(oval)
                d['default'] = d['value']
            elif isinstance(val, Aggregation):
                d['name'] = val.name
                fn = val.function
                d['function'] = conv.to_string_converters[type(fn)](fn)
        json.dump(json_dict, output_stream)
