import os
import tempfile

import configman.config_manager as config_manager

import unittest


class TestCase(unittest.TestCase):

    def test_OptionsByIniFile_basics(self):
        tmp_filename = os.path.join(tempfile.gettempdir(), 'test.conf')
        open(tmp_filename, 'w').write("""
; comment
[top_level]
name=Peter
awesome:
; comment
[othersection]
foo=bar  ; other comment
        """)

        try:
            o = config_manager.OptionsByIniFile(tmp_filename)
            c = config_manager.ConfigurationManager([],
                                        manager_controls=False,
                                        use_config_files=False,
                                        auto_help=False,
                                        argv_source=[])

            self.assertEqual(o.get_values(c, False),
                             {'othersection.foo': 'bar',
                              'name': 'Peter',
                              'awesome': ''})
            self.assertEqual(o.get_values(c, True),
                             {'othersection.foo': 'bar',
                              'name': 'Peter',
                              'awesome': ''})
        finally:
            if os.path.isfile(tmp_filename):
                os.remove(tmp_filename)
