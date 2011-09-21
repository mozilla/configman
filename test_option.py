import option as opt
import converters as conv

import datetime as dt


def do_assert(r, e):
    assert r == e, 'expected\n%s\nbut got\n%s' % (e, r)


def test_option_constructor_1 ():
    o = opt.Option()
    do_assert(o.name, None)
    do_assert(o.default, None)
    do_assert(o.doc, None)
    do_assert(o.from_string_converter, None)
    do_assert(o.value, None)

    o = opt.Option('lucy')
    do_assert(o.name, 'lucy')
    do_assert(o.default, None)
    do_assert(o.doc, None)
    do_assert(o.from_string_converter, None)
    do_assert(o.value, None)

    d = { 'name': 'lucy',
          'default': 1,
          'doc': "lucy's integer"
        }
    o = opt.Option(**d)
    do_assert(o.name, 'lucy')
    do_assert(o.default, 1)
    do_assert(o.doc, "lucy's integer")
    do_assert(o.from_string_converter, int)
    do_assert(o.value, 1)

    d = { 'name': 'lucy',
          'default': 1,
          'doc': "lucy's integer",
          'value': '1'
        }
    o = opt.Option(**d)
    do_assert(o.name, 'lucy')
    do_assert(o.default, 1)
    do_assert(o.doc, "lucy's integer")
    do_assert(o.from_string_converter, int)
    do_assert(o.value, 1)

    d = { 'name': 'lucy',
          'default': '1',
          'doc': "lucy's integer",
          'from_string_converter': int
        }
    o = opt.Option(**d)
    do_assert(o.name, 'lucy')
    do_assert(o.default, '1')
    do_assert(o.doc, "lucy's integer")
    do_assert(o.from_string_converter, int)
    do_assert(o.value, 1)

    d = { 'name': 'lucy',
          'default': '1',
          'doc': "lucy's integer",
          'from_string_converter': int,
          'other': 'no way'
        }
    o = opt.Option(**d)
    do_assert(o.name, 'lucy')
    do_assert(o.default, '1')
    do_assert(o.doc, "lucy's integer")
    do_assert(o.from_string_converter, int)
    do_assert(o.value, 1)

    d = { 'default': '1',
          'doc': "lucy's integer",
          'from_string_converter': int,
          'other': 'no way'
        }
    o = opt.Option(**d)
    do_assert(o.name, None)
    do_assert(o.default, '1')
    do_assert(o.doc, "lucy's integer")
    do_assert(o.from_string_converter, int)
    do_assert(o.value, 1)

    d = dt.datetime.now()
    o = opt.Option(name='now', default=d)
    do_assert(o.name, 'now')
    do_assert(o.default, d)
    do_assert(o.doc, None)
    do_assert(o.from_string_converter, conv.datetime_converter)
    do_assert(o.value, d)
