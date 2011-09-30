import unittest
import collections

import configman.config_manager as config_manager
import configman.dotdict as dd
import configman.option_defs as optdef

class TestCase(unittest.TestCase):

    def test_setup_definitions_1(self):
        d = dd.DotDict()
        def fake_mapping_func(source, destination):
            self.assertIsInstance(source, collections.Mapping)
            self.assertEqual(d, destination)
        saved_original = optdef.definition_dispatch.copy()
        try:
            optdef.definition_dispatch[collections.Mapping] = fake_mapping_func
            s = {}
            optdef.setup_definitions(s, d)
            s = dd.DotDict()
            optdef.setup_definitions(s, d)
            s = config_manager.Namespace()
            optdef.setup_definitions(s, d)
        finally:
            optdef.definition_dispatch = saved_original


    def test_setup_definitions_2(self):
        d = dd.DotDict()
        def fake_mapping_func(source, destination):
            self.assertIs(source, collections)
            self.assertEqual(d, destination)
        saved_original = optdef.definition_dispatch.copy()
        try:
            optdef.definition_dispatch[type(collections)] = fake_mapping_func
            s = collections
            optdef.setup_definitions(s, d)
        finally:
            optdef.definition_dispatch = saved_original


    def test_setup_definitions_3(self):
        d = dd.DotDict()
        def fake_mapping_func(source, destination):
            self.assertIsInstance(source, str)
            self.assertEqual(d, destination)
        saved_original = optdef.definition_dispatch.copy()
        try:
            optdef.definition_dispatch[str] = fake_mapping_func
            s = "{}"
            optdef.setup_definitions(s, d)
        finally:
            optdef.definition_dispatch = saved_original



