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
