import unittest
import datetime
import datetime_util


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
