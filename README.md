configman
=========

(c) Mozilla

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

