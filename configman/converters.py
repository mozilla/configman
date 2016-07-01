# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function

import sys
import re
import datetime
import types
import json
import six

from configman.datetime_util import (
    datetime_from_ISO_string,
    date_from_ISO_string,
    datetime_to_ISO_string,
    date_to_ISO_string,
)

# for backward compatibility these two methods get alternate names
datetime_converter = datetime_from_ISO_string
date_converter = date_from_ISO_string

from configman.config_exceptions import CannotConvertError

#------------------------------------------------------------------------------
#  Utility section
#
#  various handy functions used or associated with type conversions
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
def str_dict_keys(a_dict):
    """return a modified dict where all the keys that are anything but str get
    converted to str.
    E.g.

      >>> result = str_dict_keys({u'name': u'Peter', u'age': 99, 1: 2})
      >>> # can't compare whole dicts in doctests
      >>> result['name']
      u'Peter'
      >>> result['age']
      99
      >>> result[1]
      2

    The reason for this is that in Python <= 2.6.4 doing
    ``MyClass(**{u'name': u'Peter'})`` would raise a TypeError

    Note that only unicode types are converted to str types.
    The reason for that is you might have a class that looks like this::

        class Option(object):
            def __init__(self, foo=None, bar=None, **kwargs):
                ...

    And it's being used like this::

        Option(**{u'foo':1, u'bar':2, 3:4})

    Then you don't want to change that {3:4} part which becomes part of
    `**kwargs` inside the __init__ method.
    Using integers as parameter keys is a silly example but the point is that
    due to the python 2.6.4 bug only unicode keys are converted to str.
    """
    new_dict = {}
    for key in a_dict:
        if six.PY2 and isinstance(key, six.text_type):
            new_dict[str(key)] = a_dict[key]
        else:
            new_dict[key] = a_dict[key]
    return new_dict


#------------------------------------------------------------------------------
def str_quote_stripper(input_str):
    if not isinstance(input_str, six.string_types):
        raise ValueError(input_str)
    while (
        input_str
        and input_str[0] == input_str[-1]
        and input_str[0] in ("'", '"')
    ):
        input_str = input_str.strip(input_str[0])
    return input_str


#------------------------------------------------------------------------------
#  from string section
#
#  a set of functions that will convert from a string representation into some
#  specified type
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# a bunch of known mappings of builtin items to strings
import six.moves.builtins as builtins
known_mapping_str_to_type = dict(
    (key, val) for key, val in sorted(builtins.__dict__.items())
    if val not in (True, False)
)

#------------------------------------------------------------------------------
from configman.datetime_util import (
    str_to_timedelta,  # don't worry about pyflakes here, unused in this file
    timedelta_to_str,  # but used elsewhere
)

timedelta_converter = str_to_timedelta  # for backward compatiblity


#------------------------------------------------------------------------------
def py2_to_unicode(input_str):
    if six.PY2:
        input_str = six.text_type(input_str, 'utf-8')
    return input_str


def py3_to_bytes(input_str):
    if six.py3:
        input_str = input_str.encode('utf-8')
    return input_str


#------------------------------------------------------------------------------
def str_to_boolean(input_str):
    """ a conversion function for boolean
    """
    if not isinstance(input_str, six.string_types):
        raise ValueError(input_str)
    input_str = str_quote_stripper(input_str)
    return input_str.lower() in ("true", "t", "1", "y", "yes")

boolean_converter = str_to_boolean  # for backward compatiblity


#------------------------------------------------------------------------------
def str_to_python_object(input_str):
    """ a conversion that will import a module and class name
    """
    if not input_str:
        return None
    if six.PY3 and isinstance(input_str, six.binary_type):
        input_str = to_str(input_str)
    if not isinstance(input_str, six.string_types):
        # gosh, we didn't get a string, we can't convert anything but strings
        # we're going to assume that what we got is actually what was wanted
        # as the output
        return input_str
    input_str = str_quote_stripper(input_str)
    if '.' not in input_str and input_str in known_mapping_str_to_type:
        return known_mapping_str_to_type[input_str]
    parts = [x.strip() for x in input_str.split('.') if x.strip()]
    try:
        try:
            # first try as a complete module
            package = __import__(input_str)
        except ImportError:
            # it must be a class from a module
            if len(parts) == 1:
                # since it has only one part, it must be a class from __main__
                parts = ('__main__', input_str)
            package = __import__('.'.join(parts[:-1]), globals(), locals(), [])
        obj = package
        for name in parts[1:]:
            obj = getattr(obj, name)
        return obj
    except AttributeError as x:
        raise CannotConvertError("%s cannot be found" % input_str)
    except ImportError as x:
        raise CannotConvertError(str(x))

class_converter = str_to_python_object  # for backward compatibility


#------------------------------------------------------------------------------
def str_to_classes_in_namespaces(
    template_for_namespace="cls%d",
    name_of_class_option='cls',
    instantiate_classes=False
):
    """take a comma delimited  list of class names, convert each class name
    into an actual class as an option within a numbered namespace.  This
    function creates a closure over a new function.  That new function,
    in turn creates a class derived from RequiredConfig.  The inner function,
    'class_list_converter', populates the InnerClassList with a Namespace for
    each of the classes in the class list.  In addition, it puts the each class
    itself into the subordinate Namespace.  The requirement discovery mechanism
    of configman then reads the InnerClassList's requried config, pulling in
    the namespaces and associated classes within.

    For example, if we have a class list like this: "Alpha, Beta", then this
    converter will add the following Namespaces and options to the
    configuration:

        "cls0" - the subordinate Namespace for Alpha
        "cls0.cls" - the option containing the class Alpha itself
        "cls1" - the subordinate Namespace for Beta
        "cls1.cls" - the option containing the class Beta itself

    Optionally, the 'class_list_converter' inner function can embue the
    InnerClassList's subordinate namespaces with aggregates that will
    instantiate classes from the class list.  This is a convenience to the
    programmer who would otherwise have to know ahead of time what the
    namespace names were so that the classes could be instantiated within the
    context of the correct namespace.  Remember the user could completely
    change the list of classes at run time, so prediction could be difficult.

        "cls0" - the subordinate Namespace for Alpha
        "cls0.cls" - the option containing the class Alpha itself
        "cls0.cls_instance" - an instance of the class Alpha
        "cls1" - the subordinate Namespace for Beta
        "cls1.cls" - the option containing the class Beta itself
        "cls1.cls_instance" - an instance of the class Beta

    parameters:
        template_for_namespace - a template for the names of the namespaces
                                 that will contain the classes and their
                                 associated required config options.  The
                                 namespaces will be numbered sequentially.  By
                                 default, they will be "cls1", "cls2", etc.
        class_option_name - the name to be used for the class option within
                            the nested namespace.  By default, it will choose:
                            "cls1.cls", "cls2.cls", etc.
        instantiate_classes - a boolean to determine if there should be an
                              aggregator added to each namespace that
                              instantiates each class.  If True, then each
                              Namespace will contain elements for the class, as
                              well as an aggregator that will instantiate the
                              class.
                              """

    # these are only used within this method.  No need to pollute the module
    # scope with them and avoid potential circular imports
    from configman.namespace import Namespace
    from configman.required_config import RequiredConfig

    #--------------------------------------------------------------------------
    def class_list_converter(class_list_str):
        """This function becomes the actual converter used by configman to
        take a string and convert it into the nested sequence of Namespaces,
        one for each class in the list.  It does this by creating a proxy
        class stuffed with its own 'required_config' that's dynamically
        generated."""
        if isinstance(class_list_str, six.string_types):
            class_list = [x.strip() for x in class_list_str.split(',')]
            if class_list == ['']:
                class_list = []
        else:
            raise TypeError('must be derivative of %s' % six.string_types)

        #======================================================================
        class InnerClassList(RequiredConfig):
            """This nested class is a proxy list for the classes.  It collects
            all the config requirements for the listed classes and places them
            each into their own Namespace.
            """
            # we're dynamically creating a class here.  The following block of
            # code is actually adding class level attributes to this new class
            required_config = Namespace()  # 1st requirement for configman
            subordinate_namespace_names = []  # to help the programmer know
                                              # what Namespaces we added
            namespace_template = template_for_namespace  # save the template
                                                         # for future reference
            class_option_name = name_of_class_option  # save the class's option
                                                      # name for the future
            # for each class in the class list
            for namespace_index, a_class in enumerate(class_list):
                # figure out the Namespace name
                namespace_name = template_for_namespace % namespace_index
                subordinate_namespace_names.append(namespace_name)
                # create the new Namespace
                required_config[namespace_name] = Namespace()
                # add the option for the class itself
                required_config[namespace_name].add_option(
                    name_of_class_option,
                    #doc=a_class.__doc__  # not helpful if too verbose
                    default=a_class,
                    from_string_converter=class_converter
                )
                if instantiate_classes:
                    # add an aggregator to instantiate the class
                    required_config[namespace_name].add_aggregation(
                        "%s_instance" % name_of_class_option,
                        lambda c, lc, a: lc[name_of_class_option](lc)
                    )

            @classmethod
            def to_str(cls):
                """this method takes this inner class object and turns it back
                into the original string of classnames.  This is used
                primarily as for the output of the 'help' option"""
                return ', '.join(
                    py_obj_to_str(v[name_of_class_option].value)
                    for v in cls.get_required_config().values()
                    if isinstance(v, Namespace)
                )

        return InnerClassList  # result of class_list_converter
    return class_list_converter  # result of classes_in_namespaces_converter

# for backward compatibility
classes_in_namespaces_converter = str_to_classes_in_namespaces


#------------------------------------------------------------------------------
def str_to_regular_expression(input_str):
    return re.compile(input_str)

regex_converter = str_to_regular_expression  # for backward compatibility

compiled_regexp_type = type(re.compile(r'x'))


#------------------------------------------------------------------------------
def str_to_list(
    input_str,
    item_converter=lambda x: x,
    item_separator=',',
    list_to_collection_converter=None,
):
    """ a conversion function for list
    """
    if not isinstance(input_str, six.string_types):
        raise ValueError(input_str)
    input_str = str_quote_stripper(input_str)
    result = [
        item_converter(x.strip())
        for x in input_str.split(item_separator) if x.strip()
    ]
    if list_to_collection_converter is not None:
        return list_to_collection_converter(result)
    return result

list_converter = str_to_list  # for backward compatibility


#------------------------------------------------------------------------------
#
#   To string section
#
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
str_to_instance_of_type_converters = {
    int: int,
    float: float,
    str: str,
    bool: boolean_converter,
    dict: json.loads,
    list: list_converter,
    datetime.datetime: datetime_converter,
    datetime.date: date_converter,
    datetime.timedelta: timedelta_converter,
    type: class_converter,
    types.FunctionType: class_converter,
    compiled_regexp_type: regex_converter,
}
if six.PY2:
    str_to_instance_of_type_converters[six.text_type] = py2_to_unicode
if six.PY3:
    str_to_instance_of_type_converters[six.binary_type] = py3_to_bytes

 # backward compatibility
from_string_converters = str_to_instance_of_type_converters


#------------------------------------------------------------------------------
def arbitrary_object_to_string(a_thing):
    """take a python object of some sort, and convert it into a human readable
    string.  this function is used extensively to convert things like "subject"
    into "subject_key, function -> function_key, etc."""
    # is it None?
    if a_thing is None:
        return ''
    # is it already a string?
    if isinstance(a_thing, six.string_types):
        return a_thing
    if six.PY3 and isinstance(a_thing, six.binary_type):
        try:
            return a_thing.decode('utf-8')
        except UnicodeDecodeError:
            pass
    # does it have a to_str function?
    try:
        return a_thing.to_str()
    except (AttributeError, KeyError, TypeError):
        # AttributeError - no to_str function?
        # KeyError - DotDict has no to_str?
        # TypeError - problem converting
        # nope, no to_str function
        pass
    # is this a type proxy?
    try:
        return arbitrary_object_to_string(a_thing.a_type)
    except (AttributeError, KeyError, TypeError):
        #
        # nope, no a_type property
        pass
    # is it a built in?
    try:
        return known_mapping_type_to_str[a_thing]
    except (KeyError, TypeError):
        # nope, not a builtin
        pass
    # is it something from a loaded module?
    try:
        if a_thing.__module__ not in ('__builtin__', 'builtins', 'exceptions'):
            if a_thing.__module__ == "__main__":
                module_name = (
                    sys.modules['__main__']
                    .__file__[:-3]
                    .replace('/', '.')
                    .strip('.')
                )
            else:
                module_name = a_thing.__module__
            return "%s.%s" % (module_name, a_thing.__name__)
    except AttributeError:
        # nope, not one of these
        pass
    # maybe it has a __name__ attribute?
    try:
        return a_thing.__name__
    except AttributeError:
        # nope, not one of these
        pass
    # punt and see what happens if we just cast it to string
    return str(a_thing)


py_obj_to_str = arbitrary_object_to_string  # for backwards compatibility


#------------------------------------------------------------------------------
def list_to_str(a_list, delimiter=', '):
    return delimiter.join(to_str(x) for x in a_list)


#------------------------------------------------------------------------------
def py2_to_str(a_unicode):
    return six.text_type(a_unicode)

def py3_to_str(a_bytes):
    return a_bytes.decode('utf-8')

#------------------------------------------------------------------------------
known_mapping_type_to_str = {}
for key, val in sorted(builtins.__dict__.items()):
    if val not in (True, False, list, dict):
        try:
            known_mapping_type_to_str[val] = key
        except TypeError:
            pass


#------------------------------------------------------------------------------
to_string_converters = {
    int: str,
    float: str,
    str: str,
    list: list_to_str,
    tuple: list_to_str,
    bool: lambda x: 'True' if x else 'False',
    dict: json.dumps,
    datetime.datetime: datetime_to_ISO_string,
    datetime.date: date_to_ISO_string,
    datetime.timedelta: timedelta_to_str,
    type: arbitrary_object_to_string,
    types.ModuleType: arbitrary_object_to_string,
    types.FunctionType: arbitrary_object_to_string,
    compiled_regexp_type: lambda x: x.pattern,
}
if six.PY2:
    to_string_converters[six.text_type] = py2_to_str
if six.PY3:
    to_string_converters[six.binary_type] = py3_to_str


#------------------------------------------------------------------------------
def to_str(a_thing):
    try:
        return to_string_converters[type(a_thing)](a_thing)
    except KeyError:
        return arbitrary_object_to_string(a_thing)

#------------------------------------------------------------------------------
converters_requiring_quotes = [eval, regex_converter]
