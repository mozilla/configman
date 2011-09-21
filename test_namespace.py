import namespace as nmsp
import option as opt

def test_namespace_constructor_0():
    """test_namespace_constructor_0: test namespace definition"""
    n = nmsp.Namespace('doc string')
    n.alpha = 1
    my_birthday = dt.datetime(1960,5,4,15,10)
    n.beta = my_birthday
    do_assert(n.alpha.name, 'alpha')
    do_assert(n.alpha.doc, None)
    do_assert(n.alpha.default, 1)
    do_assert(n.alpha.from_string_converter, int)
    do_assert(n.alpha.value, 1)
    do_assert(n.beta.name, 'beta')
    do_assert(n.beta.doc, None)
    do_assert(n.beta.default, my_birthday)
    do_assert(n.beta.from_string_converter, conv.datetime_converter)
    do_assert(n.beta.value, my_birthday)
    do_assert(n._doc, 'doc string')


def test_namespace_constructor_1():
    """test_namespace_constructor_1: test namespace definition"""
    n = nmsp.Namespace()
    n.a = opt.Option()
    n.a.name = 'a'
    n.a.default = 1
    n.a.doc = 'the a'
    n.b = 17
    c = cm.ConfigurationManager([n],
                                use_config_files=False,
                                )
    do_assert(c.option_definitions.a, n.a)
    do_assert(type(c.option_definitions.b), opt.Option)
    do_assert(c.option_definitions.b.value, 17)
    do_assert(c.option_definitions.b.default, 17)
    do_assert(c.option_definitions.b.name, 'b')


def test_namespace_constructor_2():
    """test_namespace_constructor_2: test list definition"""
    l = [ (None, 'a', True, 1, 'the a'),
          (None, 'b', True, 17, '') ]
    c = cm.ConfigurationManager([l],
                                use_config_files=False,
                                )
    do_assert(type(c.option_definitions.a), opt.Option)
    do_assert(c.option_definitions.a.value, 1)
    do_assert(c.option_definitions.a.default, 1)
    do_assert(c.option_definitions.a.name, 'a')
    do_assert(type(c.option_definitions.b), opt.Option)
    do_assert(c.option_definitions.b.value, 17)
    do_assert(c.option_definitions.b.default, 17)
    do_assert(c.option_definitions.b.name, 'b')


def test_namespace_constructor_3():
    """test_namespace_constructor_3: test json definition"""

    j = '{ "a": {"name": "a", "default": 1, "doc": "the a"}, "b": 17}'
    c = cm.ConfigurationManager([j],
                                use_config_files=False,
                                )
    do_assert(type(c.option_definitions.a), opt.Option)
    do_assert(c.option_definitions.a.value, 1)
    do_assert(c.option_definitions.a.default, 1)
    do_assert(c.option_definitions.a.name, 'a')
    do_assert(type(c.option_definitions.b), opt.Option)
    do_assert(c.option_definitions.b.value, 17)
    do_assert(c.option_definitions.b.default, 17)
    do_assert(c.option_definitions.b.name, 'b')

