#!/usr/bin/env python
import contextlib

from configman import Namespace, ConfigurationManager

class FakeDatabaseObjects(object):
    # This class provides an interface to a fake relational database
    # loosely modeled after the psycopg2 library.  It actually does nothing
    # at all execept offer an API and track if it is in a transaction or not.
    # It can be ignored as it is just support for the more interesting
    # example code that follows
    in_transaction = 0
    @staticmethod
    def connect(dsn):
        print 'connnected to database with "%s"' % dsn
        FakeDatabaseObjects.in_transaction = 1
        return FakeDatabaseObjects

    @staticmethod
    def cursor():
        print 'new cursor created'
        return FakeDatabaseObjects

    @staticmethod
    def execute(sql):
        print 'executing: "%s"' % sql

    @staticmethod
    def close():
        print 'closing connection'

    @staticmethod
    def commit():
        FakeDatabaseObjects.in_transaction = 0
        print 'commiting transaction'

    @staticmethod
    def rollback():
        FakeDatabaseObjects.in_transaction = 0
        print 'rolling back transaction'

    @staticmethod
    def get_transaction_status():
        return FakeDatabaseObjects.in_transaction

    STATUS_IN_TRANSACTION = 1

# this is the interesting function in this example.  It is used as a
# from string converter.  It takes a database connection string (DSN)
# and emits a fuction that returns a database connection object wrapped
# in a contextmanager.  This allows a configuration value to serve as a
# factory for database transaction objects suitable for use in a 'with'
# statement.
def transaction_context_factory(dsn):
    @contextlib.contextmanager
    def transaction_context():
        conn = FakeDatabaseObjects.connect(dsn)
        yield conn
        status = conn.get_transaction_status()
        if status == FakeDatabaseObjects.STATUS_IN_TRANSACTION:
            conn.rollback()
        conn.close()
    return transaction_context

# this function defines the connection parameters required to connect to
# a database.
def define_config():
    definition = Namespace()
    definition.add_option(
      name='host',
      default='localhost',
      doc='the hostname of the database',
      short_form='h'
    )
    definition.add_option(
      name='dbname',
      default='',
      doc='the name of the database',
      short_form='d'
    )
    definition.add_option(
      name='user',
      default='',
      doc='the name of the user within the database',
      short_form='u'
    )
    definition.add_option(
      name='password',
      default='',
      doc='the name of the database',
      short_form='p'
    )
    dsn_template = ("host=%(host)s "
                    "dbname=%(dbname)s "
                    "user=%(user)s "
                    "password=%(password)s")
    # This final option is the most interesting one.  Note that it is marked
    # as a template option.  That means that its value depends on the final
    # values of the other options within the same Namespace.  After configman
    # is done making all its overlays, there is one final pass through the
    # option definitions with the sole purpose of expanding these templated
    # values.  Just like other options, once it has its final value, the
    # from_string_converter is applied.  In this case, the coverter is the
    # database transaction factory function from above.
    definition.add_option(
      name='transaction_context',
      default=dsn_template,
      from_string_converter=transaction_context_factory,
      is_template=True
    )
    return definition


if __name__ == '__main__':
    definition = define_config()
    config_manager = ConfigurationManager(definition)
    config = config_manager.get_config()

    # In this example we do two transactions.
    # This first one succeeds because we called the 'commit' function.
    # The actions are logged to stdout, you can see that connection opens,
    # some actions happen, the transaction commits and the connection
    # is automatically closed
    try:
        with config.transaction_context() as dbconn:
            cursor = dbconn.cursor()
            cursor.execute('select * from pg_tables')
            dbconn.commit()
    except Exception, x:
        print str(x)

    try:
        with config.transaction_context() as dbconn:
            cursor = dbconn.cursor()
            cursor.execute('select * from pg_tables')
            raise Exception("we failed for some reason")
    except Exception, x:
        print str(x)
