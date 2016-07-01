.. _typeconversion:

===============
Type conversion
===============

``configman`` comes with an advanced set of type conversion utilities.
This is necessary since config files don't allow rich python types to
be expressed. The way this is done is by turning things into strings
and turning strings into rich python objects by labelling what type
conversion script to use.

A basic example is that of booleans as seen in the :ref:`Tutorial
<tutorial>`
when it dumps the boolean ``devowel`` option as into an ``ini`` file.
It looks like this::

 [top_level]
 # name: devowel
 # doc: Removes all vowels (including Y)
 devowel=False

As you can see it automatically figured out that the convertor should
be ``configman.converters.boolean_converter``. As you can imagine;
under the hood ``configman`` does something like this::

 # pseudo code
 converter = __import__('configman.converters.boolean_converter')
 actual_value = converter('False')

So, how did it know you wanted a boolean converter? It picked this up
from the definition's default value's type itself. Reminder; from the
:ref:`Tutorial <tutorial>`::

 definition = Namespace()
 definition.add_option(
   'devowel',
   default=False
 )

Built-ins
---------

The list of ``configman`` built-in converters will get you very far for
basic python types. The complete list is this:

* **int**
* **float**
* **str**
* **unicode**
* **bool**
* **datetime.datetime** (``%Y-%m-%dT%H:%M:%S`` or ``%Y-%m-%dT%H:%M:%S.%f``)
* **datetime.date** (``%Y-%m-%d``)
* **datetime.timedelta** (for example, ``1:2:0:3`` becomes ``days=1,
  hours=2, minutes=0, seconds=3``)
* **type** (see below)
* **types.FunctionType** (see below)
* **compiled_regexp_type**

The **type** and **types.FunctionType** built-ins are simpler than
they might seem. It's basically the same example pseudo code above.
This example should demostrate how it might work::

 import morse
 namespace.add_option(
   'morsecode',
   '',
   'Turns morse code into real letters',
   from_string_converter=morse.morse_load
 )

What this will do is it will import the python module ``morse`` and
expect to find a function in there called ``morse_load``. Suppose we
have one that looks like this::

 # This is morse/__init__.py
 dictionary = {
   '.-.': 'p',
   '.': 'e',
   '-': 't',
   '.--.': 'r',
 }


 def morse_load(s):
     o = []
     for e in s.split(','):
         o.append(dictionary.get(e.lower(), '?'))
     return ''.join(o)


Another more advanced example is to load a *class* rather than a simple
value. To do this you'll need to use one of the pre-defined ``configman``
converters as the ``from_string_converter`` value. To our example
above we're going to add a configurable class::

 from __future__ import absolute_import, division, print_function
 from configman.converters import class_converter
 namespace.add_option(
   'dialect',
   'morse.ScottishDialect',
   'A Scottish dialect class for the morse code converter',
   from_string_converter=class_converter
 )

That needs to exist as an importable class. So we add it::

 # This is morse/__init__.py
 class ScottishDialect(object):
     def __init__(self, text):
         self.text = text

     def render(self):
         return self.text.replace('e', 'i').replace('E','I')


Now, this means that the class is configurable and you can refer to a
specific class simply by name and it becomes available in your
program. For example, in this trivial example we can use it like this::

 if __name__ == '__main__':
     config = create_config()
     dialect = config.dialect(config.morsecode)
     print(dialect.render())

If you run this like this::

 $ python morse-communicator.py --morsecode=.,-,.--.,-,.
 itrti

This is just an example to whet your appetite but a more realistic
example is that you might have a configurable class for
sending emails. In production you might have it wired to be to
something like this::

 namespace.add_option(
   'email_send_class',
   'backends.SMTP',
   'Which backend should send the emails',
   from_string_converter=class_converter
 )
 namespace.add_option(
   'smtp_hostname',
   default='smtp.mozilla.org',
 )
 namespace.add_option(
   'smtp_username',
   doc='username for using the SMTP server'
 )
 namespace.add_option(
   'smtp_password',
   doc='password for using the SMTP server'
 )

Then, suppose you have different backends for sending SMTP available
you might want to run it like this when doing local development::

 # name: email_send_class
 # doc: Which backend should send the emails
 dialect=backends.StdoutLogDumper

So that instead of sending over the network (which was default) it
uses another class which knows to just print the emails being sent on
the stdout or some log file or something.

Not built-ins
-------------

Suppose none of the built-ins in ``configman`` is what you want. There's
nothing stopping you from just writing down your own. Consider this
tip calculator for example::

 from __future__ import absolute_import, division, print_function
 import getopt
 from configman import Namespace, ConfigurationManager


 def create_config():
     namespace = Namespace()
     namespace.add_option(
       'tip',
       default=20
     )
     import decimal
     namespace.add_option(
       'amount',
       from_string_converter=decimal.Decimal
     )
     value_sources = ('tipcalc.ini', getopt, )
     config_manager = ConfigurationManager([namespace], value_sources)
     return config_manager.get_config()


 if __name__ == '__main__':
     config = create_config()
     tip_amount = config.amount * config.tip / 100
     print("(exact amount: %r)" % tip_amount)
     print('$%.2f' % tip_amount)

When run it will automatically convert whatever number you give it to
a python ``Decimal`` type. Note how in the example it prints the
``repr`` of the calculated value::

 $ python tipcalc.py --amount 100.59 --tip=25
 (exact amount: Decimal('25.1475'))
 $25.15
