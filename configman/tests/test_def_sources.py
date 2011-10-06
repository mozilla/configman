import unittest
import collections

import configman.config_manager as config_manager
import configman.dotdict as dd
import configman.def_sources as defsrc


class TestCase(unittest.TestCase):

    def test_setup_definitions_1(self):
        d = dd.DotDict()

        def fake_mapping_func(source, destination):
            self.assertTrue(isinstance(source, collections.Mapping))
            self.assertEqual(d, destination)
        saved_original = defsrc.definition_dispatch.copy()
        try:
            defsrc.definition_dispatch[collections.Mapping] = fake_mapping_func
            s = {}
            defsrc.setup_definitions(s, d)
            s = dd.DotDict()
            defsrc.setup_definitions(s, d)
            s = config_manager.Namespace()
            defsrc.setup_definitions(s, d)
        finally:
            defsrc.definition_dispatch = saved_original

    def test_setup_definitions_2(self):
        d = dd.DotDict()

        def fake_mapping_func(source, destination):
            self.assertTrue(source is collections)
            self.assertEqual(d, destination)
        saved_original = defsrc.definition_dispatch.copy()
        try:
            defsrc.definition_dispatch[type(collections)] = fake_mapping_func
            s = collections
            defsrc.setup_definitions(s, d)
        finally:
            defsrc.definition_dispatch = saved_original

    def test_setup_definitions_3(self):
        d = dd.DotDict()

        def fake_mapping_func(source, destination):
            self.assertTrue(isinstance(source, str))
            self.assertEqual(d, destination)
        saved_original = defsrc.definition_dispatch.copy()
        try:
            defsrc.definition_dispatch[str] = fake_mapping_func
            s = "{}"
            defsrc.setup_definitions(s, d)
        finally:
            defsrc.definition_dispatch = saved_original
