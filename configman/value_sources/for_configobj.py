# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function

import sys
import six
import re
import os.path

import configobj

from configman.converters import (
    to_str,
)
from configman.value_sources.source_exceptions import (
    CantHandleTypeException,
    ValueException,
    NotEnoughInformationException
)
from configman.namespace import Namespace
from configman.option import Option

from configman.dotdict import DotDict
from configman.memoize import memoize

file_name_extension = 'ini'

can_handle = (
    configobj,
    configobj.ConfigObj,
    six.binary_type,
    six.text_type,
)


#==============================================================================
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

    #--------------------------------------------------------------------------
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

    #--------------------------------------------------------------------------
    def _load(self, infile, configspec):
        """this overrides the original ConfigObj method of the same name.  It
        runs through the input file collecting lines into a list.  When
        completed, this method submits the list of lines to the super class'
        function of the same name.  ConfigObj proceeds, completely unaware
        that it's input file has been preprocessed."""
        if isinstance(infile, (six.binary_type, six.text_type)):
            infile = to_str(infile)
            original_path = os.path.dirname(infile)
            expanded_file_contents = self._expand_files(infile, original_path)
            super(ConfigObjWithIncludes, self)._load(
                expanded_file_contents,
                configspec
            )
        else:
            super(ConfigObjWithIncludes, self)._load(infile, configspec)


#==============================================================================
class LoadingIniFileFailsException(ValueException):
    pass


#==============================================================================
class ValueSource(object):

    #--------------------------------------------------------------------------
    def __init__(
        self, source,
        config_manager=None,
        top_level_section_name=''
    ):
        self.delayed_parser_instantiation = False
        self.top_level_section_name = top_level_section_name
        if source is configobj.ConfigObj:
            try:
                app = config_manager._get_option('admin.application')
                source = "%s.%s" % (app.value.app_name, file_name_extension)
            except AttributeError:
                # we likely don't have the admin.application object set up yet.
                # we need to delay the instantiation of the config parser
                # until later.
                if source is None:
                    raise NotEnoughInformationException(
                        "Can't setup an ini file without knowing the file name"
                    )
                self.delayed_parser_instantiation = True
                return
            if not os.path.exists(source) and config_manager.config_optional:
                return
        if isinstance(source, (six.binary_type, six.text_type)):
            source = to_str(source)
        if (
            isinstance(source, six.string_types) and
            source.endswith(file_name_extension)
        ):
            try:
                self.config_obj = ConfigObjWithIncludes(source)
            except Exception as x:
                raise LoadingIniFileFailsException(
                    "ConfigObj cannot load ini: %s" % str(x)
                )
        else:
            raise CantHandleTypeException()

    #--------------------------------------------------------------------------
    @memoize()
    def get_values(self, config_manager, ignore_mismatches, obj_hook=DotDict):
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
                return obj_hook()  # return empty dict of the obj_hook type
        if isinstance(self.config_obj, obj_hook):
            return self.config_obj
        return obj_hook(initializer=self.config_obj)

    #--------------------------------------------------------------------------
    @staticmethod
    def write(source_mapping, output_stream=sys.stdout):
        ValueSource._write_ini(source_mapping, output_stream=output_stream)

    #--------------------------------------------------------------------------
    @staticmethod
    def _namespace_reference_value_from_sort(key_value_tuple):
        key, value = key_value_tuple
        if value._reference_value_from:
            return 'aaaaaa' + key
        else:
            return key

    #--------------------------------------------------------------------------
    @staticmethod
    def _write_ini(source_dict, namespace_name=None, level=0, indent_size=4,
                   output_stream=sys.stdout):
        """this function prints the components of a configobj ini file.  It is
        recursive for outputing the nested sections of the ini file."""
        options = [
            value
            for value in source_dict.values()
            if isinstance(value, Option)
        ]
        options.sort(key=lambda x: x.name)
        indent_spacer = " " * (level * indent_size)
        for an_option in options:
            print("%s# %s" % (indent_spacer, an_option.doc),
                  file=output_stream)
            option_value = to_str(an_option)

            if an_option.reference_value_from:
                print(
                    '%s# see "%s.%s" for the default or override it here' % (
                        indent_spacer,
                        an_option.reference_value_from,
                        an_option.name
                    ),
                    file=output_stream
                )

            if an_option.likely_to_be_changed or an_option.has_changed:
                option_format = '%s%s=%s\n'
            else:
                option_format = '%s#%s=%s\n'

            if isinstance(option_value, six.string_types) and \
                    ',' in option_value:
                # quote lists unless they're already quoted
                if option_value[0] not in '\'"':
                    option_value = '"%s"' % option_value

            print(option_format % (indent_spacer, an_option.name,
                                   option_value),
                  file=output_stream)
        next_level = level + 1
        namespaces = [
            (key, value)
            for key, value in source_dict.items()
            if isinstance(value, Namespace)
        ]
        namespaces.sort(key=ValueSource._namespace_reference_value_from_sort)
        for key, namespace in namespaces:
            next_level_spacer = " " * next_level * indent_size
            print("%s%s%s%s\n" % (indent_spacer, "[" * next_level, key,
                                  "]" * next_level),
                  file=output_stream)
            if namespace._doc:
                print("%s%s" % (next_level_spacer, namespace._doc),
                      file=output_stream)
            if namespace._reference_value_from:
                print("%s#+include ./common_%s.ini\n"
                      % (next_level_spacer, key), file=output_stream)

            if namespace_name:
                ValueSource._write_ini(
                    source_dict=namespace,
                    namespace_name="%s.%s" % (namespace_name, key),
                    level=level+1,
                    indent_size=indent_size,
                    output_stream=output_stream
                )
            else:
                ValueSource._write_ini(
                    source_dict=namespace,
                    namespace_name=key,
                    level=level+1,
                    indent_size=indent_size,
                    output_stream=output_stream
                )
