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

import unittest
import re
import datetime

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
        self.assertEqual(o.default, 1)  # converted using `int`
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
        self.assertEqual(o.default, 1)
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
        self.assertEqual(o.default, 1)
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

        data = {
          'default': '1.0',
          'doc': "lucy's height",
          'from_string_converter': float,
          'other': ''
        }
        o = Option('now', **data)
        self.assertEqual(o.name, 'now')
        self.assertEqual(o.default, 1.0)
        self.assertEqual(o.doc, "lucy's height")
        self.assertEqual(o.from_string_converter, float)
        self.assertEqual(o.value, 1.0)

    def test_option_constructor_more_complex_default_converters(self):
        data = {
          'default': '2011-12-31',
          'doc': "lucy's bday",
          'from_string_converter': dtu.date_from_ISO_string,
          'other': ''
        }
        o = Option('now', **data)
        self.assertEqual(o.name, 'now')
        self.assertEqual(o.default, datetime.date(2011, 12, 31))
        self.assertEqual(o.doc, "lucy's bday")
        self.assertEqual(o.from_string_converter, dtu.date_from_ISO_string)
        self.assertEqual(o.value, datetime.date(2011, 12, 31))

        data = {
          'default': '2011-12-31',
          'doc': "lucy's bday",
          'from_string_converter': \
            'configman.datetime_util.date_from_ISO_string',
          'other': ''
        }
        o = Option('now', **data)
        self.assertEqual(o.name, 'now')
        self.assertEqual(o.default, datetime.date(2011, 12, 31))
        self.assertEqual(o.doc, "lucy's bday")
        self.assertEqual(o.from_string_converter, dtu.date_from_ISO_string)
        self.assertEqual(o.value, datetime.date(2011, 12, 31))

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

    def test_set_value_from_mapping(self):
        o1 = Option('name')
        val = {'default': u'Peter'}
        o1.set_value(val)
        self.assertEqual(o1.value, 'Peter')

        val = {'justanother': 'dict!'}
        o1.set_value(val)
        self.assertEqual(o1.value, val)
