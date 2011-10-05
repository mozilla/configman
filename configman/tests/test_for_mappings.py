import unittest
import collections

import configman.config_manager as config_manager
import configman.dotdict as dd
import configman.option_defs.for_mappings as fmp

class TestCase(unittest.TestCase):

    def test_setup_definitions_1(self):
        s = config_manager.DotDict()
        s.x = config_manager.Option('x', 'the x', 17, int)
        s.n = {'name':'n', 'doc':'the n', 'default':23}
        s.__forbidden__ = config_manager.Option('__forbidden__',
                                                'no, you cannot',
                                                38)
        s.t = config_manager.Namespace()
        s.t.option('kk', 'the kk', 999)
        s.w = 89
        s.z = None
        s.t2 = config_manager.Namespace('empty namespace')
        d = config_manager.DotDict()
        fmp.setup_definitions(s, d)
        self.assertTrue(len(d) == 5)
        self.assertTrue(isinstance(d.x, config_manager.Option))
        self.assertTrue(isinstance(d.n, config_manager.Option))
        self.assertTrue(d.n.name == 'n')
        self.assertTrue(d.n.default == 23)
        self.assertTrue(d.n.doc == 'the n')
        self.assertTrue(isinstance(d.t, config_manager.Namespace))
        self.assertTrue(d.t.kk.name == 'kk')
        self.assertTrue(d.t.kk.default == 999)
        self.assertTrue(d.t.kk.doc == 'the kk')
        self.assertTrue(isinstance(d.w, config_manager.Option))
        self.assertTrue(d.w.name == 'w')
        self.assertTrue(d.w.default == 89)
        self.assertTrue(d.w.doc == 'w')
        self.assertTrue(isinstance(d.t2, config_manager.Namespace))
        self.assertTrue(len(d.t2) == 0)
