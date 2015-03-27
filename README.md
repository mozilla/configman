configman
=========

[![Travis](https://travis-ci.org/mozilla/configman.png?branch=master)](https://travis-ci.org/mozilla/configman)

Copyright Mozilla, 2013 - 2015

General tool for setting up configuration options per namespaces.
Supports reading and writing configs generally from and into config
files.


Running tests
-------------

We use [nose](http://code.google.com/p/python-nose/) to run all the
unit tests and [tox](http://tox.testrun.org/latest/) to test multiple
python versions. To run the whole suite just run:

    tox

`tox` will pass arguments after `--` to `nosetests`. To run with test
coverage calculation, run `tox` like this:

    tox -- --with-coverage --cover-html --cover-package=configman

If you want to run a specific test in a testcase class, though,
you might consider just using `nosetests`:

    nosetests configman.tests.test_config_manager:TestCase.test_write_flat


Making a release
----------------

Because our `.travis.yml` has all the necessary information to automatically
make a release, all you need to do is to push a commit onto master.
Most likely you will only want to do this after you have
edited the `configman/version.txt` file. Suppose you make some changes:

    git add configman/configman.py
    git commit -m "fixed something"

You might want to push that to your fork and make a pull request. Then,
to update the version and make a release, first do this:

    vim configman/version.txt
    git add configman/version.txt
    git commit -m "bump to version x.y.z"
    git push origin master

After that travis, upon a successful build will automatically make a new
tarball and wheel and upload it to [PyPI](https://pypi.python.org/pypi/configman)
