import re
import datetime as dt
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
def datetime_converter(input_str):
    """ a conversion function for datetimes
    """
    try:
        if type(input_str) is str:
            year = int(input_str[:4])
            month = int(input_str[5:7])
            day = int(input_str[8:10])
            hour = 0
            minute = 0
            second = 0
            try:
                hour = int(input_str[11:13])
                minute = int(input_str[14:16])
                second = int(input_str[17:19])
            except ValueError:
                pass
            return dt.datetime(year, month, day, hour, minute, second)
        return input_str
    except Exception:
        return dt.datetime.now()


#------------------------------------------------------------------------------
def timedelta_converter(input_str):
    """ a conversion function for time deltas
    """
    try:
        if type(input_str) is str:
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
            return dt.timedelta(days=days,
                                hours=hours,
                                minutes=minutes,
                                seconds=seconds)
    except ValueError:
        pass
    return input_str


#------------------------------------------------------------------------------
def boolean_converter(input_str):
    """ a conversion function for boolean
    """
    if type(input_str) is str:
        return input_str.lower() in ("true", "t", "1")
    return input_str


#------------------------------------------------------------------------------
def class_converter(input_str):
    """ a conversion that will import a module and class name
    """
    if not input_str:
        return None
    parts = input_str.split('.')
    try:
        # first try as a complete module
        package = __import__(input_str)
    except ImportError:
        if len(parts) == 1:
            # maybe this is a builtin
            return eval(input_str)
        # it must be a class from a module
        package = __import__('.'.join(parts[:-1]), globals(), locals(), [])
    obj = package
    for name in parts[1:]:
        obj = getattr(obj, name)
    return obj


#------------------------------------------------------------------------------
def eval_to_regex_converter(input_str):
    regex_as_str = eval(input_str)
    return re.compile(regex_as_str)

compiled_regexp_type = type(re.compile(r'x'))

#------------------------------------------------------------------------------
from_string_converters = {int: int,
                          float: float,
                          str: str,
                          unicode: unicode,
                          bool: boolean_converter,
                          dt.datetime: datetime_converter,
                          dt.timedelta: timedelta_converter,
                          type: class_converter,
                          types.FunctionType: class_converter,
                          compiled_regexp_type: eval_to_regex_converter,
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
                        dt.datetime: dtu.datetime_to_ISO_string,
                        dt.timedelta: dtu.timedelta_to_str,
                        type: classes_and_functions_to_str,
                        types.FunctionType: classes_and_functions_to_str,
                        compiled_regexp_type: lambda x: x.pattern,
                        }


#------------------------------------------------------------------------------
converters_requiring_quotes = [eval, eval_to_regex_converter]


