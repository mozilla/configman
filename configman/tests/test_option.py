# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function

from decimal import Decimal
import datetime
import unittest
import re
import six

from configman.converters import (
    boolean_converter,
    list_converter,
    timedelta_converter,
    regex_converter,
)
from configman.datetime_util import (
    datetime_from_ISO_string,
    date_from_ISO_string,
    timedelta_to_str,
)

from configman.option import Option
from configman.config_exceptions import CannotConvertError, OptionError


#==============================================================================
class TestCase(unittest.TestCase):

    #--------------------------------------------------------------------------
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
        self.assertEqual(o.value, '1')

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
        self.assertEqual(o.value, '1')
        o.set_value()
        self.assertEqual(o.default, '1')
        self.assertEqual(o.value, 1)

        data = {
            'name': 'lucy',
            'default': '1',
            'doc': "lucy's integer",
            'from_string_converter': int,
        }
        o = Option(**data)
        self.assertEqual(o.name, 'lucy')
        self.assertEqual(o.default, '1')
        self.assertEqual(o.doc, "lucy's integer")
        self.assertEqual(o.from_string_converter, int)
        self.assertEqual(o.value, '1')

        data = {
            'default': '1',
            'doc': "lucy's integer",
            'from_string_converter': int,
        }
        o = Option('now', **data)
        self.assertEqual(o.name, 'now')
        self.assertEqual(o.default, '1')
        self.assertEqual(o.doc, "lucy's integer")
        self.assertEqual(o.from_string_converter, int)
        self.assertEqual(o.value, '1')

        d = datetime.datetime.now()
        o = Option('now', default=d)
        self.assertEqual(o.name, 'now')
        self.assertEqual(o.default, d)
        self.assertEqual(o.doc, None)
        self.assertEqual(o.from_string_converter,
                         datetime_from_ISO_string)
        self.assertEqual(o.value, d)

        data = {
            'default': '1.0',
            'doc': "lucy's height",
            'from_string_converter': float,
        }
        o = Option('now', **data)
        self.assertEqual(o.name, 'now')
        self.assertEqual(o.default, '1.0')
        self.assertEqual(o.doc, "lucy's height")
        self.assertEqual(o.from_string_converter, float)
        self.assertEqual(o.value, '1.0')
        o.set_value()
        self.assertEqual(o.default, '1.0')
        self.assertEqual(o.value, 1.0)

    #--------------------------------------------------------------------------
    def test_option_constructor_more_complex_default_converters(self):
        data = {
            'default': '2011-12-31',
            'doc': "lucy's bday",
            'from_string_converter': date_from_ISO_string,
        }
        o = Option('now', **data)
        self.assertEqual(o.name, 'now')
        self.assertEqual(o.default, '2011-12-31')
        self.assertEqual(o.doc, "lucy's bday")
        self.assertEqual(o.from_string_converter, date_from_ISO_string)
        o.set_value()
        self.assertEqual(o.value, datetime.date(2011, 12, 31))

        data = {
            'default': '2011-12-31',
            'doc': "lucy's bday",
            'from_string_converter':
            'configman.datetime_util.date_from_ISO_string',
        }
        o = Option('now', **data)
        self.assertEqual(o.name, 'now')
        self.assertEqual(o.default, '2011-12-31')
        self.assertEqual(o.doc, "lucy's bday")
        self.assertEqual(o.from_string_converter, date_from_ISO_string)
        self.assertEqual(o.value, '2011-12-31')
        o.set_value()
        self.assertEqual(o.value, datetime.date(2011, 12, 31))

    #--------------------------------------------------------------------------
    def test_setting_known_from_string_converter_onOption(self):
        opt = Option('name', default=u'Peter')
        self.assertEqual(opt.default, u'Peter')
        if six.PY3:
            self.assertEqual(opt.from_string_converter, six.text_type)

        opt = Option('name', default=100)
        self.assertEqual(opt.default, 100)
        self.assertEqual(opt.from_string_converter, int)

        if six.PY2:
            opt = Option('name', default=long(100))
            self.assertEqual(opt.default, long(100))
            self.assertEqual(opt.from_string_converter, long)

        opt = Option('name', default=100.0)
        self.assertEqual(opt.default, 100.0)
        self.assertEqual(opt.from_string_converter, float)

        opt = Option('name', default=Decimal('100.0'))
        self.assertEqual(opt.default, Decimal('100.0'))
        self.assertEqual(opt.from_string_converter, Decimal)

        opt = Option('name', default=False)
        self.assertEqual(opt.default, False)
        self.assertEqual(opt.from_string_converter, boolean_converter)

        dt = datetime.datetime(2011, 8, 10, 0, 0, 0)
        opt = Option('name', default=dt)
        self.assertEqual(opt.default, dt)
        self.assertEqual(opt.from_string_converter,
                         datetime_from_ISO_string)

        dt = datetime.date(2011, 8, 10)
        opt = Option('name', default=dt)
        self.assertEqual(opt.default, dt)
        self.assertEqual(opt.from_string_converter,
                         date_from_ISO_string)

    #--------------------------------------------------------------------------
    def test_boolean_converter_inOption(self):
        opt = Option('name', default=False)
        self.assertEqual(opt.default, False)
        self.assertEqual(opt.from_string_converter,
                         boolean_converter)

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

    #--------------------------------------------------------------------------
    def test_list_converter_inOption(self):
        some_list = ['some', 'values', 'here']
        opt = Option('some name', default=some_list)
        self.assertEqual(opt.default, some_list)
        self.assertEqual(opt.from_string_converter,
                         list_converter)

        opt.set_value('list, of, things')
        self.assertEqual(opt.value, ['list', 'of', 'things'])

    #--------------------------------------------------------------------------
    def test_timedelta_converter_inOption(self):
        one_day = datetime.timedelta(days=1)
        opt = Option('some name', default=one_day)
        self.assertEqual(opt.default, one_day)
        self.assertEqual(opt.from_string_converter,
                         timedelta_converter)

        two_days = datetime.timedelta(days=2)
        timedelta_as_string = timedelta_to_str(two_days)
        assert isinstance(timedelta_as_string, six.string_types)
        opt.set_value(timedelta_as_string)
        self.assertEqual(opt.value, two_days)

        opt.set_value(timedelta_as_string)
        self.assertEqual(opt.value, two_days)

        opt.set_value(two_days)
        self.assertEqual(opt.value, two_days)

        self.assertRaises(CannotConvertError,
                          opt.set_value, 'JUNK')

        self.assertRaises(CannotConvertError,
                          opt.set_value, '0:x:0:0')

    #--------------------------------------------------------------------------
    def test_regexp_converter_inOption(self):
        regex_str = '\w+'
        sample_regex = re.compile(regex_str)
        opt = Option('name', default=sample_regex)
        self.assertEqual(opt.default, sample_regex)
        self.assertEqual(opt.from_string_converter,
                         regex_converter)

        opt.set_value(regex_str)
        self.assertEqual(opt.value.pattern, sample_regex.pattern)

    #--------------------------------------------------------------------------
    def test_option_comparison(self):
        o1 = Option('name')
        o2 = Option('name')
        self.assertEqual(o1, o2)

        o1 = Option('name', 'Peter')
        o2 = Option('name', u'Peter')
        self.assertEqual(o1, o2)

        o1 = Option('name', 'Peter')
        o2 = Option('name', 'Ashley')
        self.assertNotEqual(o1, o2)

        o1 = Option('name', doc='Aaa')
        o2 = Option('name', doc='Bee')
        self.assertNotEqual(o1, o2)

        o1 = Option('name', doc='Aaa')
        o2 = Option('name', doc='Aaa')
        self.assertEqual(o1, o2)

        o1 = Option('name', doc='Aaa', short_form='n')
        o2 = Option('name', doc='Aaa', short_form='N')
        self.assertNotEqual(o1, o2)

        o1 = Option('name')
        o1.set_value('Peter')
        o2 = Option('name')
        self.assertNotEqual(o1, o2)

    #--------------------------------------------------------------------------
    def test_set_value_from_other_option(self):
        o1 = Option('name')
        o1.set_value('Peter')
        o2 = Option('name')
        o2.set_value(o1)
        self.assertEqual(o2.value, None)

        o1 = Option('name', default='Your name here')
        o1.set_value('Peter')
        o2 = Option('name')
        o2.set_value(o1)
        self.assertEqual(o2.value, 'Your name here')

    #--------------------------------------------------------------------------
    def test_set_value_from_mapping(self):
        o1 = Option('name')
        val = {'default': u'Peter'}
        o1.set_value(val)
        self.assertEqual(o1.value, 'Peter')

        val = {'justanother': 'dict!'}
        o1.set_value(val)
        self.assertEqual(o1.value, val)

    #--------------------------------------------------------------------------
    def test_set_default(self):
        o1 = Option(
            'name',
            default=23
        )
        self.assertEqual(o1.value, 23)
        self.assertRaises(OptionError, o1.set_default, 68)
        o1.set_default(78, force=True)
        self.assertTrue(o1.value, 68)
        self.assertTrue(o1.default, 68)

        o2 = Option(
            'name',
            default=None
        )
        self.assertTrue(o2.value is None)
        o2.set_default(68)
        self.assertTrue(o2.value, 68)
        self.assertTrue(o2.default, 68)

    #--------------------------------------------------------------------------
    def test__str__(self):
        opt = Option('name')
        self.assertEqual(str(opt), '')
        opt = Option('name', 3.14)
        self.assertEqual(str(opt), '3.14')

        opt = Option('name', Decimal('3.14'))
        self.assertEqual(str(opt), '3.14')

        opt = Option(
            'name',
            [['one', 'One'], ['two', 'Two']],
            to_string_converter=lambda seq: ', '.join(
                '%s: %s' % (a, b) for (a, b) in seq
            )
        )
        self.assertEqual(str(opt), 'one: One, two: Two')

        # FIXME: need a way to test a value whose 'from_string_converter'
        # requires quotes

    #--------------------------------------------------------------------------
    def test_reference_value_from(self):
        o1 = Option(
            name='fred',
            reference_value_from='external.postgresql'
        )
        self.assertEqual(o1.reference_value_from, 'external.postgresql')

    #--------------------------------------------------------------------------
    def test_copy(self):
        o = Option(
            name='dwight',
            default=17,
            doc='the doc',
            from_string_converter=int,
            value=0,
            short_form='d',
            exclude_from_print_conf=True,
            exclude_from_dump_conf=True,
            is_argument=False,
            likely_to_be_changed=False,
            not_for_definition=False,
            reference_value_from='external.postgresql',
            secret=True,
        )
        o2 = o.copy()
        self.assertEqual(o, o2)
