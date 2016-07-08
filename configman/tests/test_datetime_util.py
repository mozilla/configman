# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function

import unittest
import datetime
import configman.datetime_util as datetime_util


#==============================================================================
class TestCase(unittest.TestCase):

    #--------------------------------------------------------------------------
    def test_datetime_from_ISO_string(self):
        function = datetime_util.datetime_from_ISO_string

        inp = '2011-05-04T15:10:00'
        out = function(inp)
        self.assertTrue(isinstance(out, datetime.datetime))
        self.assertEqual(out.strftime('%Y-%m-%dT%H:%M:%S'), inp)

        inp = '2011-05-04'
        out = function(inp)
        self.assertTrue(isinstance(out, datetime.datetime))
        self.assertEqual(out.strftime('%Y-%m-%dT%H:%M:%S'), inp + 'T00:00:00')

        inp = '2011-05-04T15:10:00.666000'
        out = function(inp)
        self.assertTrue(isinstance(out, datetime.datetime))
        self.assertEqual(out.microsecond, 666000)
        self.assertEqual(out.strftime('%Y-%m-%dT%H:%M:%S.%f'), inp)

        # failing conditions
        self.assertRaises(ValueError, function, '211-05-04T15:10:00')
        self.assertRaises(ValueError, function, '2011-02-30T15:10:00')
        self.assertRaises(ValueError, function, '2011-02-26T24:10:00')
        self.assertRaises(ValueError, function, '2011-02-26T23:10:00.xxx')
        self.assertRaises(ValueError, function, '211-05-32')
        self.assertRaises(ValueError, function, '2011-05-32')

    #--------------------------------------------------------------------------
    def test_date_from_ISO_string(self):
        function = datetime_util.date_from_ISO_string

        inp = '2011-05-04'
        out = function(inp)
        self.assertTrue(isinstance(out, datetime.date))
        self.assertEqual(out.strftime('%Y-%m-%d'), inp)

        inp = '2011-1-2'
        out = function(inp)
        self.assertTrue(isinstance(out, datetime.date))
        self.assertEqual(out.month, 1)
        self.assertEqual(out.day, 2)

        # failing conditions
        self.assertRaises(ValueError, function, '2011-05-04T15:10:00')
        self.assertRaises(ValueError, function, '211-05-04')
        self.assertRaises(ValueError, function, '2011-05-32')

    #--------------------------------------------------------------------------
    def test_hours_str_to_timedelta(self):
        function = datetime_util.hours_str_to_timedelta
        self.assertEqual(function(1), datetime.timedelta(hours=1))

    #--------------------------------------------------------------------------
    def test_date_to_ISO_string(self):
        function = datetime_util.date_to_ISO_string
        d = datetime.datetime.now()
        self.assertEqual(
            function(d),
            d.strftime('%Y-%m-%d')
        )

        d = datetime.date.today()
        self.assertEqual(
            function(d),
            d.strftime('%Y-%m-%d')
        )

    #--------------------------------------------------------------------------
    def test_timedelta_to_seconds(self):
        function = datetime_util.timedelta_to_seconds
        self.assertEqual(function(datetime.timedelta(hours=1)), 3600)
        self.assertEqual(function(datetime.timedelta(hours=2)), 2 * 3600)
        self.assertEqual(function(datetime.timedelta(minutes=1)), 60)
        self.assertEqual(function(datetime.timedelta(seconds=1)), 1)

    #--------------------------------------------------------------------------
    def test_str_to_timedelta(self):
        function = datetime_util.str_to_timedelta
        self.assertEqual(
            function('1:1:1:01'),
            datetime.timedelta(
                days=1,
                hours=1,
                minutes=1,
                seconds=1
            )
        )
        self.assertEqual(
            function('2 00:00:00'),
            datetime.timedelta(
                days=2,
            )
        )
        self.assertEqual(
            function('01:01:01:01'),
            datetime.timedelta(
                days=1,
                hours=1,
                minutes=1,
                seconds=1
            )
        )
        self.assertEqual(
            function('1:1:1:01'),
            datetime.timedelta(
                days=1,
                hours=1,
                minutes=1,
                seconds=1
            )
        )
        self.assertEqual(
            function('1:1:1'),
            datetime.timedelta(
                hours=1,
                minutes=1,
                seconds=1
            )
        )
        self.assertEqual(
            function('1:1'),
            datetime.timedelta(
                minutes=1,
                seconds=1
            )
        )
        self.assertEqual(
            function('1'),
            datetime.timedelta(seconds=1)
        )
        self.assertRaises(ValueError, function, 'not a number')
        self.assertEqual(
            function('1'),
            datetime.timedelta(seconds=1)
        )
        self.assertRaises(TypeError, function, 10.1)
