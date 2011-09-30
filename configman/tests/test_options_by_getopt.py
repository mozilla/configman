import unittest

import configman.config_manager as config_manager
from configman.config_exceptions import NotAnOptionError


class TestCase(unittest.TestCase):

    def test_OptionsByGetOpt_basics(self):
        source = ['a', 'b', 'c']
        o = config_manager.OptionsByGetopt(source)
        self.assertEqual(o.argv_source, source)
        o = config_manager.OptionsByGetopt(argv_source=source)
        self.assertEqual(o.argv_source, source)

    def test_OptionsByGetOpt_get_values(self):
        c = config_manager.ConfigurationManager(
          manager_controls=False,
          use_config_files=False,
          auto_help=False,
          argv_source=[]
        )

        source = ['--limit', '10']
        o = config_manager.OptionsByGetopt(source)
        self.assertEqual(o.get_values(c, True), {})
        self.assertRaises(NotAnOptionError,
                          o.get_values, c, False)

        c.option_definitions.option('limit', default=0)
        self.assertEqual(o.get_values(c, False), {'limit': '10'})
        self.assertEqual(o.get_values(c, True), {'limit': '10'})

    def test_OptionsByGetOpt_getopt_with_ignore(self):
        function = config_manager.OptionsByGetopt.getopt_with_ignore
        args = ['a', 'b', 'c']
        o, a = function(args, '', [])
        self.assertEqual(o, [])
        self.assertEqual(a, args)
        args = ['-a', '14', '--fred', 'sally', 'ethel', 'dwight']
        o, a = function(args, '', [])
        self.assertEqual([], o)
        self.assertEqual(a, args)
        args = ['-a', '14', '--fred', 'sally', 'ethel', 'dwight']
        o, a = function(args, 'a:', [])
        self.assertEqual(o, [('-a', '14')])
        self.assertEqual(a, ['--fred', 'sally', 'ethel', 'dwight'])
        args = ['-a', '14', '--fred', 'sally', 'ethel', 'dwight']
        o, a = function(args, 'a', ['fred='])
        self.assertEqual(o, [('-a', ''), ('--fred', 'sally')])
        self.assertEqual(a, ['14', 'ethel', 'dwight'])

    def test_overlay_config_5(self):
        """test namespace definition w/getopt"""
        n = config_manager.Namespace()
        n.a = config_manager.Option(name='a', doc='the a', default=1)
        n.b = 17
        n.c = config_manager.Option(name='c', doc='the c', default=False)
        g = config_manager.OptionsByGetopt(argv_source=['--a', '2', '--c'])
        c = config_manager.ConfigurationManager([n], [g],
                                    manager_controls=False,
                                    use_config_files=False,
                                    auto_help=False,
                                    argv_source=[])
        self.assertEqual(c.option_definitions.a, n.a)
        self.assertTrue(isinstance(c.option_definitions.b,
                                   config_manager.Option))
        self.assertEqual(c.option_definitions.a.value, 2)
        self.assertEqual(c.option_definitions.b.value, 17)
        self.assertEqual(c.option_definitions.b.default, 17)
        self.assertEqual(c.option_definitions.b.name, 'b')
        self.assertEqual(c.option_definitions.c.name, 'c')
        self.assertEqual(c.option_definitions.c.value, True)

    def test_overlay_config_6(self):
        """test namespace definition w/getopt"""
        n = config_manager.Namespace()
        n.a = config_manager.Option(name='a', doc='the a', default=1)
        n.b = 17
        n.c = config_manager.Namespace()
        n.c.extra = config_manager.Option(name='extra', short_form='e',
                                          doc='the x', default=3.14159)
        g = config_manager.OptionsByGetopt(
          argv_source=['--a', '2', '--c.extra', '11.0']
        )
        c = config_manager.ConfigurationManager([n], [g],
                                    manager_controls=False,
                                    use_config_files=False,
                                    auto_help=False)
        self.assertEqual(c.option_definitions.a, n.a)
        self.assertEqual(type(c.option_definitions.b), config_manager.Option)
        self.assertEqual(c.option_definitions.a.value, 2)
        self.assertEqual(c.option_definitions.b.value, 17)
        self.assertEqual(c.option_definitions.b.default, 17)
        self.assertEqual(c.option_definitions.b.name, 'b')
        self.assertEqual(c.option_definitions.c.extra.name, 'extra')
        self.assertEqual(c.option_definitions.c.extra.doc, 'the x')
        self.assertEqual(c.option_definitions.c.extra.default, 3.14159)
        self.assertEqual(c.option_definitions.c.extra.value, 11.0)

    def test_overlay_config_6a(self):
        """test namespace w/getopt w/short form"""
        n = config_manager.Namespace()
        n.a = config_manager.Option(name='a', doc='the a', default=1)
        n.b = 17
        n.c = config_manager.Namespace()
        n.c.extra = config_manager.Option(
          name='extra',
          short_form='e',
          doc='the x',
          default=3.14159
        )
        g = config_manager.OptionsByGetopt(
          argv_source=['--a', '2', '-e', '11.0']
        )
        c = config_manager.ConfigurationManager([n], [g],
                                    manager_controls=False,
                                    use_config_files=False,
                                    auto_help=False)
        self.assertEqual(c.option_definitions.a, n.a)
        self.assertEqual(type(c.option_definitions.b), config_manager.Option)
        self.assertEqual(c.option_definitions.a.value, 2)
        self.assertEqual(c.option_definitions.b.value, 17)
        self.assertEqual(c.option_definitions.b.default, 17)
        self.assertEqual(c.option_definitions.b.name, 'b')
        self.assertEqual(c.option_definitions.c.extra.name, 'extra')
        self.assertEqual(c.option_definitions.c.extra.doc, 'the x')
        self.assertEqual(c.option_definitions.c.extra.default, 3.14159)
        self.assertEqual(c.option_definitions.c.extra.value, 11.0)
