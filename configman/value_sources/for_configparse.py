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
import ConfigParser

from source_exceptions import (CantHandleTypeException, ValueException,
                               NotEnoughInformationException)
from .. import namespace
from .. import option
from .. import converters as conv


file_name_extension = 'ini'

can_handle = (ConfigParser,
              ConfigParser.RawConfigParser,  # just the base class, subclasses
                                             # will be detected too
              basestring,
             )


class LoadingIniFileFailsException(ValueException):
    pass


class ValueSource(object):

    def __init__(self, source,
                 config_manager=None,
                 top_level_section_name='top_level'):
        self.delayed_parser_instantiation = False
        self.top_level_section_name = top_level_section_name
        if source is ConfigParser:
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
                self.configparser = self._create_parser(source)
            except Exception, x:
                # FIXME: this doesn't give you a clue why it fail.
                #  Was it because the file didn't exist (IOError) or because it
                #  was badly formatted??
                raise LoadingIniFileFailsException("Cannot load ini: %s"
                                                   % str(x))

        elif isinstance(source, ConfigParser.RawConfigParser):
            self.configparser = source
        else:
            raise CantHandleTypeException(
                        "ConfigParser doesn't know how to handle %s." % source)

    @staticmethod
    def _create_parser(source):
        parser = ConfigParser.ConfigParser()
        parser.optionxform = str
        parser.read(source)
        return parser

    def get_values(self, config_manager, ignore_mismatches):
        """Return a nested dictionary representing the values in the ini file.
        In the case of this ValueSource implementation, both parameters are
        dummies."""
        if self.delayed_parser_instantiation:
            try:
                app = config_manager._get_option('admin.application')
                source = "%s%s" % (app.value.app_name, file_name_extension)
                self.configparser = self._create_parser(source)
                self.delayed_parser_instantiation = False
            except AttributeError:
                # we don't have enough information to get the ini file
                # yet.  we'll ignore the error for now
                return {}
        options = {}
        for a_section in self.configparser.sections():
            if a_section == self.top_level_section_name:
                prefix = ''
            else:
                prefix = "%s." % a_section
            for an_option in self.configparser.options(a_section):
                name = '%s%s' % (prefix, an_option)
                options[name] = self.configparser.get(a_section, an_option)
        return options

    @staticmethod
    def write(option_iter, output_stream=sys.stdout):
        print >> output_stream, '[top_level]'
        for qkey, key, val in option_iter():
            if isinstance(val, namespace.Namespace):
                print >> output_stream, '[%s]' % key
                print >> output_stream, '# %s\n' % val._doc
            elif isinstance(val, option.Option):
                print >> output_stream, '# name:', qkey
                print >> output_stream, '# doc:', val.doc
                print >> output_stream, '# converter:', \
                   conv.py_obj_to_str(val.from_string_converter)
                val_str = conv.option_value_str(val)
                print >> output_stream, '%s=%s\n' % (key, val_str)
            elif isinstance(val, option.Aggregation):
                # there is nothing to do for Aggregations at this time
                # it appears here anyway as a marker for future enhancements
                pass
