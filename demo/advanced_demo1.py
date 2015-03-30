#!/usr/bin/env python
import contextlib

from configman import Namespace, ConfigurationManager
from fakedb import FakeDatabaseObjects


# this is the interesting function in this example.  It is used as a
# from aggregation function for an Aggregation object that live within a
# configman's option definition.  It takes a database connection string (DSN)
# and emits a fuction that returns a database connection object wrapped
# in a contextmanager.  This allows a configuration value to serve as a
# factory for database transaction objects suitable for use in a 'with'
# statement.
def transaction_context_factory(config_unused, local_namespace, args_unused):
    dsn = ("host=%(host)s "
           "dbname=%(dbname)s "
           "user=%(user)s "
           "password=%(password)s") % local_namespace

    @contextlib.contextmanager
    def transaction_context():
        conn = FakeDatabaseObjects.connect(dsn)
        try:
            yield conn
        finally:
            status = conn.get_transaction_status()
            if status == FakeDatabaseObjects.STATUS_IN_TRANSACTION:
                conn.rollback()
            conn.close()
    return transaction_context


# this function defines the connection parameters required to connect to
# a database.
def define_config():
    definition = Namespace()
    # here we're setting up the minimal parameters required for connecting
    # to a database.
    definition.add_option(
      name='host',
      default='localhost',
      doc='the hostname of the database',
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
    # This final aggregation object is the most interesting one.  Its final
    # value depends on the final values of options within the same Namespace.
    # After configman is done doing all its value overlays, there is
    # one final pass through the option definitions with the sole purpose of
    # expanding the Aggregations.  To do so, the Aggregations' aggregation_fn
    # is called passing the whole config set to the function.  That function
    # can then use any values within the config values to come up with its
    # own value.  In this case, the function returns a factory function that
    # return functions that return database connections wrapped in
    # contextmanagers.
    definition.add_aggregation(
      name='db_transaction',
      function=transaction_context_factory
    )
    return definition


if __name__ == '__main__':
    definition = define_config()
    config_manager = ConfigurationManager(definition)
    config = config_manager.get_config()

    # In this example we do two transactions.
    # This first one succeeds so we call the 'commit' function to indicate
    # that fact.  The actions in the database are logged to stdout, you can
    # see the order of events: connection opens, we fetch a cursor, we execute
    # some sql, we commit the transaction and the connection
    # is automatically closed
    try:
        with config.db_transaction() as transaction:
            cursor = transaction.cursor()
            cursor.execute('select * from pg_tables')
            transaction.commit()
    except Exception, x:
        print str(x)

    # This second transaction fails with a (contrived) exception being raised.
    # Because no commit was called during the context of the 'with' statement,
    # the transaction will be automatically rolled back. This behavior is shown
    # in the stdout logging when the app is run:
    try:
        with config.db_transaction() as transaction:
            cursor = transaction.cursor()
            cursor.execute('select * from pg_tables')
            raise Exception("we failed for some reason")
    except Exception, x:
        print str(x)
