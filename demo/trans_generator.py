import contextlib

from configman import Namespace, ConfigurationManager

class FakeDatabaseObjects(object):
    @staticmethod
    def connection(dsn):
        print 'connnected to database with "%s"' % dsn
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
        print 'commiting transaction'

    @staticmethod
    def rollback():
        print 'rolling back transaction'


def transaction_context_factory(dsn_dict):
    dsn = ("host=%(host)s "
           "dbname=%(dbname)s "
           "user=%(user)s "
           "password=%(password)s") % dsn_dict
    @contextlib.contextmanager
    def transaction_context():
        conn = FakeDatabaseObjects.connect(dsn)
        yield conn
        status = conn.get_transaction_status()
        if status == psycopg2.extensions.STATUS_IN_TRANSACTION:
            conn.rollback()
        conn.close()

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
      short_form='n'
    )
    definition.add_option(
      name='user',
      default='',
      doc='the name of the user within the database',
      short_form='n'
    )
    definition.add_option(
      name='password',
      default='',
      doc='the name of the database',
      short_form='n'
    )
    definition.add_option(
      name='transaction_context',
      default=dsn_dict,
      from_string_converter=transaction_context_factory,
      template=True
    )
    return definition


if __name__ == '__main__':
    definition = define_config()
    config_manager = ConfigurationManager(definition)
    config = config_manager.get_config()

    with config.transaction_context() as dbconn:
        cursor = dbconn.cursor()
        cursor.execute('select * from pg_tables')
        dbconn.commit()

    with config.transaction_context() as dbconn:
        cursor = dbconn.cursor()
        cursor.execute('select * from pg_tables')




















self.dsn = "host=%(databaseHost)s port=%(databasePort)s dbname=%(databaseName)s user=%(databaseUserName)s password=%(databasePassword)s" % config
