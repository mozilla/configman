import unittest
import os
import tempfile

import configman.config_manager as config_manager


class TestCase(unittest.TestCase):

    def test_OptionsByConfFile_basics(self):
        tmp_filename = os.path.join(tempfile.gettempdir(), 'test.conf')
        with open(tmp_filename, 'w') as f:
            f.write('# comment\n')
            f.write('limit=20\n')
            f.write('\n')
        try:
            o = config_manager.ConfValueSource(tmp_filename)
            assert o.values == {'limit': '20'}, o.values
            c = config_manager.ConfigurationManager([],
                                        manager_controls=False,
                                        use_config_files=False,
                                        auto_help=False,
                                        argv_source=[])

            self.assertEqual(o.get_values(c, False), {'limit': '20'})
            self.assertEqual(o.get_values(c, True), {'limit': '20'})
            # XXX (peterbe): commented out because I'm not sure if
            # OptionsByConfFile get_values() should depend on the configuration
            # manager it is given as first argument or not.
            #self.assertEqual(o.get_values(c, True), {})
            #self.assertRaises(config_manager.NotAnOptionError,
            #                  o.get_values, c, False)

            #c.option_definitions.option('limit', default=0)
            #self.assertEqual(o.get_values(c, False), {'limit': '20'})
            #self.assertEqual(o.get_values(c, True), {'limit': '20'})
        finally:
            if os.path.isfile(tmp_filename):
                os.remove(tmp_filename)
