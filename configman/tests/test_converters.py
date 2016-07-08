# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest
import datetime
import six

from configman import converters
from configman import RequiredConfig, Namespace, ConfigurationManager
from configman.dotdict import DotDict


#==============================================================================
# the following two classes are used in test_classes_in_namespaces_converter1
# and need to be declared at module level scope
class Foo(RequiredConfig):
    required_config = Namespace()
    required_config.add_option('x', default=17)
    required_config.add_option('y', default=23)


#==============================================================================
class Bar(RequiredConfig):
    required_config = Namespace()
    required_config.add_option('x', default=227)
    required_config.add_option('a', default=11)


# the following two classes are used in test_classes_in_namespaces_converter2
# and test_classes_in_namespaces_converter_3.  They need to be declared at
#module level scope
#==============================================================================
class Alpha(RequiredConfig):
    required_config = Namespace()
    required_config.add_option('a', doc='a', default=17)

    #--------------------------------------------------------------------------
    def __init__(self, config):
        self.config = config
        self.a = config.a

    #--------------------------------------------------------------------------
    def to_str(self):
        return "I am an instance of an Alpha object"


#==============================================================================
class AlphaBad1(Alpha):
    def __init__(self, config):
        super(AlphaBad1, self).__init__(config)
        self.a_type = int

    #--------------------------------------------------------------------------
    def to_str(self):
        raise AttributeError


#==============================================================================
class AlphaBad2(AlphaBad1):
    #--------------------------------------------------------------------------
    def to_str(self):
        raise KeyError


#==============================================================================
class AlphaBad3(AlphaBad1):
    #--------------------------------------------------------------------------
    def to_str(self):
        raise TypeError


#==============================================================================
class Beta(RequiredConfig):
    required_config = Namespace()
    required_config.add_option(
        'b',
        doc='b',
        default=23
    )

    #--------------------------------------------------------------------------
    def __init__(self, config):
        self.config = config
        self.b = config.b


#==============================================================================
class TestCase(unittest.TestCase):

    #--------------------------------------------------------------------------
    def test_str_dict_keys(self):
        function = converters.str_dict_keys
        result = function({u'name': u'Peter', 'age': 99, 10: 11})
        self.assertEqual(result, {'name': u'Peter', 'age': 99, 10: 11})

        for key in result.keys():
            if key in ('name', 'age'):
                if six.PY2:
                    self.assertTrue(not isinstance(key, six.text_type))
                self.assertTrue(isinstance(key, str))
            else:
                self.assertTrue(isinstance(key, int))

    #--------------------------------------------------------------------------
    def test_str_quote_stripper(self):
        a = """'"single and double quoted"'"""
        self.assertEqual(
            converters.str_quote_stripper(a),
            'single and double quoted'
        )

        a = """'single quoted'"""
        self.assertEqual(converters.str_quote_stripper(a), 'single quoted')

        a = '''"double quoted"'''
        self.assertEqual(converters.str_quote_stripper(a), 'double quoted')

        a = '"""triple quoted"""'
        self.assertEqual(converters.str_quote_stripper(a), 'triple quoted')

        a = "'''triple quoted'''"
        self.assertEqual(converters.str_quote_stripper(a), 'triple quoted')

        a = '''"trailing apostrophy'"'''
        self.assertEqual(
            converters.str_quote_stripper(a),
            "trailing apostrophy'"
        )

    #--------------------------------------------------------------------------
    def test_str_to_timedelta(self):
        str_to_timedelta = converters.timedelta_converter
        from datetime import timedelta
        self.assertEqual(
            str_to_timedelta('1'),
            timedelta(seconds=1)
        )
        self.assertEqual(
            str_to_timedelta('2:1'),
            timedelta(minutes=2, seconds=1)
        )
        self.assertEqual(
            str_to_timedelta('3:2:1'),
            timedelta(hours=3, minutes=2, seconds=1)
        )
        self.assertEqual(
            str_to_timedelta('4:3:2:1'),
            timedelta(days=4, hours=3, minutes=2, seconds=1)
        )
        self.assertEqual(
            str_to_timedelta('4 03:02:01'),
            timedelta(days=4, hours=3, minutes=2, seconds=1)
        )
        self.assertRaises(ValueError, str_to_timedelta, 'xxx')
        self.assertRaises(TypeError, str_to_timedelta, 10.1)

    #--------------------------------------------------------------------------
    def test_str_to_python_object_nothing(self):
        self.assertEqual(converters.str_to_python_object(''), None)

    #--------------------------------------------------------------------------
    def test_str_to_python_object_with_whitespace(self):
        """either side whitespace doesn't matter"""
        function = converters.class_converter
        self.assertEqual(
            function("""

         configman.tests.test_converters.Foo

        """),
            Foo)

    #--------------------------------------------------------------------------
    def test_dict_conversions(self):
        d = {
            'a': 1,
            'b': 'fred',
            'c': 3.1415
        }
        converter_fn = converters.to_string_converters[type(d)]
        s = converter_fn(d)

        # round  trip
        converter_fn = converters.str_to_instance_of_type_converters[type(d)]
        dd = converter_fn(s)
        self.assertEqual(dd, d)

    #--------------------------------------------------------------------------
    def test_classes_in_namespaces_converter_1(self):
        converter_fn = converters.classes_in_namespaces_converter('HH%d')
        class_list_str = (
            'configman.tests.test_converters.Foo,'
            'configman.tests.test_converters.Bar'
        )
        result = converter_fn(class_list_str)
        self.assertTrue(hasattr(result, 'required_config'))
        req = result.required_config
        self.assertEqual(len(req), 2)
        self.assertTrue('HH0' in req)
        self.assertEqual(len(req.HH0), 1)
        self.assertTrue('cls' in req.HH0)
        self.assertTrue('HH1' in req)
        self.assertEqual(len(req.HH1), 1)
        self.assertTrue('cls' in req.HH1)
        self.assertEqual(
            sorted([x.strip() for x in class_list_str.split(',')]),
            sorted([
                x.strip() for x in
                converters.py_obj_to_str(result).split(',')
            ])
        )

    #--------------------------------------------------------------------------
    def test_classes_in_namespaces_converter_2(self):
        converter_fn = converters.classes_in_namespaces_converter('HH%d')
        class_sequence = (Foo, Bar)
        self.assertRaises(TypeError, converter_fn, class_sequence)

    #--------------------------------------------------------------------------
    def test_classes_in_namespaces_converter_3(self):
        n = Namespace()
        n.add_option(
            'kls_list',
            default=(
                'configman.tests.test_converters.Alpha, '
                'configman.tests.test_converters.Alpha, '
                'configman.tests.test_converters.Alpha'
            ),
            from_string_converter=
            converters.classes_in_namespaces_converter('kls%d')
        )

        cm = ConfigurationManager(n, argv_source=[])
        config = cm.get_config()

        self.assertEqual(len(config.kls_list.subordinate_namespace_names), 3)
        for x in config.kls_list.subordinate_namespace_names:
            self.assertTrue(x in config)
            self.assertEqual(config[x].cls, Alpha)
            self.assertTrue('cls_instance' not in config[x])

    #--------------------------------------------------------------------------
    def test_classes_in_namespaces_converter_4(self):
        n = Namespace()
        n.add_option(
            'kls_list',
            default=(
                'configman.tests.test_converters.Alpha, '
                'configman.tests.test_converters.Alpha, '
                'configman.tests.test_converters.Alpha'
            ),
            from_string_converter=converters.classes_in_namespaces_converter(
                'kls%d',
                'kls',
                instantiate_classes=True
            )
        )

        cm = ConfigurationManager(
            n,
            [{
                'kls_list': (
                    'configman.tests.test_converters.Alpha, '
                    'configman.tests.test_converters.Beta, '
                    'configman.tests.test_converters.Beta, '
                    'configman.tests.test_converters.Alpha'
                )
            }]
        )
        config = cm.get_config()

        self.assertEqual(len(config.kls_list.subordinate_namespace_names), 4)
        for x in config.kls_list.subordinate_namespace_names:
            self.assertTrue(x in config)
            self.assertTrue('kls_instance' in config[x])
            self.assertTrue(
                isinstance(config[x].kls_instance,
                           config[x].kls)
            )

    #--------------------------------------------------------------------------
    def test_to_str_to_regular_expression(self):
        import re
        self.assertEqual(
            converters.str_to_regular_expression('.*'),
            re.compile('.*')
        )

    #--------------------------------------------------------------------------
    def test_str_to_list(self):
        function = converters.list_converter
        self.assertEqual(function(''), [])

        self.assertEqual(
            function('configman.tests.test_converters.TestCase'),
            ['configman.tests.test_converters.TestCase']
        )
        self.assertEqual(
            function('configman.tests, configman'),
            ['configman.tests', 'configman']
        )
        self.assertEqual(
            function('int, str, 123, hello'),
            ['int', 'str', '123', 'hello']
        )
        self.assertEqual(
            function(u'P\xefter, L\xa3rs'),
            [u'P\xefter', u'L\xa3rs']
        )

    #--------------------------------------------------------------------------
    def test_to_str(self):
        to_str = converters.to_str
        self.assertEqual(to_str(int), 'int')
        self.assertEqual(to_str(float), 'float')
        if six.PY2:
            self.assertEqual(to_str(six.binary_type), 'str')
            self.assertEqual(to_str(six.text_type), 'unicode')
        else:
            self.assertEqual(to_str(six.binary_type), 'bytes')
            self.assertEqual(to_str(six.text_type), 'str')
        self.assertEqual(to_str(bool), 'bool')
        self.assertEqual(to_str(dict), 'dict')
        self.assertEqual(to_str(list), 'list')
        self.assertEqual(to_str(datetime.datetime), 'datetime.datetime')
        self.assertEqual(to_str(datetime.date), 'datetime.date')
        self.assertEqual(to_str(datetime.timedelta), 'datetime.timedelta')
        self.assertEqual(to_str(type), 'type')
        self.assertEqual(
            to_str(converters.compiled_regexp_type),
            '_sre.SRE_Pattern'
        )
        self.assertEqual(to_str(1), '1')
        self.assertEqual(to_str(3.1415), '3.1415')
        self.assertEqual(
            to_str(datetime.datetime(
                1960,
                5,
                4,
                15,
                10
            )),
            '1960-05-04T15:10:00'
        )
        self.assertEqual(to_str(True), 'True')
        self.assertEqual(to_str(False), 'False')
        self.assertEqual(to_str((2, False, int, max)), '2, False, int, max')
        self.assertEqual(to_str(None), '')
        self.assertEqual(to_str('hello'), "hello")
        self.assertEqual(
            to_str(u"'你好'"),
            u"'\u4f60\u597d'"
        )
        self.assertEqual(
            converters.list_to_str([1, 2, 3]),
            "1, 2, 3"
        )
        self.assertEqual(
            to_str(datetime.datetime(1960, 5, 4, 15, 10)),
            "1960-05-04T15:10:00"
        )
        self.assertEqual(
            to_str(datetime.date(1960, 5, 4)),
            "1960-05-04"
        )
        self.assertEqual(
            to_str(datetime.timedelta(days=1, seconds=1)),
            "1 00:00:01"
        )
        self.assertEqual(to_str(unittest), 'unittest')

        self.assertEqual(
            to_str(to_str),
            'configman.converters.to_str'
        )

        import re
        r = re.compile('.*')
        self.assertEqual(to_str(r), '.*')

    #--------------------------------------------------------------------------
    def test_str_to_boolean(self):
        self.assertTrue(converters.str_to_boolean('TRUE'))
        self.assertTrue(converters.str_to_boolean('"""TRUE"""'))
        self.assertTrue(converters.str_to_boolean('true'))
        self.assertTrue(converters.str_to_boolean('t'))
        self.assertTrue(converters.str_to_boolean('1'))
        self.assertTrue(converters.str_to_boolean('T'))
        self.assertTrue(converters.str_to_boolean('yes'))
        self.assertTrue(converters.str_to_boolean("'yes'"))
        self.assertTrue(converters.str_to_boolean('y'))

        self.assertFalse(converters.str_to_boolean('FALSE'))
        self.assertFalse(converters.str_to_boolean('false'))
        self.assertFalse(converters.str_to_boolean('f'))
        self.assertFalse(converters.str_to_boolean('F'))
        self.assertFalse(converters.str_to_boolean('no'))
        self.assertFalse(converters.str_to_boolean('NO'))
        self.assertFalse(converters.str_to_boolean(''))
        self.assertFalse(converters.str_to_boolean(
            '你好, says Lärs'
        ))
        self.assertRaises(ValueError, converters.str_to_boolean, 99)

    #--------------------------------------------------------------------------
    def test_arbitrary_object_to_string(self):
        function = converters.py_obj_to_str
        self.assertEqual(function(None), '')
        self.assertEqual(function('hello'), 'hello')

        config = DotDict()
        config.a = 17
        config.b = 23
        a = Alpha(config)
        self.assertEqual(
            converters.arbitrary_object_to_string(a),
            "I am an instance of an Alpha object"
        )
        a = AlphaBad1(config)
        self.assertEqual(
            converters.arbitrary_object_to_string(a),
            "int"
        )
        a = AlphaBad2(config)
        self.assertEqual(
            converters.arbitrary_object_to_string(a),
            "int"
        )
        a = AlphaBad3(config)
        self.assertEqual(
            converters.arbitrary_object_to_string(a),
            "int"
        )
        self.assertEqual(
            converters.arbitrary_object_to_string(IndexError),
            "IndexError"
        )

        self.assertEqual(
            converters.arbitrary_object_to_string(Beta),
            "configman.tests.test_converters.Beta"
        )

        from configman import tests as tests_module
        self.assertEqual(function(tests_module), 'configman.tests')

    #--------------------------------------------------------------------------
    def test_list_to_str(self):
        function = converters.list_to_str
        self.assertEqual(function([]), '')
        self.assertEqual(function(tuple()), '')

        import configman
        self.assertEqual(
            function([configman.tests.test_converters.TestCase]),
            'configman.tests.test_converters.TestCase'
        )
        self.assertEqual(
            function([configman.tests, configman]),
            'configman.tests, configman'
        )
        self.assertEqual(
            function([int, str, 123, "hello"]),
            'int, str, 123, hello'
        )
        self.assertEqual(
            function((configman.tests.test_converters.TestCase,)),
            'configman.tests.test_converters.TestCase'
        )
        self.assertEqual(
            function((configman.tests, configman)),
            'configman.tests, configman'
        )
        self.assertEqual(
            function((int, str, 123, "hello")),
            'int, str, 123, hello'
        )
        self.assertEqual(
            function((u'P\xefter', u'L\xa3rs')),
            u'P\xefter, L\xa3rs'
        )
