import datetime as dt
from contextlib import contextmanager
import ConfigParser
import io
import StringIO as sio
import json
import functools

#import socorro.unittest.testlib.expectations as exp
import config_manager as cm
import converters as conv

def do_assert(r, e):
    assert r == e, 'expected\n%s\nbut got\n%s' % (e, r)

def test_OptionsByGetOpt01():
    source = [ 'a', 'b', 'c' ]
    o = cm.OptionsByGetopt(source)
    do_assert(o.argv_source, source)
    o = cm.OptionsByGetopt(argv_source=source)
    do_assert(o.argv_source, source)

def test_OptionsByGetOpt02():
    args = [ 'a', 'b', 'c' ]
    o, a = cm.OptionsByGetopt.getopt_with_ignore(args, '', [])
    do_assert([], o)
    do_assert(a, args)
    args = [ '-a', '14', '--fred', 'sally', 'ethel', 'dwight' ]
    o, a = cm.OptionsByGetopt.getopt_with_ignore(args, '', [])
    do_assert([], o)
    do_assert(a, args)
    args = [ '-a', '14', '--fred', 'sally', 'ethel', 'dwight' ]
    o, a = cm.OptionsByGetopt.getopt_with_ignore(args, 'a:', [])
    do_assert(o, [('-a', '14')])
    do_assert(a,['--fred', 'sally', 'ethel', 'dwight'])
    args = [ '-a', '14', '--fred', 'sally', 'ethel', 'dwight' ]
    o, a = cm.OptionsByGetopt.getopt_with_ignore(args, 'a', ['fred='])
    do_assert(o, [('-a', ''), ('--fred', 'sally')])
    do_assert(a,['14', 'ethel', 'dwight'])


def test_empty_ConfigurationManager_constructor():
    c = cm.ConfigurationManager(manager_controls=False,
                                use_config_files=False,
                                auto_help=False)
    do_assert(c.option_definitions, cm.Namespace())

def test_get_config_1():
    n = cm.Namespace()
    n.a = cm.Option('a', 'the a', 1)
    n.b = 17
    c = cm.ConfigurationManager([n],
                                manager_controls=False,
                                use_config_files=False,
                                auto_help=False)
    d = c.get_config()
    e = cm.DotDict()
    e.a = 1
    e.b = 17
    do_assert(d, e)

def test_get_config_2():
    n = cm.Namespace()
    n.a = cm.Option(name='a', default=1, doc='the a')
    n.b = 17
    n.c = c = cm.Namespace()
    c.x = 'fred'
    c.y = 3.14159
    c.z = cm.Option('z', 'the 99', 99)
    c = cm.ConfigurationManager([n],
                                manager_controls=False,
                                use_config_files=False,
                                auto_help=False)
    d = c.get_config()
    e = cm.DotDict()
    e.a = 1
    e.b = 17
    e.c = cm.DotDict()
    e.c.x = 'fred'
    e.c.y = 3.14159
    e.c.z = 99
    do_assert(d, e)

def test_walk_config():
    """test_walk_config: step through them all"""
    n = cm.Namespace(doc='top')
    n.aaa = cm.Option('aaa', 'the a', False, short_form='a')
    n.c = cm.Namespace(doc='c space')
    n.c.fred = cm.Option('fred', 'husband from Flintstones')
    n.c.wilma = cm.Option('wilma', 'wife from Flintstones')
    n.d = cm.Namespace(doc='d space')
    n.d.fred = cm.Option('fred', 'male neighbor from I Love Lucy')
    n.d.ethel = cm.Option('ethel', 'female neighbor from I Love Lucy')
    n.d.x = cm.Namespace(doc='x space')
    n.d.x.size = cm.Option('size', 'how big in tons', 100, short_form='s')
    n.d.x.password = cm.Option('password', 'the password', 'secrets')
    c = cm.ConfigurationManager([n],
                                manager_controls=False,
                                use_config_files=False,
                                auto_help=False)
    e = [('aaa', 'aaa', n.aaa.name),
         ('c', 'c', n.c._doc),
         ('c.wilma', 'wilma', n.c.wilma.name),
         ('c.fred', 'fred', n.c.fred.name),
         ('d', 'd', n.d._doc),
         ('d.ethel', 'ethel', n.d.ethel.name),
         ('d.fred', 'fred', n.d.fred.name),
         ('d.x', 'x', n.d.x._doc),
         ('d.x.size', 'size', n.d.x.size.name),
         ('d.x.password', 'password', n.d.x.password.name),
        ]
    e.sort()
    r = [(q, k, v.name if isinstance(v, cm.Option) else v._doc)
          for q, k, v in c.walk_config()]
    r.sort()
    for expected, received in zip(e, r):
        do_assert(received, expected)

def some_namespaces():
    """set up some namespaces"""
    n = cm.Namespace(doc='top')
    n.aaa = cm.Option('aaa', 'the a', '2011-05-04T15:10:00', short_form='a',
                      from_string_converter=conv.datetime_converter)
    n.c = cm.Namespace(doc='c space')
    n.c.fred = cm.Option('fred', 'husband from Flintstones', default='stupid')
    n.c.wilma = cm.Option('wilma', 'wife from Flintstones', default='waspish')
    n.d = cm.Namespace(doc='d space')
    n.d.fred = cm.Option('fred', 'male neighbor from I Love Lucy', default='crabby')
    n.d.ethel = cm.Option('ethel', 'female neighbor from I Love Lucy', default='silly')
    n.x = cm.Namespace(doc='x space')
    n.x.size = cm.Option('size', 'how big in tons', 100, short_form='s')
    n.x.password = cm.Option('password', 'the password', 'secrets')
    return n

def test_write_flat():
    n = some_namespaces()
    c = cm.ConfigurationManager([n],
                                manager_controls=False,
                                use_config_files=False,
                                auto_help=False)
    expected = \
"""# name: aaa
# doc: the a
# converter: configman.converters.datetime_converter
aaa=2011-05-04T15:10:00

#-------------------------------------------------------------------------------
# c - c space

# name: c.fred
# doc: husband from Flintstones
# converter: str
c.fred=stupid

# name: c.wilma
# doc: wife from Flintstones
# converter: str
c.wilma=waspish

#-------------------------------------------------------------------------------
# d - d space

# name: d.ethel
# doc: female neighbor from I Love Lucy
# converter: str
d.ethel=silly

# name: d.fred
# doc: male neighbor from I Love Lucy
# converter: str
d.fred=crabby

#-------------------------------------------------------------------------------
# x - x space

# name: x.password
# doc: the password
# converter: str
x.password=********

# name: x.size
# doc: how big in tons
# converter: int
x.size=100
"""
    s = sio.StringIO()
    c.write_conf(output_stream=s)
    received = s.getvalue()
    s.close()
    for e, r in zip(expected.split('\n'), received.split('\n')):
        do_assert(r, e)

def test_write_ini():
    n = some_namespaces()
    c = cm.ConfigurationManager([n],
                                manager_controls=False,
                                use_config_files=False,
                                auto_help=False)
    expected = """[top_level]
# name: aaa
# doc: the a
# converter: configman.converters.datetime_converter
aaa=2011-05-04T15:10:00

[c]
# c space

# name: c.fred
# doc: husband from Flintstones
# converter: str
fred=stupid

# name: c.wilma
# doc: wife from Flintstones
# converter: str
wilma=waspish

[d]
# d space

# name: d.ethel
# doc: female neighbor from I Love Lucy
# converter: str
ethel=silly

# name: d.fred
# doc: male neighbor from I Love Lucy
# converter: str
fred=crabby

[x]
# x space

# name: x.password
# doc: the password
# converter: str
password=********

# name: x.size
# doc: how big in tons
# converter: int
size=100
"""
    s = sio.StringIO()
    c.write_ini(output_stream=s)
    received = s.getvalue()
    s.close()
    print received
    for e, r in zip(expected.split('\n'), received.split('\n')):
        do_assert(r, e)


def test_write_json():
    n = some_namespaces()
    c = cm.ConfigurationManager([n],
                                manager_controls=False,
                                use_config_files=False,
                                auto_help=False)
    expected = '{"x": {"password": {"default": "secrets", "name": "password", "from_string_converter": "str", "doc": "the password", "value": "secrets", "short_form": null}, "size": {"default": "100", "name": "size", "from_string_converter": "int", "doc": "how big in tons", "value": "100", "short_form": "s"}}, "c": {"wilma": {"default": "waspish", "name": "wilma", "from_string_converter": "str", "doc": "wife from Flintstones", "value": "waspish", "short_form": null}, "fred": {"default": "stupid", "name": "fred", "from_string_converter": "str", "doc": "husband from Flintstones", "value": "stupid", "short_form": null}}, "aaa": {"default": "2011-05-04T15:10:00", "name": "aaa", "from_string_converter": "configman.converters.datetime_converter", "doc": "the a", "value": "2011-05-04T15:10:00", "short_form": "a"}, "d": {"ethel": {"default": "silly", "name": "ethel", "from_string_converter": "str", "doc": "female neighbor from I Love Lucy", "value": "silly", "short_form": null}, "fred": {"default": "crabby", "name": "fred", "from_string_converter": "str", "doc": "male neighbor from I Love Lucy", "value": "crabby", "short_form": null}}}'
    jexp = json.loads(expected)
    s = sio.StringIO()
    c.write_json(output_stream=s)
    received = s.getvalue()
    s.close()
    jrec = json.loads(received)
    do_assert(jrec, jexp)
    # let's make sure that we can do a complete round trip
    c2 = cm.ConfigurationManager([jrec],
                                manager_controls=False,
                                use_config_files=False,
                                auto_help=False)
    s = sio.StringIO()
    c2.write_json(output_stream=s)
    received2 = s.getvalue()
    s.close()
    jrec2 = json.loads(received2)
    do_assert(jrec2, jexp)

def test_overlay_config_1():
    n = cm.Namespace()
    n.a = cm.Option()
    n.a.name = 'a'
    n.a.default = 1
    n.a.doc = 'the a'
    n.b = 17
    n.c = c = cm.Namespace()
    c.x = 'fred'
    c.y = 3.14159
    c.z = cm.Option()
    c.z.default = 99
    c.z.doc = 'the 99'
    c = cm.ConfigurationManager([n],
                                manager_controls=False,
                                use_config_files=False,
                                auto_help=False)
    o = { "a": 2, "c.z": 22, "c.x": 'noob', "c.y": "2.89" }
    c.overlay_config_recurse(o)
    d = c.get_config()
    e = cm.DotDict()
    e.a = 2
    e.b = 17
    e.c = cm.DotDict()
    e.c.x = 'noob'
    e.c.y = 2.89
    e.c.z = 22
    do_assert(d, e)

def test_overlay_config_2():
    n = cm.Namespace()
    n.a = cm.Option()
    n.a.name = 'a'
    n.a.default = 1
    n.a.doc = 'the a'
    n.b = 17
    n.c = c = cm.Namespace()
    c.x = 'fred'
    c.y = 3.14159
    c.z = cm.Option()
    c.z.default = 99
    c.z.doc = 'the 99'
    c = cm.ConfigurationManager([n],
                                manager_controls=False,
                                use_config_files=False,
                                auto_help=False)
    o = { "a": 2, "c.z": 22, "c.x": 'noob', "c.y": "2.89", "n": "not here" }
    c.overlay_config_recurse(o, ignore_mismatches=True)
    d = c.get_config()
    e = cm.DotDict()
    e.a = 2
    e.b = 17
    e.c = cm.DotDict()
    e.c.x = 'noob'
    e.c.y = 2.89
    e.c.z = 22
    do_assert(d, e)

def test_overlay_config_3():
    n = cm.Namespace()
    n.a = cm.Option()
    n.a.name = 'a'
    n.a.default = 1
    n.a.doc = 'the a'
    n.b = 17
    n.c = c = cm.Namespace()
    c.x = 'fred'
    c.y = 3.14159
    c.z = cm.Option()
    c.z.default = 99
    c.z.doc = 'the 99'
    c = cm.ConfigurationManager([n],
                                manager_controls=False,
                                use_config_files=False,
                                auto_help=False)
    o = { "a": 2, "c.z": 22, "c.x": 'noob', "c.y": "2.89", "c.n": "not here" }
    try:
        c.overlay_config_recurse(o, ignore_mismatches=False)
    except cm.NotAnOptionError:
        pass

def test_overlay_config_4():
    """test_namespace_constructor_4: test overlay dict w/flat source dict"""
    n = cm.Namespace()
    n.a = cm.Option(name='a', doc='the a', default=1)
    n.b = 17
    n.c = cm.Namespace()
    n.c.extra = cm.Option(name='extra', doc='the x', default=3.14159)
    g = { 'a': 2, 'c.extra': 2.89 }
    c = cm.ConfigurationManager([n], [g],
                                manager_controls=False,
                                use_config_files=False,
                                auto_help=False)
    do_assert(c.option_definitions.a, n.a)
    do_assert(type(c.option_definitions.b), cm.Option)
    do_assert(c.option_definitions.a.value, 2)
    do_assert(c.option_definitions.b.value, 17)
    do_assert(c.option_definitions.b.default, 17)
    do_assert(c.option_definitions.b.name, 'b')
    do_assert(c.option_definitions.c.extra.name, 'extra')
    do_assert(c.option_definitions.c.extra.doc, 'the x')
    do_assert(c.option_definitions.c.extra.default, 3.14159)
    do_assert(c.option_definitions.c.extra.value, 2.89)

def test_overlay_config_4a():
    """test_namespace_constructor_4a: test overlay dict w/deep source dict"""
    n = cm.Namespace()
    n.a = cm.Option(name='a', doc='the a', default=1)
    n.b = 17
    n.c = cm.Namespace()
    n.c.extra = cm.Option(name='extra', doc='the x', default=3.14159)
    g = { 'a': 2, 'c': {'extra': 2.89 }}
    c = cm.ConfigurationManager([n], [g],
                                manager_controls=False,
                                use_config_files=False,
                                auto_help=False)
    do_assert(c.option_definitions.a, n.a)
    do_assert(type(c.option_definitions.b), cm.Option)
    do_assert(c.option_definitions.a.value, 2)
    do_assert(c.option_definitions.b.value, 17)
    do_assert(c.option_definitions.b.default, 17)
    do_assert(c.option_definitions.b.name, 'b')
    do_assert(c.option_definitions.c.extra.name, 'extra')
    do_assert(c.option_definitions.c.extra.doc, 'the x')
    do_assert(c.option_definitions.c.extra.default, 3.14159)
    do_assert(c.option_definitions.c.extra.value, 2.89)

def test_overlay_config_5():
    """test_overlay_config_5: test namespace definition w/getopt"""
    n = cm.Namespace()
    n.a = cm.Option(name='a', doc='the a', default=1)
    n.b = 17
    n.c = cm.Option(name='c', doc='the c', default=False)
    g = cm.OptionsByGetopt(argv_source=['--a', '2', '--c'])
    c = cm.ConfigurationManager([n], [g],
                                manager_controls=False,
                                use_config_files=False,
                                auto_help=False)
    do_assert(c.option_definitions.a, n.a)
    do_assert(type(c.option_definitions.b), cm.Option)
    do_assert(c.option_definitions.a.value, 2)
    do_assert(c.option_definitions.b.value, 17)
    do_assert(c.option_definitions.b.default, 17)
    do_assert(c.option_definitions.b.name, 'b')
    do_assert(c.option_definitions.c.name, 'c')
    do_assert(c.option_definitions.c.value, True)

def test_overlay_config_6():
    """test_overlay_config_6: test namespace definition w/getopt"""
    n = cm.Namespace()
    n.a = cm.Option(name='a', doc='the a', default=1)
    n.b = 17
    n.c = cm.Namespace()
    n.c.extra = cm.Option(name='extra', short_form='e', doc='the x',
                          default=3.14159)
    g = cm.OptionsByGetopt(argv_source=['--a', '2', '--c.extra', '11.0'])
    c = cm.ConfigurationManager([n], [g],
                                manager_controls=False,
                                use_config_files=False,
                                auto_help=False)
    do_assert(c.option_definitions.a, n.a)
    do_assert(type(c.option_definitions.b), cm.Option)
    do_assert(c.option_definitions.a.value, 2)
    do_assert(c.option_definitions.b.value, 17)
    do_assert(c.option_definitions.b.default, 17)
    do_assert(c.option_definitions.b.name, 'b')
    do_assert(c.option_definitions.c.extra.name, 'extra')
    do_assert(c.option_definitions.c.extra.doc, 'the x')
    do_assert(c.option_definitions.c.extra.default, 3.14159)
    do_assert(c.option_definitions.c.extra.value, 11.0)

def test_overlay_config_6a():
    """test_overlay_config_6a: test namespace w/getopt w/short form"""
    n = cm.Namespace()
    n.a = cm.Option(name='a', doc='the a', default=1)
    n.b = 17
    n.c = cm.Namespace()
    n.c.extra = cm.Option(name='extra', short_form='e', doc='the x',
                          default=3.14159)
    g = cm.OptionsByGetopt(argv_source=['--a', '2', '-e', '11.0'])
    c = cm.ConfigurationManager([n], [g],
                                manager_controls=False,
                                use_config_files=False,
                                auto_help=False)
    do_assert(c.option_definitions.a, n.a)
    do_assert(type(c.option_definitions.b), cm.Option)
    do_assert(c.option_definitions.a.value, 2)
    do_assert(c.option_definitions.b.value, 17)
    do_assert(c.option_definitions.b.default, 17)
    do_assert(c.option_definitions.b.name, 'b')
    do_assert(c.option_definitions.c.extra.name, 'extra')
    do_assert(c.option_definitions.c.extra.doc, 'the x')
    do_assert(c.option_definitions.c.extra.default, 3.14159)
    do_assert(c.option_definitions.c.extra.value, 11.0)

def test_overlay_config_7():
    """test_overlay_config_7: test namespace definition flat file"""
    n = cm.Namespace()
    n.a = cm.Option(name='a', doc='the a', default=1)
    n.b = 17
    n.c = cm.Namespace()
    n.c.extra = cm.Option(name='extra', doc='the x', default=3.14159)
    n.c.string = cm.Option(name='string', doc='str', default='fred')
    @contextmanager
    def dummy_open(filename):
        yield ['# comment line to be ignored\n',
               '\n', # blank line to be ignored
               'a=22\n',
               'b = 33\n',
               'c.extra = 2.0\n',
               'c.string =   wilma\n'
              ]
    g = cm.OptionsByConfFile('dummy-filename', dummy_open)
    c = cm.ConfigurationManager([n], [g],
                                manager_controls=False,
                                use_config_files=False,
                                auto_help=False)
    do_assert(c.option_definitions.a, n.a)
    do_assert(type(c.option_definitions.b), cm.Option)
    do_assert(c.option_definitions.a.value, 22)
    do_assert(c.option_definitions.b.value, 33)
    do_assert(c.option_definitions.b.default, 17)
    do_assert(c.option_definitions.b.name, 'b')
    do_assert(c.option_definitions.c.extra.name, 'extra')
    do_assert(c.option_definitions.c.extra.doc, 'the x')
    do_assert(c.option_definitions.c.extra.default, 3.14159)
    do_assert(c.option_definitions.c.extra.value, 2.0)
    do_assert(c.option_definitions.c.string.name, 'string')
    do_assert(c.option_definitions.c.string.doc, 'str')
    do_assert(c.option_definitions.c.string.default, 'fred')
    do_assert(c.option_definitions.c.string.value, 'wilma')

def test_overlay_config_8():
    """test_overlay_config_8: test namespace definition ini file"""
    n = cm.Namespace()
    n.other = cm.Namespace()
    n.other.t = cm.Option('t', 'the t', 'tee')
    n.d = cm.Namespace()
    n.d.a = cm.Option(name='a', doc='the a', default=1)
    n.d.b = 17
    n.c = cm.Namespace()
    n.c.extra = cm.Option(name='extra', doc='the x', default=3.14159)
    n.c.string = cm.Option(name='string', doc='str', default='fred')
    ini_data = """
[other]
t=tea
[d]
# blank line to be ignored
a=22
b = 33
[c]
extra = 2.0
string =   wilma
"""
    #config = ConfigParser.RawConfigParser(allow_no_value=True)
    config = ConfigParser.RawConfigParser()
    config.readfp(io.BytesIO(ini_data))
    g = cm.OptionsByIniFile(config)
    c = cm.ConfigurationManager([n], [g],
                                manager_controls=False,
                                use_config_files=False,
                                auto_help=False)
    do_assert(c.option_definitions.other.t.name, 't')
    do_assert(c.option_definitions.other.t.value, 'tea')
    do_assert(c.option_definitions.d.a, n.d.a)
    do_assert(type(c.option_definitions.d.b), cm.Option)
    do_assert(c.option_definitions.d.a.value, 22)
    do_assert(c.option_definitions.d.b.value, 33)
    do_assert(c.option_definitions.d.b.default, 17)
    do_assert(c.option_definitions.d.b.name, 'b')
    do_assert(c.option_definitions.c.extra.name, 'extra')
    do_assert(c.option_definitions.c.extra.doc, 'the x')
    do_assert(c.option_definitions.c.extra.default, 3.14159)
    do_assert(c.option_definitions.c.extra.value, 2.0)
    do_assert(c.option_definitions.c.string.name, 'string')
    do_assert(c.option_definitions.c.string.doc, 'str')
    do_assert(c.option_definitions.c.string.default, 'fred')
    do_assert(c.option_definitions.c.string.value, 'wilma')

def test_overlay_config_9():
    """test_overlay_config_9: test namespace definition ini file"""
    n = cm.Namespace()
    n.other = cm.Namespace()
    n.other.t = cm.Option('t', 'the t', 'tee')
    n.d = cm.Namespace()
    n.d.a = cm.Option(name='a', doc='the a', default=1)
    n.d.b = 17
    n.c = cm.Namespace()
    n.c.extra = cm.Option(name='extra', doc='the x', default=3.14159)
    n.c.string = cm.Option(name='string', doc='str', default='fred')
    ini_data = """
[other]
t=tea
[d]
# blank line to be ignored
a=22
[c]
extra = 2.0
string =   from ini
"""
    #config = ConfigParser.RawConfigParser(allow_no_value=True)
    config = ConfigParser.RawConfigParser()
    config.readfp(io.BytesIO(ini_data))
    g = cm.OptionsByIniFile(config)
    e = cm.DotDict()
    e.fred = cm.DotDict() # should be ignored
    e.fred.t = 'T'  # should be ignored
    e.d = cm.DotDict()
    e.d.a = 16
    e.c = cm.DotDict()
    e.c.extra = 18.6
    e.c.string = 'from environment'
    v = cm.OptionsByGetopt(argv_source=['--other.t', 'TTT', '--c.extra', '11.0']
                           )
    c = cm.ConfigurationManager([n], [e, g, v],
                                manager_controls=False,
                                use_config_files=False,
                                auto_help=False)
    do_assert(c.option_definitions.other.t.name, 't')
    do_assert(c.option_definitions.other.t.value, 'TTT')
    do_assert(c.option_definitions.d.a, n.d.a)
    do_assert(type(c.option_definitions.d.b), cm.Option)
    do_assert(c.option_definitions.d.a.value, 22)
    do_assert(c.option_definitions.d.b.value, 17)
    do_assert(c.option_definitions.d.b.default, 17)
    do_assert(c.option_definitions.d.b.name, 'b')
    do_assert(c.option_definitions.c.extra.name, 'extra')
    do_assert(c.option_definitions.c.extra.doc, 'the x')
    do_assert(c.option_definitions.c.extra.default, 3.14159)
    do_assert(c.option_definitions.c.extra.value, 11.0)
    do_assert(c.option_definitions.c.string.name, 'string')
    do_assert(c.option_definitions.c.string.doc, 'str')
    do_assert(c.option_definitions.c.string.default, 'fred')
    do_assert(c.option_definitions.c.string.value, 'from ini')

def test_overlay_config_10():
    """test_overlay_config_10: test namespace definition ini file"""
    n = cm.Namespace()
    n.t = cm.Option('t', 'the t', 'tee')
    n.d = cm.Namespace()
    n.d.a = cm.Option(name='a', doc='the a', default=1)
    n.d.b = 17
    n.c = cm.Namespace()
    n.c.extra = cm.Option(name='extra', doc='the x', default=3.14159)
    n.c.string = cm.Option(name='string', doc='str', default='fred')
    ini_data = """
[top_level]
t=tea
[d]
# blank line to be ignored
a=22
[c]
extra = 2.0
string =   from ini
"""
    #config = ConfigParser.RawConfigParser(allow_no_value=True)
    config = ConfigParser.RawConfigParser()
    config.readfp(io.BytesIO(ini_data))
    g = cm.OptionsByIniFile(config)
    e = cm.DotDict()
    e.top_level = cm.DotDict()
    e.top_level.t = 'T'
    e.d = cm.DotDict()
    e.d.a = 16
    e.c = cm.DotDict()
    e.c.extra = 18.6
    e.c.string = 'from environment'
    v = cm.OptionsByGetopt(argv_source=['--c.extra', '11.0'])
    c = cm.ConfigurationManager([n], [e, g, v],
                                manager_controls=False,
                                use_config_files=False,
                                auto_help=False)
    do_assert(c.option_definitions.t.name, 't')
    do_assert(c.option_definitions.t.value, 'tea')
    do_assert(c.option_definitions.d.a, n.d.a)
    do_assert(type(c.option_definitions.d.b), cm.Option)
    do_assert(c.option_definitions.d.a.value, 22)
    do_assert(c.option_definitions.d.b.value, 17)
    do_assert(c.option_definitions.d.b.default, 17)
    do_assert(c.option_definitions.d.b.name, 'b')
    do_assert(c.option_definitions.c.extra.name, 'extra')
    do_assert(c.option_definitions.c.extra.doc, 'the x')
    do_assert(c.option_definitions.c.extra.default, 3.14159)
    do_assert(c.option_definitions.c.extra.value, 11.0)
    do_assert(c.option_definitions.c.string.name, 'string')
    do_assert(c.option_definitions.c.string.doc, 'str')
    do_assert(c.option_definitions.c.string.default, 'fred')
    do_assert(c.option_definitions.c.string.value, 'from ini')

def test_walk_expanding_class_options():
    class A(cm.RequiredConfig):
        required_config = { 'a': cm.Option('a', 'the a', 1),
                            'b': 17,
                          }
    n = cm.Namespace()
    n.source = cm.Namespace()
    n.source.c = cm.Option(name='c', default=A, doc='the A class')
    n.dest = cm.Namespace()
    n.dest.c = cm.Option(name='c', default=A, doc='the A class')
    c = cm.ConfigurationManager([n],
                                manager_controls=False,
                                use_config_files=False,
                                auto_help=False)
    e = cm.Namespace()
    e.s = cm.Namespace()
    e.s.c = cm.Option(name='c', default=A, doc='the A class')
    e.s.a = cm.Option('a', 'the a', 1)
    e.s.b = cm.Option('b', default=17)
    e.d = cm.Namespace()
    e.d.c = cm.Option(name='c', default=A, doc='the A class')
    e.d.a = cm.Option('a', 'the a', 1)
    e.d.b = cm.Option('b', default=17)
    def namespace_test(val):
        do_assert(type(val), cm.Namespace)
    def option_test(val, expected=None):
        do_assert(val.name, expected.name)
        do_assert(val.default, expected.default)
        do_assert(val.doc, expected.doc)
    e = [ ('dest', 'dest', namespace_test),
          ('dest.a', 'a', functools.partial(option_test, expected=e.d.a)),
          ('dest.b', 'b', functools.partial(option_test, expected=e.d.b)),
          ('dest.c', 'c', functools.partial(option_test, expected=e.d.c)),
          ('source', 'source', namespace_test),
          ('source.a', 'a', functools.partial(option_test, expected=e.s.a)),
          ('source.b', 'b', functools.partial(option_test, expected=e.s.b)),
          ('source.c', 'c', functools.partial(option_test, expected=e.s.c)),
        ]
    c_contents = [(qkey, key, val) for qkey, key, val in c.walk_config()]
    c_contents.sort()
    e.sort()
    print c_contents
    print e
    for c_tuple, e_tuple in zip(c_contents, e):
        qkey, key, val = c_tuple
        e_qkey, e_key, e_fn = e_tuple
        do_assert(qkey, e_qkey)
        do_assert(key, e_key)
        e_fn(val)

def test_get_option_names():
    """test_get_option_names: walk 'em"""
    n = cm.Namespace()
    n.a = cm.Option('a', 'the a', 1)
    n.b = 17
    n.c = cm.Namespace()
    n.c.fred = cm.Option('fred')
    n.c.wilma = cm.Option('wilma')
    n.d = cm.Namespace()
    n.d.fred = cm.Option('fred')
    n.d.wilma = cm.Option('wilma')
    n.d.x = cm.Namespace()
    n.d.x.size = cm.Option('size')
    c = cm.ConfigurationManager([n],
                                manager_controls=False,
                                use_config_files=False,
                                auto_help=False)
    names = c.get_option_names()
    names.sort()
    e = ['a', 'b', 'c.fred', 'c.wilma', 'd.fred', 'd.wilma', 'd.x.size']
    e.sort()
    do_assert(names, e)

def test_get_option_by_name():
    """test_get_option_by_name: you made them, you can have them back"""
    n = cm.Namespace()
    n.a = cm.Option('a', 'the a', 1)
    n.b = 17
    n.c = cm.Namespace()
    n.c.fred = cm.Option('fred')
    n.c.wilma = cm.Option('wilma')
    n.d = cm.Namespace()
    n.d.fred = cm.Option('fred')
    n.d.wilma = cm.Option('wilma')
    n.d.x = cm.Namespace()
    n.d.x.size = cm.Option('size')
    c = cm.ConfigurationManager([n],
                                manager_controls=False,
                                use_config_files=False,
                                auto_help=False)
    do_assert(c.get_option_by_name('a'), n.a)
    do_assert(c.get_option_by_name('b').name, 'b')
    do_assert(c.get_option_by_name('c.fred'), n.c.fred)
    do_assert(c.get_option_by_name('c.wilma'), n.c.wilma)
    do_assert(c.get_option_by_name('d.fred'), n.d.fred)
    do_assert(c.get_option_by_name('d.wilma'), n.d.wilma)
    do_assert(c.get_option_by_name('d.wilma'), n.d.wilma)
    do_assert(c.get_option_by_name('d.x.size'), n.d.x.size)

def test_output_summary():
    """test_output_summary: the output from help"""
    n = cm.Namespace()
    n.aaa = cm.Option('aaa', 'the a', False, short_form='a')
    n.b = 17
    n.c = cm.Namespace()
    n.c.fred = cm.Option('fred', 'husband from Flintstones')
    n.c.wilma = cm.Option('wilma', 'wife from Flintstones')
    n.d = cm.Namespace()
    n.d.fred = cm.Option('fred', 'male neighbor from I Love Lucy')
    n.d.ethel = cm.Option('ethel', 'female neighbor from I Love Lucy')
    n.d.x = cm.Namespace()
    n.d.x.size = cm.Option('size', 'how big in tons', 100, short_form='s')
    n.d.x.password = cm.Option('password', 'the password', 'secrets')
    c = cm.ConfigurationManager([n],
                                manager_controls=False,
                                use_config_files=False,
                                auto_help=False)
    s = sio.StringIO()
    c.output_summary(output_stream=s)
    r = s.getvalue()
    s.close()
    e =  \
"""	-a, --aaa
		the a
	    --b
		no documentation available (default: 17)
	    --c.fred
		husband from Flintstones (default: None)
	    --c.wilma
		wife from Flintstones (default: None)
	    --d.ethel
		female neighbor from I Love Lucy (default: None)
	    --d.fred
		male neighbor from I Love Lucy (default: None)
	    --d.x.password
		the password (default: ********)
	-s, --d.x.size
		how big in tons (default: 100)
"""
    do_assert(r, e)

def test_eval_as_converter():
    """does eval work as a to string converter on an Option object?"""
    n = cm.Namespace()
    n.aaa = cm.Option('aaa', 'the a', False, short_form='a')
    n.b = 17
    n.c = cm.Namespace()
    n.c.fred = cm.Option('rules', 'the doc',
                         default="[ ('version', 'fred', 100), "
                                 "('product', 'sally', 100)]",
                         from_string_converter=eval)
    n.c.wilma = cm.Option('wilma', 'wife from Flintstones')
    c = cm.ConfigurationManager([n],
                                manager_controls=False,
                                use_config_files=False,
                                auto_help=False)
    s = sio.StringIO()
    c.output_summary(output_stream=s)
    r = s.getvalue()
    s.close()
    e =  \
"""	-a, --aaa
		the a
	    --b
		no documentation available (default: 17)
	    --c.fred
		the doc (default: [('version', 'fred', 100), ('product', 'sally', 100)])
	    --c.wilma
		wife from Flintstones (default: None)
"""
    do_assert(r, e)
