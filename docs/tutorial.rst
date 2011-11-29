.. _tutorial:

.. highlight:: python

========
Tutorial
========

We're going to go from a simple application without ``configman``, to a
simple application with ``configman``.


Basics
------

Suppose we write an app similar to the ``echo`` command line program in Unix
and Linux.  Our app, though reverses the lettering of each word::

 def backwards(x):
     return x[::-1]

 if __name__ == '__main__':
     import sys
     output_string = ' '.join(sys.argv[1:])
     print backwards(output_string)

.. sidebar:: running examples

   each example in this tutorial is available as file in the ``configman/demo``
   folder.

When run it could look something like this::

 $ ./tutorial01.py Peter was here
 ereh saw reteP

Now, suppose you want to add some more options that can be selected at run
time. For example, it could remove all vowels from reversed string. So you can
do this::

 $ ./tutorial02.py --devowel Lars was here
 rh sw srL

First, let's improve our business logic to add this new feature::

 def backwards(x):
     return x[::-1]

 import re
 vowels_regex = re.compile('[AEIOUY]', re.IGNORECASE)

 def devowel(x):
     return vowels_regex.sub('', x)

Now we need ``configman`` to enable the run time option for removing the vowels
from the input string. It will take the form of a command line switch.  If, at
run time, the switch is present, we'll use the ``devowel`` function.  If the
switch is not present, we won't use the function.

To add this option we create an option container.  These containers are called
*namespaces* and have a method that allows us to define our command line
options.

Here's a function that sets up a namespace with a single option::

 from configman import Namespace, ConfigurationManager
 ...
 def define_config():
     definition = Namespace()
     definition.add_option(
       name='devowel',
       default=False
     )

Before we can use this option definition, we need to wrap it up in a
``ConfigurationManager`` instance that is able to cook it up for
us correctly::

 ...
 config_manager = ConfigurationManager(definition)
 config = config_manager.get_config()

That's all! That last line returned an instance of what we call a DotDict.
It is essentially a standard Python dict that's had its ``__getattr__`` cross
wired with its ``__getitem__`` method.  This means that we can access the
values in the dict as if they were attributes.  Watch how we access the value
of ``devowel`` in the full example below::

 from configman import Namespace, ConfigurationManager

 def backwards(x, capitalize=False):
     return x[::-1]

 import re
 vowels_regex = re.compile('[AEIOUY]', re.IGNORECASE)

 def devowel(x):
     return vowels_regex.sub('', x)

 def define_config():
     definition = Namespace()
     definition.add_option(
       name='devowel',
       default=False
     )
     return definition

 if __name__ == '__main__':
     definition = define_config()
     config_manager = ConfigurationManager(definition)
     config = config_manager.get_config()
     output_string = ' '.join(config_manager.args)
     if config.devowel:
         output_string = devowel(output_string)
     print backwards(output_string)

When run, you get what you expect::

 $ ./tutorial02.py Peter was here
 ereh saw reteP
 $ ./tutorial02.py --devowel Peter was here
 rh sw rtP

In the ``tutorial01.py`` example, we fetched the command line arguments using
the reference to argv from the sys module.  We couldn't do that in the second
tutorial because sys.argv included the command line switch ``--devowel``.  We
don't want that as part of the output.  ``configman`` offers a version of the
command line arguments with the switches removed.  That's the
``config_manager.args`` reference inside the ``join``.


Intermediate
------------

Now let's expand some of the more powerful features of ``configman`` to
see what it can help us with. Let's start with the help. You invoke
the help simply by running it like this::

 $ ./tutorial02.py --help

That's set up automatically for you. As you can see, it mentions,
amongst other things, our ``--devowel`` option there. Let's change
the definition of the option slightly to be more helpful::


 def define_config():
     definition = Namespace()
     definition.add_option(
       name='devowel',
       default=False,
       doc='Removes all vowels (including Y)',
       short_form='d'
     )

Now, when running ``--help`` it will explain our option like this::

  -d, --devowel    Removes all vowels (including Y)

Let's add another option so that we can get our text from a file instead
of the command line.  The objective is to get a file name from a ``--file``
or ``-f`` switch.  We'll set the default to be the empty string.  If the
user doesn't use the switch, the value for this will be the empty string::

     ...
     definition.add_option(
       name='file',
       default='',
       doc='Filename that contains our text',
       short_form='f'
     )


Excellent! The whole thing together looks like this now::

 from configman import Namespace, ConfigurationManager

 def backwards(x, capitalize=False):
     return x[::-1]

 import re
 vowels_regex = re.compile('[AEIOUY]', re.IGNORECASE)

 def devowel(x):
     return vowels_regex.sub('', x)

 def define_config():
     definition = Namespace()
     definition.add_option(
       name='devowel',
       default=False,
       doc='Removes all vowels (including Y)',
       short_form='d'
     )
     definition.add_option(
       name='file',
       default='',
       doc='file name for the input text',
       short_form='f'
     )
     return definition

 if __name__ == '__main__':
     definition = define_config()
     config_manager = ConfigurationManager(definition)
     config = config_manager.get_config()
     if config.file:
         with open(config.file) as f:
             output_string = f.read().strip()
     else:
         output_string = ' '.join(config_manager.args)
     if config.devowel:
         output_string = devowel(output_string)
     print backwards(output_string)

And it's executed like this::

 $ cat > foo.txt
 Peter works for Mozilla.^d
 $ ./tutorial03.py  --file foo.txt
 .allizoM rof skrow reteP
 $ ./tutorial03.py --file foo.txt -d
 .llzM rf skrw rtP


Persistent config files
-----------------------

Our examples so far have been very much about the command line. The whole
point of using ``configman`` is so you can use various config file formats
to provide configuration information to your programs.  The real power of
``configman`` isn't to wrap executable command line scripts but its ability
to work *ecumenically* with config files.

.. sidebar:: admin options
  :subtitle: controlling configman at run time

   ``configman`` adds some command line parameters to your application that
   are used to control ``configman`` itself.  To avoid name collisions with
   command line switches that you define, we've isolated these switches with
   the namespace, ``admin``.

To get started, let's have our program itself write a configuration file
for us.  The easiest way is to use the ``--admin.dump_conf`` option that is
automatically available. It offers different ways to output.

* ``ini``
* ``conf``
* ``json``
* ``xml`` (future enhancement, if requested)

Let's, for the sake of this tutorial, decide to use ``.ini`` files::

 $ ./tutorial03.py --admin.dump_conf=./backwards.ini

This will write out a default configation file in ``ini`` format.
``configman`` figured that out by the file extension that you specified.  If
you had used 'json' instead, ``configman`` would have written out a json file::

 $ ./tutorial03.py --admin.dump_conf=./backwards.ini
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

Any of the command line switches that you specify along with the
``--dump_conf`` switch will appear as the new defaults in the config file
that is written::

 $ python backwards.py --admin.dump_conf=./backwards.ini --file=/tmp/foo.txt
 $ cat backwards.ini
 [top_level]
 # name: devowel
 # doc: Removes all vowels (including Y)
 # converter: configman.converters.boolean_converter
 devowel=False

 # name: file
 # doc: Filename that contains our text
 # converter: str
 file=/tmp/foo.txt

Next, let's make our app always read from this file to get its defaults.  To do
that, we're going to modify what is known as the hierarchy of value sources.
``configman``, when determining what values to give to your option definitions,
uses a list of sources.  By default, it first checks the operating system
environment.  If the names of your options match anything from the environment,
``configman`` will pull those values in, overriding any defaults that you
specified.  Next it looks to the command line.  Any values that it fetches
will override the defaults as well as the environment variables.

If this default hierarchy of value sources doesn't suit you, you may specify
your own hierarchy.  In our example, we're going to want our configuration
file to be the base value source.  Then we want the environment variables and
finally the command line.  We can specify it like this::

 value_sources = ('./backwards.ini', os.environ, getopt)

``configman`` will walk this list, applying the values that it finds in turn.
First it will read your ini file (you may want to use an absolute path to
specify your ini file name).  Second, we pass in a dict that represents the
operating system environment.  Interestingly, you can use any dict-like object
that you want as a source.  Third, we're telling ``configman`` to use the
``getopt`` module to read the command line.  In the future, we'll have the
``argparse`` module available here.

To use this value source, we must specify it in the constructor::

 config_manager = ConfigurationManager(definition,
                                       values_source_list=value_sources)

Now, the program will read from the ``./backwards.ini`` config file whenever
the application is run.

Suppose we change the last line of the file ``backwards.ini`` to
instead say::

 file=/tmp/bar.txt

And then create that file like this::

 $ echo "Socorro" > /tmp/bar.txt

Now, our little program is completely self-sufficient::

 $ ./tutorial04.py
 orrocoS

Even though we're using a config file, that doesn't mean that we've
eliminated the use of the command line.  You can override any configuration
parameter from command line::

 $ ./tutorial04.py --devowel
 rrcS
 $ ./tutorial04.py We both work at Mozilla --file=
 allizoM ta krow htob eW


More advanced options
---------------------

We just covered how to turn a simple application to one where the
configuration is done entirely by a ``ini`` file. Note: we could have
chosen ``json`` or ``conf`` instead of ``ini`` and the program would
be completely unchanged. Only your taste of config file format
changed.

