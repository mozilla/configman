.. _introduction:

.. highlight:: python

=========================
Introduction (start here)
=========================

``configman`` is a package that paves over the differences between
various configuration methods to achieve a smooth road of cooperation
between them.

We use it here at Mozilla to tie together all the different scripts
and programs in `Socorro <https://wiki.mozilla.org/Socorro>`_.

The modules typically used for configuration in Python applications
have inconsistent APIs.  You cannot simply swap ``getopt`` for
``argparse`` and neither of them will do anything at all with
configuration files like ``ini`` or ``json``. And if applications do
work with some configuration file of choice it usually doesn't support
rich types such as classes, functions and Python types that aren't
built in.
 
For example, it is possible with ``configman`` to define
configuration in ``json`` and then automatically have ``ini`` file and
command line support.  Further, configman enables configuration values
to be dynamically loaded Python objects, functions, classes or
modules.  These dynamically loaded values can, in turn, pull in more
configuration definitions and more dynamic loading.  This enables
configman to offer configurable plugins for nearly any aspect of a
Python application.


