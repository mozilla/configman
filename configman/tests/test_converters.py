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
import tempfile
from configman import converters
from configman import RequiredConfig, Namespace, ConfigurationManager

# the following two classes are used in test_classes_in_namespaces_converter1
# and need to be declared at module level scope
class Foo(RequiredConfig):
    required_config = Namespace()
    required_config.add_option('x',
                               default=17)
    required_config.add_option('y',
                               default=23)
class Bar(RequiredConfig):
    required_config = Namespace()
    required_config.add_option('x',
                               default=227)
    required_config.add_option('a',
                               default=11)

# the following two classes are used in test_classes_in_namespaces_converter2
# and test_classes_in_namespaces_converter_3.  They need to be declared at
#module level scope

class Alpha(RequiredConfig):
    required_config = Namespace()
    required_config.add_option('a',
                               doc='a',
                               default=17)

    def __init__(self, config):
        self.config = config
        self.a = config.a

class Beta(RequiredConfig):
    required_config = Namespace()
    required_config.add_option('b',
                               doc='b',
                               default=23)
    def __init__(self, config):
        self.config = config
        self.b = config.b

class Gamma(RequiredConfig):
    required_config = Namespace()
    required_config.add_option('g',
                               default=30)

    def __init__(self, config):
        self.config = config
        self.g = config.g

def splitter(class_list_str):
    return [tuple(line.split('|')) for line in class_list_str.split('\n')]

def get_class(class_list_element):
    try:
        return class_list_element[0].strip()
    except IndexError:
        if isinstance(class_list_element, basestring):
            return class_list_element

def get_extra(class_list_tuple):
    n = Namespace()
    n.add_option('frequency',
                 doc='how often',
                 default=class_list_tuple[1].strip(),
                 from_string_converter=int)
    try:
        n.add_option('time',
                     doc='absolute execution time',
                     default=class_list_tuple[2].strip())
    except IndexError:
        pass
    return n

def make_class_list_fn(class_namespace_prefix='cls', class_option_name='cls'):
    def class_list_fn(global_config, local_config, args):
        class_list = []
        for a_class_namespace in local_config.keys():
            if a_class_namespace.startswith(class_namespace_prefix):
                class_list.append(
                  local_config[a_class_namespace][class_option_name])
        return class_list
    return class_list_fn

def make_class_list_extra_fn(class_namespace_prefix='cls',
                             class_option_name='cls'):
    def class_list_fn(global_config, local_config, args):
        class_list = []
        for a_class_namespace in local_config.keys():
            if a_class_namespace.startswith(class_namespace_prefix):
                try:
                    class_extra_tuple = (
                      local_config[a_class_namespace][class_option_name],
                      local_config[a_class_namespace].frequency,
                      local_config[a_class_namespace].time
                    )
                except KeyError:
                    class_extra_tuple = (
                      local_config[a_class_namespace][class_option_name],
                      local_config[a_class_namespace].frequency,
                    )
                class_list.append(class_extra_tuple)
        return class_list
    return class_list_fn


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

    def test_list_to_str(self):
        function = converters.list_to_str
        self.assertEqual(function([]), '')
        self.assertEqual(function(tuple()), '')

        import configman
        self.assertEqual(function([configman.tests.test_converters.TestCase]),
                         'configman.tests.test_converters.TestCase')
        self.assertEqual(function([configman.tests, configman]),
                         'configman.tests, configman')
        self.assertEqual(function([int, str, 123, "hello"]),
                         'int, str, 123, hello')

        self.assertEqual(function((configman.tests.test_converters.TestCase,)),
                         'configman.tests.test_converters.TestCase')
        self.assertEqual(function((configman.tests, configman)),
                         'configman.tests, configman')
        self.assertEqual(function((int, str, 123, "hello")),
                         'int, str, 123, hello')

    def test_classes_in_namespaces_converter_1(self):
        converter_fn = converters.classes_in_namespaces_converter('HH%d')
        class_list_str = ('configman.tests.test_converters.Foo,'
                          'configman.tests.test_converters.Bar')
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
                sorted([x.strip() for x in
                             converters.py_obj_to_str(result).split(',')]))

    def test_classes_in_namespaces_converter_2(self):
        converter_fn = converters.classes_in_namespaces_converter('HH%d')
        class_sequence = (Foo, Bar)
        self.assertRaises(TypeError, converter_fn, class_sequence)

    def test_classes_in_namespaces_converter_3(self):
        n = Namespace()
        n.add_option('kls_list',
                      default='configman.tests.test_converters.Alpha, '
                              'configman.tests.test_converters.Alpha, '
                              'configman.tests.test_converters.Alpha',
                      from_string_converter=
                         converters.classes_in_namespaces_converter('kls%d'))

        cm = ConfigurationManager(n, argv_source=[])
        config = cm.get_config()

        self.assertEqual(len(config.kls_list.subordinate_namespace_names), 3)
        for x in config.kls_list.subordinate_namespace_names:
            self.assertTrue(x in config)
            self.assertEqual(config[x].cls, Alpha)
            self.assertTrue('cls_instance' not in config[x])

    def test_classes_in_namespaces_converter_4(self):
        n = Namespace()
        n.add_option('kls_list',
                      default='configman.tests.test_converters.Alpha, '
                              'configman.tests.test_converters.Alpha, '
                              'configman.tests.test_converters.Alpha',
                      from_string_converter=
                         converters.classes_in_namespaces_converter(
                          'kls%d',
                          'kls',
                          instantiate_classes=True))

        cm = ConfigurationManager(
          n,
          [{'kls_list':'configman.tests.test_converters.Alpha, '
                       'configman.tests.test_converters.Beta, '
                       'configman.tests.test_converters.Beta, '
                       'configman.tests.test_converters.Alpha'}])
        config = cm.get_config()

        self.assertEqual(len(config.kls_list.subordinate_namespace_names), 4)
        for x in config.kls_list.subordinate_namespace_names:
            self.assertTrue(x in config)
            self.assertTrue('kls_instance' in config[x])
            self.assertTrue(isinstance(config[x].kls_instance,
                                       config[x].kls))

    def test_classes_in_namespaces_converter_5(self):
        source = """configman.tests.test_converters.Alpha|1|02:00:00
                    configman.tests.test_converters.Beta|2
                    configman.tests.test_converters.Gamma|3|03:00:00"""

        rc = Namespace()
        rc.add_option('cx',
                      default=source,
                      from_string_converter=
                          converters.classes_in_namespaces_converter(
                            list_splitter_fn=splitter,
                            class_extractor=get_class,
                            extra_extractor=get_extra,
                            instantiate_classes=True))
        # make an aggregation that is a list of class objects
        rc.add_aggregation('class_list',
                           make_class_list_fn())
        # make an aggregation that is a list of class objects and the
        # extra data as a tuple
        rc.add_aggregation('class_list_with_extra',
                           make_class_list_extra_fn())

        cm = ConfigurationManager(rc, values_source_list=[])
        config = cm.get_config()

        self.assertTrue('cx' in config)

        self.assertTrue('cls0' in config)
        self.assertTrue('cls' in config.cls0)
        self.assertTrue('cls_instance' in config.cls0)
        self.assertEqual(config.cls0.cls_instance.a, 17)
        self.assertTrue('frequency' in config.cls0)
        self.assertTrue('time' in config.cls0)

        self.assertTrue('cls1' in config)
        self.assertTrue('cls' in config.cls1)
        self.assertTrue('cls_instance' in config.cls1)
        self.assertEqual(config.cls1.cls_instance.b, 23)
        self.assertTrue('frequency' in config.cls1)
        self.assertTrue('time' not in config.cls1)

        self.assertTrue('cls2' in config)
        self.assertTrue('cls' in config.cls2)
        self.assertTrue('cls_instance' in config.cls2)
        self.assertEqual(config.cls2.cls_instance.g, 30)
        self.assertTrue('frequency' in config.cls2)
        self.assertTrue('time' in config.cls2)

        self.assertEqual(len(config.class_list), 3)
        classes = (config.cls0.cls,
                   config.cls1.cls,
                   config.cls2.cls)
        for ec, rc in zip(classes, config.class_list):
            self.assertTrue(ec is rc)

        self.assertEqual(len(config.class_list_with_extra), 3)
        classes = ((config.cls0.cls, 1, '02:00:00'),
                   (config.cls1.cls, 2),
                   (config.cls2.cls, 3, '03:00:00'))
        for ec, rc in zip(classes, config.class_list_with_extra):
            self.assertEqual(ec, rc)
