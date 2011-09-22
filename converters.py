import sys
import re
import datetime
import types
import inspect

import datetime_util as dtu


#------------------------------------------------------------------------------
def io_converter(input_str):
    """ a conversion function for to select stdout, stderr or open a file for
    writing"""
    if type(input_str) is str:
        input_str_lower = input_str.lower()
        if input_str_lower == 'stdout':
            return sys.stdout
        if input_str_lower == 'stderr':
            return sys.stderr
        return open(input_str, "w")
    return input_str


#------------------------------------------------------------------------------
#def datetime_converter(input_str):
#    """ a conversion function for datetimes
#    """
#    try:
#        if type(input_str) is str:
#            year = int(input_str[:4])
#            month = int(input_str[5:7])
#            day = int(input_str[8:10])
#            hour = 0
#            minute = 0
#            second = 0
#            try:
#                hour = int(input_str[11:13])
#                minute = int(input_str[14:16])
#                second = int(input_str[17:19])
#            except ValueError:
#                pass
#            return datetime.datetime(year, month, day, hour, minute, second)
#        return input_str
#    except Exception:
#        return datetime.datetime.now()


#------------------------------------------------------------------------------
def timedelta_converter(input_str):
    """a conversion function for time deltas"""
    if isinstance(input_str, basestring):
        days, hours, minutes, seconds = 0, 0, 0, 0
        details = input_str.split(':')
        if len(details) >= 4:
            days = int(details[-4])
        if len(details) >= 3:
            hours = int(details[-3])
        if len(details) >= 2:
            minutes = int(details[-2])
        if len(details) >= 1:
            seconds = int(details[-1])
        return datetime.timedelta(days=days,
                                      hours=hours,
                                      minutes=minutes,
                                      seconds=seconds)
    raise ValueError(input_str)


#------------------------------------------------------------------------------
def boolean_converter(input_str):
    """ a conversion function for boolean
    """
    return input_str.lower() in ("true", "t", "1", "y", "yes")


#------------------------------------------------------------------------------
import __builtin__  # FIXME: there has to be a better way to do this
_all_named_builtins = dir(__builtin__)


def class_converter(input_str):
    """ a conversion that will import a module and class name
    """
    if not input_str:
        return None
    if '.' not in input_str and input_str in _all_named_builtins:
        return eval(input_str)
    parts = input_str.split('.')
    try:
        # first try as a complete module
        package = __import__(input_str)
    except ImportError:
        # it must be a class from a module
        package = __import__('.'.join(parts[:-1]), globals(), locals(), [])
    obj = package
    for name in parts[1:]:
        obj = getattr(obj, name)
    return obj


#------------------------------------------------------------------------------
def regex_converter(input_str):
    return re.compile(input_str)

compiled_regexp_type = type(re.compile(r'x'))

#------------------------------------------------------------------------------
from_string_converters = {int: int,
                          float: float,
                          str: str,
                          unicode: unicode,
                          bool: boolean_converter,
                          datetime.datetime: dtu.datetime_from_ISO_string,
                          datetime.date: dtu.date_from_ISO_string,
                          datetime.timedelta: timedelta_converter,
                          type: class_converter,
                          types.FunctionType: class_converter,
                          compiled_regexp_type: regex_converter,
                          }


#------------------------------------------------------------------------------
def classes_and_functions_to_str(a_thing):
    if a_thing is None:
        return ''
    if inspect.ismodule(a_thing):
        return a_thing.__name__
    if a_thing.__module__ == '__builtin__':
        return a_thing.__name__
    return "%s.%s" % (a_thing.__module__, a_thing.__name__)


#------------------------------------------------------------------------------
to_string_converters = {int: str,
                        float: str,
                        str: str,
                        unicode: unicode,
                        bool: lambda x: 'True' if x else 'False',
                        datetime.datetime: dtu.datetime_to_ISO_string,
                        datetime.date: dtu.date_to_ISO_string,
                        datetime.timedelta: dtu.timedelta_to_str,
                        type: classes_and_functions_to_str,
                        types.FunctionType: classes_and_functions_to_str,
                        compiled_regexp_type: lambda x: x.pattern,
                        }


#------------------------------------------------------------------------------
#converters_requiring_quotes = [eval, eval_to_regex_converter]
converters_requiring_quotes = [eval, regex_converter]
