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
