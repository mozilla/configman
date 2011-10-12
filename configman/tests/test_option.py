import unittest
import re
import datetime

import configman.config_manager as config_manager
import configman.converters as conv
import configman.datetime_util as dtu
from configman.option import Option
from configman.config_exceptions import CannotConvertError


class TestCase(unittest.TestCase):

    def test_option_constructor_basics(self):
        o = Option('name')
        self.assertEqual(o.name, 'name')
        self.assertEqual(o.default, None)
        self.assertEqual(o.doc, None)
        self.assertEqual(o.from_string_converter, None)
        self.assertEqual(o.value, None)

        o = Option('lucy')
        self.assertEqual(o.name, 'lucy')
        self.assertEqual(o.default, None)
        self.assertEqual(o.doc, None)
        self.assertEqual(o.from_string_converter, None)
        self.assertEqual(o.value, None)

        o = Option(u'spa\xa0e')
        self.assertEqual(o.name, u'spa\xa0e')
        self.assertEqual(o.default, None)
        self.assertEqual(o.doc, None)
        self.assertEqual(o.from_string_converter, None)
        self.assertEqual(o.value, None)

        data = {
          'name': 'lucy',
          'default': 1,
          'doc': "lucy's integer"
        }
        o = Option(**data)
        self.assertEqual(o.name, 'lucy')
        self.assertEqual(o.default, 1)
        self.assertEqual(o.doc, "lucy's integer")
        self.assertEqual(o.from_string_converter, int)
        self.assertEqual(o.value, 1)

        data = {
          'name': 'lucy',
          'default': 1,
          'doc': "lucy's integer",
          'value': '1'
        }
        o = Option(**data)
        self.assertEqual(o.name, 'lucy')
        self.assertEqual(o.default, 1)
        self.assertEqual(o.doc, "lucy's integer")
        self.assertEqual(o.from_string_converter, int)
        self.assertEqual(o.value, 1)

        data = {
          'name': 'lucy',
          'default': '1',
          'doc': "lucy's integer",
          'from_string_converter': int
        }
        o = Option(**data)
        self.assertEqual(o.name, 'lucy')
        self.assertEqual(o.default, '1')
        self.assertEqual(o.doc, "lucy's integer")
        self.assertEqual(o.from_string_converter, int)
        self.assertEqual(o.value, 1)

        data = {
          'name': 'lucy',
          'default': '1',
          'doc': "lucy's integer",
          'from_string_converter': int,
          'other': 'no way'
        }
        o = Option(**data)
        self.assertEqual(o.name, 'lucy')
        self.assertEqual(o.default, '1')
        self.assertEqual(o.doc, "lucy's integer")
        self.assertEqual(o.from_string_converter, int)
        self.assertEqual(o.value, 1)

        data = {
          'default': '1',
          'doc': "lucy's integer",
          'from_string_converter': int,
          'other': 'no way'
        }
        o = Option('now', **data)
        self.assertEqual(o.name, 'now')
        self.assertEqual(o.default, '1')
        self.assertEqual(o.doc, "lucy's integer")
        self.assertEqual(o.from_string_converter, int)
        self.assertEqual(o.value, 1)

        d = datetime.datetime.now()
        o = Option('now', default=d)
        self.assertEqual(o.name, 'now')
        self.assertEqual(o.default, d)
        self.assertEqual(o.doc, None)
        self.assertEqual(o.from_string_converter,
                         dtu.datetime_from_ISO_string)
        self.assertEqual(o.value, d)

    def test_setting_known_from_string_converter_onOption(self):
        opt = Option('name', default=u'Peter')
        self.assertEqual(opt.default, u'Peter')
        self.assertEqual(opt.from_string_converter, unicode)

        opt = Option('name', default=100)
        self.assertEqual(opt.default, 100)
        self.assertEqual(opt.from_string_converter, int)

        opt = Option('name', default=100L)
        self.assertEqual(opt.default, 100L)
        self.assertEqual(opt.from_string_converter, long)

        opt = Option('name', default=100.0)
        self.assertEqual(opt.default, 100.0)
        self.assertEqual(opt.from_string_converter, float)

        from decimal import Decimal
        opt = Option('name', default=Decimal('100.0'))
        self.assertEqual(opt.default, Decimal('100.0'))
        self.assertEqual(opt.from_string_converter, Decimal)

        opt = Option('name', default=False)
        self.assertEqual(opt.default, False)
        self.assertEqual(opt.from_string_converter,
                         conv.boolean_converter)

        dt = datetime.datetime(2011, 8, 10, 0, 0, 0)
        opt = Option('name', default=dt)
        self.assertEqual(opt.default, dt)
        self.assertEqual(opt.from_string_converter,
                         dtu.datetime_from_ISO_string)

        dt = datetime.date(2011, 8, 10)
        opt = Option('name', default=dt)
        self.assertEqual(opt.default, dt)
        self.assertEqual(opt.from_string_converter,
                         dtu.date_from_ISO_string)

    def test_boolean_converter_inOption(self):
        opt = Option('name', default=False)
        self.assertEqual(opt.default, False)
        self.assertEqual(opt.from_string_converter,
                         conv.boolean_converter)

        opt.set_value('true')
        self.assertEqual(opt.value, True)

        opt.set_value('false')
        self.assertEqual(opt.value, False)

        opt.set_value('1')
        self.assertEqual(opt.value, True)

        opt.set_value('t')
        self.assertEqual(opt.value, True)

        opt.set_value(True)
        self.assertEqual(opt.value, True)

        opt.set_value(False)
        self.assertEqual(opt.value, False)

        opt.set_value('False')
        self.assertEqual(opt.value, False)

        opt.set_value('True')
        self.assertEqual(opt.value, True)

        opt.set_value('None')
        self.assertEqual(opt.value, False)

        opt.set_value('YES')
        self.assertEqual(opt.value, True)

        opt.set_value(u'1')
        self.assertEqual(opt.value, True)

        opt.set_value(u'y')
        self.assertEqual(opt.value, True)

        opt.set_value(u't')
        self.assertEqual(opt.value, True)

    def test_timedelta_converter_inOption(self):
        one_day = datetime.timedelta(days=1)
        opt = Option('some name', default=one_day)
        self.assertEqual(opt.default, one_day)
        self.assertEqual(opt.from_string_converter,
                         conv.timedelta_converter)

        two_days = datetime.timedelta(days=2)
        timedelta_as_string = dtu.timedelta_to_str(two_days)
        assert isinstance(timedelta_as_string, basestring)
        opt.set_value(timedelta_as_string)
        self.assertEqual(opt.value, two_days)

        opt.set_value(unicode(timedelta_as_string))
        self.assertEqual(opt.value, two_days)

        opt.set_value(two_days)
        self.assertEqual(opt.value, two_days)

        self.assertRaises(CannotConvertError,
                          opt.set_value, 'JUNK')

        self.assertRaises(CannotConvertError,
                          opt.set_value, '0:x:0:0')

    def test_regexp_converter_inOption(self):
        regex_str = '\w+'
        sample_regex = re.compile(regex_str)
        opt = Option('name', default=sample_regex)
        self.assertEqual(opt.default, sample_regex)
        self.assertEqual(opt.from_string_converter,
                         conv.regex_converter)

        opt.set_value(regex_str)
        self.assertEqual(opt.value.pattern, sample_regex.pattern)
