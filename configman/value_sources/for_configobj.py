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
import re
import os.path

import configobj

from source_exceptions import (CantHandleTypeException, ValueException,
                               NotEnoughInformationException)
from ..namespace import Namespace
from ..option import Option
from .. import converters as conv

file_name_extension = 'ini'

can_handle = (configobj,
              configobj.ConfigObj,
              basestring,
             )


class ConfigObjWithIncludes(configobj.ConfigObj):
    """This derived class is an extention to ConfigObj that adds nested
    includes to ini files.  Here's an example:

    db.ini:

        dbhostname=myserver
        dbname=some_database
        dbuser=dwight
        dbpassword=secrets

    app.ini:
        [source]
        +include ./db.ini

        [destination]
        +include ./db.ini

    when the 'app.ini' file is loaded, ConfigObj will respond as if the file
    had been written like this:
        [source]
        dbhostname=myserver
        dbname=some_database
        dbuser=dwight
        dbpassword=secrets

        [destination]
        dbhostname=myserver
        dbname=some_database
        dbuser=dwight
        dbpassword=secrets
    """
    _include_re = re.compile(r'^(\s*)\+include\s+(.*?)\s*$')

    def _expand_files(self, file_name, original_path, indent=""):
        """This recursive function accepts a file name, opens the file and then
        spools the contents of the file into a list, examining each line as it
        does so.  If it detects a line beginning with "+include", it assumes
        the string immediately following is a file name.  Recursing, the file
        new file is openned and its contents are spooled into the accumulating
        list."""
        expanded_file_contents = []
        with open(file_name) as f:
            for a_line in f:
                match = ConfigObjWithIncludes._include_re.match(a_line)
                if match:
                    include_file = match.group(2)
                    include_file = os.path.join(
                          original_path,
                          include_file
                    )
                    new_lines = self._expand_files(
                        include_file,
                        os.path.dirname(include_file),
                        indent + match.group(1)
                    )
                    expanded_file_contents.extend(new_lines)
                else:
                    expanded_file_contents.append(indent + a_line.rstrip())
        return expanded_file_contents

    def _load(self, infile, configspec):
        """this overrides the original ConfigObj method of the same name.  It
        runs through the input file collecting lines into a list.  When
        completed, this method submits the list of lines to the super class'
        function of the same name.  ConfigObj proceeds, completely unaware
        that it's input file has been preprocessed."""
        if isinstance(infile, basestring):
            original_path = os.path.dirname(infile)
            expanded_file_contents = self._expand_files(infile, original_path)
            super(ConfigObjWithIncludes, self)._load(
              expanded_file_contents,
              configspec
            )
        else:
            super(ConfigObjWithIncludes, self)._load(infile, configspec)


class LoadingIniFileFailsException(ValueException):
    pass


class ValueSource(object):

    def __init__(self, source,
                 config_manager=None,
                 top_level_section_name=''):
        self.delayed_parser_instantiation = False
        self.top_level_section_name = top_level_section_name
        if source is configobj.ConfigObj:
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
                #self.config_obj = configobj.ConfigObj(source)
                self.config_obj = ConfigObjWithIncludes(source)
            except Exception, x:
                raise LoadingIniFileFailsException(
                  "ConfigObj cannot load ini: %s" % str(x))
        else:
            raise CantHandleTypeException()

    def get_values(self, config_manager, ignore_mismatches):
        """Return a nested dictionary representing the values in the ini file.
        In the case of this ValueSource implementation, both parameters are
        dummies."""
        if self.delayed_parser_instantiation:
            try:
                app = config_manager._get_option('admin.application')
                source = "%s%s" % (app.value.app_name, file_name_extension)
                self.config_obj = configobj.ConfigObj(source)
                self.delayed_parser_instantiation = False
            except AttributeError:
                # we don't have enough information to get the ini file
                # yet.  we'll ignore the error for now
                return {}
        return self.config_obj

    @staticmethod
    def write(source_mapping, output_stream=sys.stdout):
        ValueSource._write_ini(source_mapping, output_stream=output_stream)

    @staticmethod
    def _write_ini(source_dict, level=0, indent_size=4,
                   output_stream=sys.stdout):
        """this function prints the components of a configobj ini file.  It is
        recursive for outputing the nested sections of the ini file."""
        options = [
          value
          for value in source_dict.values()
              if isinstance(value, Option)
        ]
        options.sort(cmp=lambda x, y: cmp(x.name, y.name))
        namespaces = [
          (key, value)
          for key, value in source_dict.items()
              if isinstance(value, Namespace)
        ]
        namespaces.sort()
        indent_spacer = " " * (level * indent_size)
        for an_option in options:
            print >>output_stream, "%s# name: %s" % (indent_spacer,
                                                     an_option.name)
            print >>output_stream, "%s# doc: %s" % (indent_spacer,
                                                    an_option.doc)
            print >>output_stream, "%s# converter: %s" % (
              indent_spacer,
              conv.py_obj_to_str(
                an_option.from_string_converter
              )
            )
            option_value = conv.option_value_str(an_option)
            if isinstance(option_value, unicode):
                option_value = option_value.encode('utf8')

            if an_option.comment_out:
                option_format = '%s#%s=%s\n'
                print >>output_stream, "%s# The following value has been " \
                    "automatically commented out because" % indent_spacer
                print >>output_stream, "%s#   the option is found in other " \
                    "sections and the defaults are the same." % indent_spacer
                print >>output_stream, "%s#   The common value can be found " \
                    "in the lowest level section. Uncomment" % indent_spacer
                print >>output_stream, "%s#   to override that lower level " \
                    "value" % indent_spacer
            else:
                option_format = '%s%s=%s\n'

            repr_for_converter = repr(an_option.from_string_converter)
            if (
                repr_for_converter.startswith('<function') or
                repr_for_converter.startswith('<built-in')
            ):
                option_value = repr(option_value)
                print >>output_stream, "%s# Inspect the automatically " \
                    "written value below to make sure it is valid" \
                    % indent_spacer
                print >>output_stream, "%s#   as a Python object for its " \
                    "intended converter function." % indent_spacer
            elif an_option.from_string_converter is str:
                if ',' in option_value or '\n' in option_value:
                    option_value = repr(option_value)

            if an_option.not_for_definition:
                print >>output_stream, "%s# The following value is common " \
                    "for more than one section below. Its value" \
                    % indent_spacer
                print >>output_stream, "%s#   may be set here for all or " \
                    "it can be overridden in its original section" \
                    % indent_spacer

            print >>output_stream, option_format % (
              indent_spacer,
              an_option.name,
              option_value
            )
        next_level = level + 1
        for key, namespace in namespaces:
            print >>output_stream, "%s%s%s%s\n" % (
              " " * level * indent_size,
              "[" * next_level,
              key,
              "]" * next_level
            )
            ValueSource._write_ini(
              namespace,
              level=level + 1,
              indent_size=indent_size,
              output_stream=output_stream
            )
