import unittest
import tempfile
from configman import converters


class TestCase(unittest.TestCase):

    def test_str_dict_keys(self):
        function = converters.str_dict_keys
        result = function({u'name': u'Peter', 'age': 99, 10: 11})
        self.assertEqual(result,
          {'name': u'Peter', 'age': 99, 10: 11})

        for key in result.keys():
            if key in ('name', 'age'):
                self.assertTrue(not isinstance(key, unicode))
                self.assertTrue(isinstance(key, str))
            else:
                self.assertTrue(isinstance(key, int))

    def test_option_value_str(self):
        function = converters.option_value_str

        class _Option(object):
            def __init__(self, value=None, from_string_converter=None):
                self.value = value
                self.from_string_converter = from_string_converter

        opt = _Option()
        self.assertEqual(function(opt), '')
        opt = _Option(3.14)
        self.assertEqual(function(opt), '3.14')

        from decimal import Decimal
        opt = _Option(Decimal('3.14'))
        self.assertEqual(function(opt), '3.14')

        # FIXME: need a way to test a value whose 'from_string_converter'
        # requires quotes

    def test_io_converter(self):
        function = converters.io_converter
        import sys
        import os
        self.assertEqual(function(100.0), 100.0)
        self.assertEqual(function('stdout'), sys.stdout)
        self.assertEqual(function('STDOut'), sys.stdout)
        self.assertEqual(function('Stderr'), sys.stderr)
        tmp_filename = os.path.join(tempfile.gettempdir(), 'test.anything')
        try:

            r = function(tmp_filename)
            self.assertTrue(hasattr(r, 'write'))
            self.assertTrue(hasattr(r, 'close'))
            r.write('stuff\n')
            r.close()
            self.assertEqual(open(tmp_filename).read(), 'stuff\n')
        finally:
            if os.path.isfile(tmp_filename):
                os.remove(tmp_filename)

    def test_timedelta_converter(self):
        function = converters.timedelta_converter
        from datetime import timedelta
        self.assertEqual(function('1'), timedelta(seconds=1))
        self.assertEqual(function('2:1'), timedelta(minutes=2, seconds=1))
        self.assertEqual(function('3:2:1'),
                         timedelta(hours=3, minutes=2, seconds=1))
        self.assertEqual(function('4:3:2:1'),
                         timedelta(days=4, hours=3, minutes=2, seconds=1))
        self.assertRaises(ValueError, function, 'xxx')
        self.assertRaises(ValueError, function, 10.1)

    def test_class_converter_nothing(self):
        function = converters.class_converter
        self.assertEqual(function(''), None)

    def test_py_obj_to_str(self):
        function = converters.py_obj_to_str
        self.assertEqual(function(None), '')
        from configman import tests as tests_module
        self.assertEqual(function(tests_module), 'configman.tests')
        self.assertEqual(function(int), 'int')
