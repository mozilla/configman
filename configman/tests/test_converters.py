import unittest
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

        # FIXME: need a way to test a value whose 'from_string_converter' requires quotes
