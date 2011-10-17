import unittest

from configman import option, dotdict, namespace
from configman.def_sources import for_mappings


class TestCase(unittest.TestCase):

    def test_setup_definitions_1(self):
        s = dotdict.DotDict()
        s.x = option.Option('x', 17, 'the x')
        s.n = {'name': 'n', 'doc': 'the n', 'default': 23}
        s.__forbidden__ = option.Option('__forbidden__',
                                        'no, you cannot',
                                         38)
        s.t = namespace.Namespace()
        s.t.add_option('kk', 999, 'the kk')
        s.w = 89
        s.z = None
        s.t2 = namespace.Namespace('empty namespace')
        d = dotdict.DotDict()
        for_mappings.setup_definitions(s, d)
        self.assertTrue(len(d) == 5)
        self.assertTrue(isinstance(d.x, option.Option))
        self.assertTrue(isinstance(d.n, option.Option))
        self.assertTrue(d.n.name == 'n')
        self.assertTrue(d.n.default == 23)
        self.assertTrue(d.n.doc == 'the n')
        self.assertTrue(isinstance(d.t, namespace.Namespace))
        self.assertTrue(d.t.kk.name == 'kk')
        self.assertTrue(d.t.kk.default == 999)
        self.assertTrue(d.t.kk.doc == 'the kk')
        self.assertTrue(isinstance(d.w, namespace.Option))
        self.assertTrue(d.w.name == 'w')
        self.assertTrue(d.w.default == 89)
        self.assertTrue(d.w.doc == 'w')
        self.assertTrue(isinstance(d.t2, namespace.Namespace))
        self.assertTrue(len(d.t2) == 0)
