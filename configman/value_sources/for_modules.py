# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function

try:
    from functools import total_ordering
except ImportError:
    from total_ordering import total_ordering
import types
import sys
import datetime
import json
import keyword
import re
import six

from inspect import isclass, ismodule, isfunction
from collections import defaultdict

from configman.namespace import Namespace
from configman.dotdict import DotDict
from configman.option import Option, Aggregation
from configman.converters import (
    to_str,
    class_converter,
    known_mapping_str_to_type,
    CannotConvertError,
    str_quote_stripper,
    compiled_regexp_type
)
file_name_extension = 'py'


can_handle = (
    types.ModuleType,
    six.binary_type,
    six.text_type,
)

#------------------------------------------------------------------------------
# Converter Section
#------------------------------------------------------------------------------

# each value source is allowed to have its own set of converters for
# serializing objects to strings.  This converter section defines the functions
# that can serialize objects into Python code.  This allows writing of a
# Python module in the same manner that ini files are written.

identifier_re = re.compile(r'^[a-z_][a-z0-9_\.]*$', re.I)


#------------------------------------------------------------------------------
def is_identifier(a_candidate):
    if a_candidate in keyword.kwlist:
        return False  # identifiers can't also be keywords
    return bool(identifier_re.match(a_candidate))


#------------------------------------------------------------------------------
def sequence_to_string(
    a_list,
    open_bracket_char='[',
    close_bracket_char=']',
    delimiter=", "
):
    """a dedicated function that turns a list into a comma delimited string
    of items converted.  This method will flatten nested lists."""
    return "%s%s%s" % (
        open_bracket_char,
        delimiter.join(
            local_to_str(x)
            for x in a_list
        ),
        close_bracket_char
    )


#------------------------------------------------------------------------------
def dict_to_string(d):
    return json.dumps(
        d,
        indent=4,
        sort_keys=True,
        separators=(',', ': '),
    )


#------------------------------------------------------------------------------
def string_to_string(a_string):
    a_string = to_str(a_string)
    quote = '"'
    if '"' in a_string:
        quote = "'"
    if "'" in a_string:
        quote = '"""'
    if "/n" in a_string:
        quote = "'''"
    return "%s%s%s" % (quote, a_string, quote)


#------------------------------------------------------------------------------
def unicode_to_unicode(a_string):
    quote = '"'
    if '"' in a_string:
        quote = "'"
    if "'" in a_string:
        quote = '"""'
    if "/n" in a_string:
        quote = "'''"
    return "u%s%s%s" % (quote, a_string, quote)


#------------------------------------------------------------------------------
def datetime_to_string(d):
    return "datetime(year=%s, month=%s, day=%s, hour=%s, " \
        "minute=%s, second=%s)" % (
            d.year,
            d.month,
            d.day,
            d.hour,
            d.minute,
            d.second,
        )


#------------------------------------------------------------------------------
def date_to_string(d):
    return "date(year=%s, month=%s, day=%s)" % (
        d.year,
        d.month,
        d.day,
    )


#------------------------------------------------------------------------------
def timedelta_to_string(d):
    return "timedelta(days=%s, seconds=%s)" % (
        d.days,
        d.seconds,
    )


#------------------------------------------------------------------------------
def get_import_for_type(t):
    """given a type, return a tuple of the (module-path, type_name)
    or (None, None) if it is a built in."""
    t_as_string = to_str(t)
    if not is_identifier(t_as_string):
        # this class expanded into something other than a single identifier
        # we can ignore it.  This is the case when we encounter something
        # like the configman.converter.str_to_classes_in_namespaces
        # InnerClassList.  We can safely ignore these things here.
        return (None, None)
    if '.' in t_as_string:
        parts = t_as_string.split('.')
        return ('.'.join(parts[:-1]), parts[-1])
    else:
        if t_as_string in known_mapping_str_to_type:
            return (None, None)
        return (None, t_as_string)


#------------------------------------------------------------------------------
local_to_string_converters = {
    list: sequence_to_string,
    tuple: sequence_to_string,
    dict: dict_to_string,
    datetime.datetime: datetime_to_string,
    datetime.date: date_to_string,
    datetime.timedelta: timedelta_to_string,
    type(None): lambda x: "None",
    compiled_regexp_type: lambda x: string_to_string(x.pattern)
}
if six.PY2:
    local_to_string_converters[six.text_type] = unicode_to_unicode
    local_to_string_converters[six.binary_type] = string_to_string
elif six.PY3:
    local_to_string_converters[six.text_type] = string_to_string
    local_to_string_converters[six.binary_type] = string_to_string


#------------------------------------------------------------------------------
def find_to_string_converter(a_thing):
    for a_candidate_type, to_string_converter in local_to_string_converters:
        if isinstance(a_thing, a_candidate_type):
            return to_string_converter
    return None


#------------------------------------------------------------------------------
def local_to_str(a_thing):
    try:
        return local_to_string_converters[type(a_thing)](a_thing)
    except KeyError:
        try:
            return find_to_string_converter(a_thing)(a_thing)
        except TypeError:
            return to_str(a_thing)


#==============================================================================
@total_ordering
class OrderableObj(object):
    """Python3 can't sort non-string types implicitly.
    """
    def __init__(self, value):
        if not isinstance(value, six.string_types):
            value_str = to_str(value)
        else:
            value_str = value
        self.value_str = value_str
        self.value = value
    def __lt__(self, other):
        return (self.value_str < other.value_str)
    def __eq__(self, other):
        return (self.value_str == other.value_str)
    def __repr__(self):
        return self.value_str


#==============================================================================
@total_ordering
class OrderableTuple(object):
    """Python3 can't sort non-string types implicitly.
    """
    def __init__(self, value, index=1):
        self.value = value
        self.index = index
    def __lt__(self, other):
        return (self.value[self.index] < other.value[self.index])
    def __eq__(self, other):
        return (self.value[self.index] == other.value[self.index])
    def __repr__(self):
        return self.value.__repr__()


#==============================================================================
class ValueSource(object):
    #--------------------------------------------------------------------------
    def __init__(self, source, the_config_manager=None):
        if isinstance(source, (six.binary_type, six.text_type)):
            source = class_converter(source)
        module_as_dotdict = DotDict()
        try:
            ignore_symbol_list = source.ignore_symbol_list
            if 'ignore_symbol_list' not in ignore_symbol_list:
                ignore_symbol_list.append('ignore_symbol_list')
        except AttributeError:
            ignore_symbol_list = []
        try:
            self.always_ignore_mismatches = source.always_ignore_mismatches
        except AttributeError:
            pass  # don't need to do anything - mismatches will not be ignored
        for key, value in six.iteritems(source.__dict__):
            if key.startswith('__') and key != "__doc__":
                continue
            if key in ignore_symbol_list:
                continue
            module_as_dotdict[key] = value
        self.module = source
        self.source = module_as_dotdict

    #--------------------------------------------------------------------------
    def get_values(self, config_manager, ignore_mismatches, obj_hook=DotDict):
        if isinstance(self.source, obj_hook):
            return self.source
        return obj_hook(initializer=self.source)

    #--------------------------------------------------------------------------
    @staticmethod
    def write_class(key, value, alias_by_class, output_stream):
        if value in alias_by_class:
            class_str = alias_by_class[value]
        else:
            class_str = local_to_str(value)
        if is_identifier(class_str):
            parts = [x.strip() for x in class_str.split('.') if x.strip()]
            print('%s = %s' % (key, parts[-1]), file=output_stream)
        else:
            print('%s = "%s"' % (key, class_str), file=output_stream)

    #--------------------------------------------------------------------------
    @staticmethod
    def write_bare_value(key, value, output_stream):
        if isclass(value):
            ValueSource.write_class(key, value, output_stream)
            return
        try:
            value = local_to_str(value)
        except CannotConvertError:
            value = repr(value)
        if '\n' in value:
            value = "'''%s'''" % str_quote_stripper(value)
        print('%s = %s' % (key, value), file=output_stream)

    #--------------------------------------------------------------------------
    @staticmethod
    def write_option(key, an_option, alias_by_class, output_stream):
        print('\n', end='', file=output_stream)
        if an_option.doc:
            print('# %s' % an_option.doc, file=output_stream)
        if (
            isclass(an_option.value)
            or ismodule(an_option.value)
            or isfunction(an_option.value)
        ):
            ValueSource.write_class(
                key,
                an_option.value,
                alias_by_class,
                output_stream
            )
            return
        else:
            value = local_to_str(an_option.value)
            print('%s = %s' % (key, value), file=output_stream)

    #--------------------------------------------------------------------------
    @staticmethod
    def write_namespace(key, a_namespace, output_stream):
        print('\n# Namespace:', key, file=output_stream)
        if 'doc' in dir(a_namespace):
            print('#', a_namespace.doc, file=output_stream)
        print('%s = DotDict()' % key, file=output_stream)

    #--------------------------------------------------------------------------
    @staticmethod
    def write(source_mapping, output_stream=sys.stdout):
        """This method writes a Python module respresenting all the keys
        and values known to configman.
        """
        # a set of classes, modules and/or functions that are values in
        # configman options.  These values will have to be imported in the
        # module that this method is writing.
        set_of_classes_needing_imports = set()
        # once symbols are imported, they are in the namespace of the module,
        # but that's not where we want them.  We only want them to be values
        # in configman Options.  This set will be used to make a list of
        # these symbols, to forewarn a future configman that reads this
        # module, that it can ignore these symbols. This will prevent that
        # future configman from issuing a "mismatced symbols" warinng.
        symbols_to_ignore = set()

        # look ahead to see what sort of imports we're going to have to do
        for key in source_mapping.keys_breadth_first():
            value = source_mapping[key]

            if isinstance(value, Aggregation):
                # Aggregations don't get included, skip on
                continue

            if '.' in key:
                # this indicates that there are things in nested namespaces,
                # we will use the DotDict class to represent namespaces
                set_of_classes_needing_imports.add(DotDict)

            option = None
            if isinstance(value, Option):
                # it's the value inside the option, not the option itself
                # that is of interest to us
                option = value
                value = option.value

            if value is None:
                # we don't need in import anything having to do with None
                continue

            if isclass(value) or ismodule(value) or isfunction(value):
                # we know we need to import any of these types
                set_of_classes_needing_imports.add(value)
            else:
                try:
                    # perhaps the value is an instance of a class?  If so,
                    # we'll likely need to import that class, but only if
                    # we don't have a way to convert a string to that class
                    set_of_classes_needing_imports.add(value.__class__)
                except AttributeError:
                    # it's not a class instance, we can skip on
                    pass

        # for everyone of the imports that we're going to have to create
        # we need to know the dotted module pathname and the name of the
        # of the class/module/function.  This routine make a list of 3-tuples
        # class, dotted_module_path, class_name
        class_and_module_path_and_class_name = []
        for a_class in set_of_classes_needing_imports:
            module_path, class_name = get_import_for_type(a_class)
            if (not module_path) and (not class_name):
                continue
            class_and_module_path_and_class_name.append(
                (a_class, module_path, class_name)
            )

        # using the collection of 3-tuples, create a lookup mapping where a
        # class is the key to a 2-tuple of the dotted_module_path & class_name.
        # This is also the appropriate time to detect any name collisions
        # and create a mapping of aliases, so we can resolve name collisions.
        class_name_by_module_path_list = defaultdict(list)
        alias_by_class = {}
        previously_used_names = set()
        for (
            a_class,
            a_module_path,
            class_name
        ) in class_and_module_path_and_class_name:
            if class_name:
                if class_name in previously_used_names:
                    new_class_name_alias = "%s_%s" % (
                        a_module_path.replace('.', '_'),
                        class_name
                    )
                    alias_by_class[a_class] = new_class_name_alias
                    previously_used_names.add(new_class_name_alias)
                else:
                    previously_used_names.add(class_name)
                class_name_by_module_path_list[a_module_path].append(
                    (a_class, class_name)
                )

        # start writing the output module
        print("# generated Python configman file\n", file=output_stream)

        # the first section that we're going to write is imports of the form:
        #     from X import Y
        # and
        #     from X import (
        #         A,
        #         B,
        #     )
        sorted_list = [x.value for x in sorted([OrderableObj(x) for x in
                       class_name_by_module_path_list.keys()])]
        for a_module_path in sorted_list:
            print(a_module_path)
            # if there is no module path, then it is something that we don't
            # need to import.  If the module path begins with underscore then
            # it is private and we ought not step into that mire.  If that
            # causes the output module to fail, it is up to the implementer
            # of the configman option to have created an approprate
            # "from_string" & "to_string" configman Option function references.
            if a_module_path is None or a_module_path.startswith('_'):
                continue
            list_of_class_names = \
                class_name_by_module_path_list[a_module_path]
            if len(list_of_class_names) > 1:
                output_line = "from %s import (\n" % a_module_path
                sorted_list = [x.value for x in sorted([OrderableTuple(x)
                               for x in list_of_class_names])]
                for a_class, a_class_name in sorted_list:
                    if a_class in alias_by_class:
                        output_line = "%s\n    %s as %s," % (
                            output_line,
                            a_class_name,
                            alias_by_class[a_class]
                        )
                        symbols_to_ignore.add(alias_by_class[a_class])
                    else:
                        output_line = "%s    %s,\n" % (
                            output_line,
                            a_class_name
                        )
                        symbols_to_ignore.add(a_class_name)

                output_line = output_line + ')'
                print(output_line.strip(), file=output_stream)
            else:
                a_class, a_class_name = list_of_class_names[0]
                output_line = "from %s import %s" % (
                    a_module_path,
                    a_class_name
                )
                if a_class in alias_by_class:
                    output_line = "%s as %s" % (
                        output_line,
                        alias_by_class[a_class]
                    )
                    symbols_to_ignore.add(alias_by_class[a_class])
                else:
                    symbols_to_ignore.add(a_class_name)
                print(output_line.strip(), file=output_stream)
        print('', file=output_stream)

        # The next section to write will be the imports of the form:
        #     import X
        sorted_list = [x.value for x in sorted([OrderableObj(x) for x in
                       class_name_by_module_path_list.keys()])]
        for a_module_path in sorted_list:
            list_of_class_names = \
                class_name_by_module_path_list[a_module_path]
            a_class, a_class_name = list_of_class_names[0]
            if a_module_path:
                continue
            import_str = ("import %s" % a_class_name).strip()
            symbols_to_ignore.add(a_class_name)
            print(import_str, file=output_stream)

        # See the explanation of 'symbols_to_ignore' above
        if symbols_to_ignore:
            print(
                "\n" \
                "# the following symbols will be ignored by configman when\n" \
                "# this module is used as a value source.  This will\n" \
                "# suppress the mismatch warning since these symbols are\n" \
                "# values for options, not option names themselves.",
                file=output_stream
            )
            print("ignore_symbol_list = [", file=output_stream)
            for a_symbol in sorted(symbols_to_ignore):
                print('    "%s",' % a_symbol, file=output_stream)
            print(']\n', file=output_stream)

        # finally, as the last step, we need to write out the keys and values
        # will be used by a future configman as Options and values.
        sorted_keys = sorted(
            source_mapping.keys_breadth_first(include_dicts=True)
        )
        for key in sorted_keys:
            value = source_mapping[key]
            if isinstance(value, Namespace):
                ValueSource.write_namespace(key, value, output_stream)
            elif isinstance(value, Option):
                ValueSource.write_option(
                    key,
                    value,
                    alias_by_class,
                    output_stream
                )
            elif isinstance(value, Aggregation):
                # skip Aggregations
                continue
            else:
                ValueSource.write_bare_value(key, value, output_stream)
