.. _tutorial:

.. highlight:: python

========
Tutorial
========

We're going to go from a simple application without ``configman``, to a
simple application with ``configman``.


Basics
------

Suppose we have a piece of code that is able to take a file of text
and transform it to something else::

 #!/usr/bin/env python

 def backwards(x):
     return x[::-1]

 if __name__ == '__main__':
     import sys
     print backwards(open(sys.argv[1]).read())

When run it could look something like this::

 $ echo "Peter" > foo.txt
 $ python backwards.py foo.txt
 reteP

Now, suppose you want to add some more options. For example, it could
remove all vowels from reversed string. So you can do this::

 $ python backwards.py --devowel foo.txt
 rtP

First, let's improve our business logic to add this new feature::

 def backwards(x):
     return x[::-1]

 import re
 vowels_regex = re.compile('[AEIOUY]', re.IGNORECASE)

 def devowel(x):
     return vowels_regex.sub('', x)


Now we need ``configman``. To add an option we need a namespace and then
we can define the first option.
For that create a function that sets
up ``configman`` for us. It can look something like this::

 from configman import Namespace, ConfigurationManager
 ...
 def create_config():
     definition = Namespace()
     definition.add_option(
       'devowel',
       default=False
     )

Next we need a decide what the value sources for this can come from.
Let's keep it simple for now and just use ``getopt`` which is Python's
built in command line argument parser::

 ...
 import getopt
 value_sources = (getopt,)

Before we can use ``configman``, we need to wrap it all up in a
``ConfigurationManager`` instance that is able to cook it all up for
us correctly. Continuing where we left off inside ``create_config()``::

 ...
 config_manager = ConfigurationManager(namespace, value_sources)
 return config_manager.get_config()

That's all! Let's put it all together and take it for a spin::

 #!/usr/bin/env python

 import getopt
 from configman import Namespace, ConfigurationManager


 def backwards(x, capitalize=False):
     return x[::-1]


 import re
 vowels_regex = re.compile('[AEIOUY]', re.IGNORECASE)


 def devowel(x):
     return vowels_regex.sub('', x)


 def create_config():
     definition = Namespace()
     namespace.add_option(
       'devowel',
       False
     )
     value_sources = (getopt,)
     config_manager = ConfigurationManager(definition, value_sources)
     return config_manager.get_config()


 if __name__ == '__main__':
     import sys
     config = create_config()
     content = backwards(open(sys.argv[1]).read())
     if config.devowel:
         content = devowel(content)
     print content

When run, you get what you expect::

 $ python backwards.py --devowel foo.txt
 rtP
 $ python backwards.py foo.txt
 reteP


Intermediate
------------

Now let's expand some of the more powerful features of ``configman`` to
see what it can help us with. Let's start with the help. You invoke
the help simply by running it like this::

 $ python backwards.py --help

That's set up automatically for you. As you can see, it mentions,
amongst other things, our ``--devowel`` option there. Let's change
the definition of the option slightly to be more helpful::


 def create_config():
     definition = Namespace()
     definition.add_option(
       'devowel',
       False,
       'Removes all vowels (including Y)',
       short_form='d'
     )

Now, when running ``--help`` it will explain our option like this::

  -d, --devowel
      Removes all vowels (including Y)

Our example is still very much about the command line and the whole
point of using ``configman`` is so you can use various config file formats
to provide input to your programs.

Realistically, when integrating systems you don't read individual
words from the command line like this. I/O is more likely to come from
a file or a database or something. Let's now also add an option for
taking in the text::

     ...
     definition.add_option(
       'file',
       '',  # default value
       'Filename that contains our text'
     )


Excellent! Now let's assume that what's coming in is a file instead.
The full code looks like this now::

 #!/usr/bin/env python

 import getopt
 from configman import Namespace, ConfigurationManager


 def backwards(x, capitalize=False):
     return x[::-1]


 import re
 vowels_regex = re.compile('[AEIOUY]', re.IGNORECASE)


 def devowel(x):
     return vowels_regex.sub('', x)


 def create_config():
     definition = Namespace()
     definition.add_option(
       'devowel',
       False,
       'Removes all vowels (including Y)',
       short_form='d'
     )
     definition.add_option(
       'file',
       default='',  # default value
       doc='Filename that contains our text'
     )
     value_sources = (getopt,)
     config_manager = ConfigurationManager(definition, value_sources)
     return config_manager.get_config()


 if __name__ == '__main__':
     config = create_config()
     content = open(config.file)
     content = backwards(content)
     if config.devowel:
         content = devowel(content)
     print content

And it's executed like this::

 $ python backwards.py --file foo.txt
 reteP

 $ python backwards.py --file foo.txt -d
 rtP


Persistent config files
-----------------------

The real power of ``configman`` isn't to wrap executable command line
scripts but it its ability to work **agnostically** with config files.

To get started, let's turn our program into a configuration file. The
easiest way is to use the ``--write`` option that is automatically
available. It offers different ways to output.

* ``ini``
* ``conf``
* ``json``

Let's, for the sake of this tutorial, decide to use ``.ini`` files::

 $ python backwards.py --write=ini

This will print out a default configation file in ``ini`` format.
Let's save that so it can be used and read from instead of having to
use input on the command line. First save it::

 $ sudo python backwards.py --write=ini > backwards.ini
 $ cat backwards.ini
 [top_level]
 # name: devowel
 # doc: Removes all vowels (including Y)
 # converter: configman.converters.boolean_converter
 devowel=False

 # name: file
 # doc: Filename that contains our text
 # converter: str
 file=

Alternatively, we can adjust they default values by what use as
parameters when we write the config file. Let's do it like this
instead::

 $ sudo python backwards.py --write=ini --devowel \
  --file=/tmp/foo.txt > backwards.ini
 $ cat backwards.ini
 [top_level]
 # name: devowel
 # doc: Removes all vowels (including Y)
 # converter: configman.converters.boolean_converter
 devowel=True

 # name: file
 # doc: Filename that contains our text
 # converter: str
 file=/tmp/foo.txt

Next, let's make this file the default to read from instead of using
the command line. To do that edit this line::

 value_sources = (getopt,)

To this::

 value_sources = ('backwards.ini', getopt)

Now, the program can run entirely from the config file instead.
Suppose we change the last line of the file ``backwards.ini`` to
instead say::

 file=/tmp/bar.txt

And then create that file like this::

 $ echo "Socorro" > /tmp/bar.txt

Now, our little program is completely self-sufficient::

 $ python backwards.py
 Orrocos


More advanced options
---------------------

We just covered how to turn a simple application to one where the
configuration is done entirely by a ``ini`` file. Note; we could have
chosen ``json`` or ``conf`` instead of ``ini`` and the program would
be completely unchanged. Only your taste of config file format
changed. Let's quickly explore some more advanced options to whet your
appetite.
