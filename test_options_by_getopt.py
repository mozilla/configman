import options_by_getopt as gopt

def do_assert(r, e):
    assert r == e, 'expected\n%s\nbut got\n%s' % (e, r)

def test_OptionsByGetOpt01():
    source = [ 'a', 'b', 'c' ]
    o = gopt.OptionsByGetopt(source)
    do_assert(o.argv_source, source)
    o = gopt.OptionsByGetopt(argv_source=source)
    do_assert(o.argv_source, source)

def test_OptionsByGetOpt02():
    args = [ 'a', 'b', 'c' ]
    o, a = gopt.OptionsByGetopt.getopt_with_ignore(args, '', [])
    do_assert([], o)
    do_assert(a, args)
    args = [ '-a', '14', '--fred', 'sally', 'ethel', 'dwight' ]
    o, a = gopt.OptionsByGetopt.getopt_with_ignore(args, '', [])
    do_assert([], o)
    do_assert(a, args)
    args = [ '-a', '14', '--fred', 'sally', 'ethel', 'dwight' ]
    o, a = gopt.OptionsByGetopt.getopt_with_ignore(args, 'a:', [])
    do_assert(o, [('-a', '14')])
    do_assert(a,['--fred', 'sally', 'ethel', 'dwight'])
    args = [ '-a', '14', '--fred', 'sally', 'ethel', 'dwight' ]
    o, a = gopt.OptionsByGetopt.getopt_with_ignore(args, 'a', ['fred='])
    do_assert(o, [('-a', ''), ('--fred', 'sally')])
    do_assert(a,['14', 'ethel', 'dwight'])


