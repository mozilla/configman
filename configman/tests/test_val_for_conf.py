import unittest
import os
import tempfile
import StringIO as sio

import configman.config_manager as config_manager
from ..value_sources import for_conf
from ..option import Option


class TestCase(unittest.TestCase):

    def test_OptionsByConfFile_basics(self):
        tmp_filename = os.path.join(tempfile.gettempdir(), 'test.conf')
        with open(tmp_filename, 'w') as f:
            f.write('# comment\n')
            f.write('limit=20\n')
            f.write('\n')
        try:
            o = for_conf.ValueSource(tmp_filename)
            assert o.values == {'limit': '20'}, o.values
            # in the case of this implementation of a ValueSource,
            # the two parameters to get_values are dummies.  That may
            # not be true for all ValueSource implementations
            self.assertEqual(o.get_values(1, False), {'limit': '20'})
            self.assertEqual(o.get_values(2, True), {'limit': '20'})
            # XXX (peterbe): commented out because I'm not sure if
            # OptionsByConfFile get_values() should depend on the configuration
            # manager it is given as first argument or not.
            #c = config_manager.ConfigurationManager([],
                                        #manager_controls=False,
                                        ##use_config_files=False,
                                        #use_auto_help=False,
                                        #argv_source=[])
            #self.assertEqual(o.get_values(c, True), {})
            #self.assertRaises(config_manager.NotAnOptionError,
            #                  o.get_values, c, False)
            #c.option_definitions.option('limit', default=0)
            #self.assertEqual(o.get_values(c, False), {'limit': '20'})
            #self.assertEqual(o.get_values(c, True), {'limit': '20'})
        finally:
            if os.path.isfile(tmp_filename):
                os.remove(tmp_filename)

    def test_write_flat_1(self):
        def iter_source():
            yield 'x', 'x', Option('x', default=13, doc='the x')
            yield 'y', 'y', Option('y', default=-1, doc='the y')
            yield 'z', 's', Option('z', default='fred', doc='the z')
        out = sio.StringIO()
        for_conf.ValueSource.write(iter_source, out)
        result = out.getvalue()
        expected = ("# name: x\n"
                    "# doc: the x\n"
                    "# converter: int\n"
                    "x=13\n\n"
                    "# name: y\n"
                    "# doc: the y\n"
                    "# converter: int\n"
                    "y=-1\n\n"
                    "# name: z\n"
                    "# doc: the z\n"
                    "# converter: str\n"
                    "z=fred\n\n"
                    )
        self.assertEqual(expected, result,
                         "exepected %s\nbut got\n%s" % (expected, result))
        #config.write_conf(output_stream=out)

    #def test_write_flat(self):
        #n = self._some_namespaces()
        #config = config_manager.ConfigurationManager(
          #[n],
          #manager_controls=False,
          ##use_config_files=False,
          #use_auto_help=False,
          #argv_source=[]
        #)
        #expected = """# name: aaa
## doc: the a
## converter: configman.datetime_util.datetime_from_ISO_string
#aaa=2011-05-04T15:10:00

##-------------------------------------------------------------------------------
## c - c space

## name: c.fred
## doc: husband from Flintstones
## converter: str
#c.fred=stupid

## name: c.wilma
## doc: wife from Flintstones
## converter: str
#c.wilma=waspish

##-------------------------------------------------------------------------------
## d - d space

## name: d.ethel
## doc: female neighbor from I Love Lucy
## converter: str
#d.ethel=silly

## name: d.fred
## doc: male neighbor from I Love Lucy
## converter: str
#d.fred=crabby

##-------------------------------------------------------------------------------
## x - x space

## name: x.password
## doc: the password
## converter: str
#x.password=********

## name: x.size
## doc: how big in tons
## converter: int
#x.size=100
#"""
        #out = StringIO()
        #config.write_conf(output_stream=out)
        #received = out.getvalue()
        #self.assertEqual(expected.strip(), received.strip())

    #def test_write_flat_with_passwords(self):

        #n = config_manager.Namespace(doc='top')
        #n.add_option('password', 'secrets', 'the password')
        #n.add_option('unpassword', 'notsecret', 'not a password')

        #config = config_manager.ConfigurationManager(
          #[n],
          #manager_controls=False,
          ##use_config_files=False,
          #use_auto_help=False,
          #argv_source=[]
        #)

        #out = StringIO()
        #config.write_conf(output_stream=out)
        #received = out.getvalue()
        #expected = ("# name: password\n"
                    #"# doc: the password\n"
                    #"# converter: str\n"
                    #"password=********")
        #self.assertTrue(expected in received)

        #expected = ("# name: unpassword\n"
                    #"# doc: not a password\n"
                    #"# converter: str\n"
                    #"unpassword=notsecret")
        #self.assertTrue(expected in received)

    #def test_write_flat_unrecognized_converter(self):
        #from decimal import Decimal
        #n = config_manager.Namespace(doc='top')
        #n.add_option('cost', Decimal('0.00'), 'the cost',
          #short_form='cost',
          #from_string_converter=Decimal
        #)

        #config = config_manager.ConfigurationManager(
          #[n],
          #manager_controls=False,
          ##use_config_files=False,
          #use_auto_help=False,
          #argv_source=[]
        #)

        #out = StringIO()
        #config.write_conf(output_stream=out)
        #received = out.getvalue()
        #expected = ("# name: cost\n"
                   #"# doc: the cost\n"
                   #"# converter: decimal.Decimal\n"
                   #"cost=0.00")
        #self.assertEqual(received.strip(), expected.strip())

