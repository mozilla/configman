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
import datetime
import configman.datetime_util as datetime_util


class TestCase(unittest.TestCase):

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

    def test_hours_str_to_timedelta(self):
        function = datetime_util.hours_str_to_timedelta
        self.assertEqual(function(1), datetime.timedelta(hours=1))

    def test_date_to_ISO_string(self):
        function = datetime_util.date_to_ISO_string
        d = datetime.datetime.now()
        self.assertEqual(function(d),
                         d.strftime('%Y-%m-%d'))

        d = datetime.date.today()
        self.assertEqual(function(d),
                         d.strftime('%Y-%m-%d'))

    def test_timedelta_to_seconds(self):
        function = datetime_util.timedelta_to_seconds
        self.assertEqual(function(datetime.timedelta(hours=1)), 3600)
        self.assertEqual(function(datetime.timedelta(hours=2)), 2 * 3600)
        self.assertEqual(function(datetime.timedelta(minutes=1)), 60)
        self.assertEqual(function(datetime.timedelta(seconds=1)), 1)

    def test_str_to_timedelta(self):
        function = datetime_util.str_to_timedelta
        self.assertEqual(function('1:1:1:01'),
                         datetime.timedelta(days=1,
                                            hours=1,
                                            minutes=1,
                                            seconds=1))

        self.assertEqual(function('1:1:1'),
                         datetime.timedelta(hours=1,
                                            minutes=1,
                                            seconds=1))

        self.assertEqual(function('1:1'),
                         datetime.timedelta(minutes=1,
                                            seconds=1))

        self.assertEqual(function('1'),
                         datetime.timedelta(seconds=1))
        self.assertRaises(ValueError, function, 'not a number')
