import unittest
from configman.dotdict import DotDict


class TestCase(unittest.TestCase):

    def test_setting_and_getting(self):
        dd = DotDict()
        dd.name = u'Peter'
        dd['age'] = 31
        setattr(dd, 'gender', 'male')

        self.assertEqual(dd['name'], u'Peter')
        self.assertEqual(dd.age, 31)
        self.assertEqual(dd['gender'], dd.gender)
        self.assertEqual(dd.get('name'), u'Peter')
        self.assertEqual(getattr(dd, 'gender'), 'male')
        self.assertEqual(dd.get('gender'), 'male')
        self.assertEqual(dd.get('junk'), None)
        self.assertEqual(dd.get('junk', 'trash'), 'trash')

    def test_deleting_attributes(self):
        dd = DotDict()
        dd.name = 'peter'
        dd.age = 31
        del dd.name
        del dd.age
        self.assertEqual(dict(dd), {})

    def test_key_errors(self):
        dd = DotDict()

        try:
            dd['name']
            raise AssertionError("should have raised KeyError")
        except KeyError:
            pass

        try:
            dd.age
            raise AssertionError("should have raised KeyError")
        except KeyError:
            pass

        try:
            getattr(dd, 'name')
            raise AssertionError("should have raised KeyError")
        except KeyError:
            pass

        self.assertEqual(dd.get('age'), None)
        self.assertEqual(dd.get('age', 0), 0)
