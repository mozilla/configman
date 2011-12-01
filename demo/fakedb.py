# This is just a hack to simulate the minimal api of psycopg2 for the purposes
# of a demo.  There is nothing of any real interest here, please move along.

class FakeDatabaseObjects(object):
    # This class provides an interface to a fake relational database
    # loosely modeled after the psycopg2 library.  It actually does nothing
    # at all execept offer an API and track if it is in a transaction or not.
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
