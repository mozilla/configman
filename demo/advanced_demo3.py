#!/usr/bin/env python
# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is configman
#
# The Initial Developer of the Original Code is
# Mozilla Foundation
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#    K Lars Lohn, lars@mozilla.com
#    Peter Bengtsson, peterbe@mozilla.com
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

"""This sample app demos wrapping a pluggable database with configman."""
# this is an advanced demo uses configman to allow an app to not only change
# the database implementation at run time, but to change the overall behavior
# of the database.  Three families of classes are used in this demo:
# 1) FakeDatabaseConnection - there is only one member of this family.  It is
#        used to simulate a database.  Understanding this class is unimportant
#        in understanding the rest of the app.  It is just a mock.
# 2) Postgres; PostgresPooled - This two member class hierarchy shows how to
#        wrap a database module with configman to implement a transaction
#        context.
#        * The base class 'Postgres' implements a system where each database
#          connection is opened, used once, and then closed.  Normally, this
#          would be a pretty inefficient way to implement a database intensive
#          application.  However, if an external connection manager is in use,
#          this is a fine model for connection management.
#        * The second class in the hierarchy implements a different connection
#          management strategy.  Here connections are pooled for reuse by name.
#          Defaulting to the model of one connection per thread, it uses the
#          name of the current executing thread as the name of the connection.
#          However the facility exists to name connections with any string.
#          This class implements a more efficient way to run a database
#          intensive app because connections get recycled.
# 3) TransactionExecutor, TransactionExecutorWithBackoff - this two member
#        family implements two behaviors of transactions.
#        * The base class 'TransactionExecutor' is the simple case where a
#          a transaction is submitted and it either succeeds or fails.
#        * The derived class 'TransactionExecutorWithBackoff' will try to
#          execute a transaction.  If it succeeds, it does nothing more.  If it
#          fails with a database operational error (connection lost, socket
#          timeout), the transaction is retried over and over util it
#          suceeds.  Between each subsequent retry, execution sleeps for a set
#          or progressive number of seconds.  Exceptions deemed non-operational
#          are passed out to the application and do not trigger retries.
# The latter two class families are settable using configman at run time.  The
# demo app logs its actions, so we suggest trying different combinations of the
# Postgres and TransactionExecutor families to observe how they differ in
# behavior

import contextlib
import threading
import random
import time
import socket

from configman import RequiredConfig, ConfigurationManager, Namespace


#------------------------------------------------------------------------------
class FakeDBOperationalError(Exception):
    pass


#------------------------------------------------------------------------------
class FakeDBProgrammingError(Exception):
    pass


#------------------------------------------------------------------------------
class FakeDatabaseConnection():
    """this class substitutes for a real database connection"""
    # understanding the inner workings of this class is unimportant for this
    # demo.  It is just a mock for a real database connection used to make the
    # demo easier to run.
    #--------------------------------------------------------------------------
    def __init__(self, dsn):
        print "FakeDatabaseConnection - created"
        self.connection_open = True
        self.in_transaction = False

    #--------------------------------------------------------------------------
    def close(self):
        if self.connection_open:
            print "FakeDatabaseConnection - closed connection"
            self.connection_open = False
        else:
            print "FakeDatabaseConnection - already closed"

    #--------------------------------------------------------------------------
    def query(self, query):

        if self.connection_open:
            print "FakeDatabaseConnection - trying query..."
            if random.randint(1, 2) == 1:
                raise FakeDBOperationalError("can't connect to database")
            print 'FakeDatabaseConnection - yep, we did your query <wink>'
            self.in_transaction = True
        else:
            print "FakeDatabaseConnection - can't query a closed connection"
            raise FakeDBProgrammingError("can't query a closed connection")

    #--------------------------------------------------------------------------
    def commit(self):
        print "FakeDatabaseConnection - commit"
        self.in_transaction = False

    #--------------------------------------------------------------------------
    def rollback(self):
        print "FakeDatabaseConnection - rollback"
        self.in_transaction = False


#==============================================================================
class Postgres(RequiredConfig):
    """a configman compliant class for setup of Postgres transactions"""
    #--------------------------------------------------------------------------
    # configman parameter definition section
    # here we're setting up the minimal parameters required for connecting
    # to a database.
    required_config = Namespace()
    required_config.add_option(
        name='database_host',
        default='localhost',
        doc='the hostname of the database',
    )
    required_config.add_option(
        name='database_name',
        default='breakpad',
        doc='the name of the database',
    )
    required_config.add_option(
        name='database_port',
        default=5432,
        doc='the port for the database',
    )
    required_config.add_option(
        name='database_user',
        default='breakpad_rw',
        doc='the name of the user within the database',
    )
    required_config.add_option(
        name='database_password',
        default='secrets',
        doc="the user's database password",
    )

    #--------------------------------------------------------------------------
    def __init__(self, config, local_config):
        """Initialize the parts needed to start making database connections

        parameters:
            config - the complete config for the app.  If a real app, this
                     would be where a logger or other resources could be
                     found.
            local_config - this is the namespace within the complete config
                           where the actual database parameters are found"""
        super(Postgres, self).__init__()
        self.dsn = ("host=%(database_host)s "
                    "dbname=%(database_name)s "
                    "port=%(database_port)s "
                    "user=%(database_user)s "
                    "password=%(database_password)s") % local_config
        self.operational_exceptions = (FakeDBOperationalError,
                                       socket.timeout)

    #--------------------------------------------------------------------------
    def connection(self, name_unused=None):
        """return a new database connection

        parameters:
            name_unused - optional named connections.  Used by the
                          derived class
        """
        return FakeDatabaseConnection(self.dsn)

    #--------------------------------------------------------------------------
    @contextlib.contextmanager
    def __call__(self, name=None):
        """returns a database connection wrapped in a contextmanager.

        This function allows database connections to be used in a with
        statement.  Connection/transaction objects will automatically be
        rolled back if they weren't explicitly committed within the context of
        the 'with' statement.  Additionally, it is equipped with the ability to
        automatically close the connection when leaving the 'with' block.

        parameters:
            name - an optional name for the database connection"""
        exception_raised = False
        conn = self.connection(name)
        try:
            yield conn
        except self.operational_exceptions:
            # we need to close the connection
            print "Postgres - operational exception caught"
            exception_raised = True
        except Exception:
            print "Postgres - non operational exception caught"
            exception_raised = True
        finally:
            if not exception_raised:
                try:
                    if conn.in_transaction:
                        conn.rollback()
                    self.close_connection(conn)
                except self.operational_exceptions:
                    exception_raised = True
            if exception_raised:
                try:
                    self.close_connection(conn, force=True)
                except self.operational_exceptions:
                    pass
                raise

    #--------------------------------------------------------------------------
    def close_connection(self, connection, force=False):
        """close the connection passed in.

        This function exists to allow derived classes to override the closing
        behavior.

        parameters:
            connection - the database connection object
            force - unused boolean to force closure; used in derived classes
        """
        print "Postgres - requestng connection to close"
        connection.close()

    #--------------------------------------------------------------------------
    def close(self):
        """close any pooled or cached connections.  Since this base class
        object does no caching, there is no implementation required.  Derived
        classes may implement it."""
        pass


#==============================================================================
class PostgresPooled(Postgres):
    """a configman compliant class that pools Postgres database connections"""
    #--------------------------------------------------------------------------
    def __init__(self, config, local_config):
        super(PostgresPooled, self).__init__(config, local_config)
        print "PostgresPooled - setting up connection pool"
        self.pool = {}

    #--------------------------------------------------------------------------
    def connection(self, name=None):
        """return a named connection.

        This function will return a named connection by either finding one
        in its pool by the name or creating a new one.  If no name is given,
        it will use the name of the current executing thread as the name of
        the connection.

        parameters:
            name - a name as a string
        """
        if not name:
            name = threading.currentThread().getName()
        if name in self.pool:
            return self.pool[name]
        self.pool[name] = FakeDatabaseConnection(self.dsn)
        return self.pool[name]

    #--------------------------------------------------------------------------
    def close_connection(self, connection, force=False):
        """overriding the baseclass function, this routine will decline to
        close a connection at the end of a transaction context.  This allows
        for reuse of connections."""
        if force:
            print 'PostgresPooled - delegating connection closure'
            try:
                super(PostgresPooled, self).close_connection(connection,
                                                                  force)
            except self.operational_exceptions:
                print 'PostgresPooled - failed closing'
            for name, conn in self.pool.iteritems():
                if conn is connection:
                    break
            del self.pool[name]
        else:
            print 'PostgresPooled - refusing to close connection'

    #--------------------------------------------------------------------------
    def close(self):
        """close all pooled connections"""
        print "PostgresPooled - shutting down connection pool"
        for name, conn in self.pool.iteritems():
            conn.close()
            print "PostgresPooled - connection %s closed" % name


#------------------------------------------------------------------------------
def transaction_factory(config, local_config, args):
    """instantiate a transaction object that will create database
    connections

    This function will be associated with an Aggregation object.  It will
    look at the value of the 'database' option which is a reference to one
    of Postgres or PostgresPooled from above.  This function will
    instantiate the class
    """
    return local_config.database_class(config, local_config)


#==============================================================================
class TransactionExecutor(RequiredConfig):
    required_config = Namespace()
    # setup the option that will specify which database connection/transaction
    # factory will be used.  Config man will query the class for additional
    # config options for the database connection parameters.
    required_config.add_option('database_class',
                               default=Postgres,
                               doc='the database connection source')
    # this Aggregation will actually instantiate the class in the preceding
    # option called 'database'.  Once instantiated, it will be available as
    # 'db_transaction'.  It will then be used as a source of database
    # connections cloaked as a context.
    required_config.add_aggregation(
        name='db_transaction',
        function=transaction_factory)

    #--------------------------------------------------------------------------
    def __init__(self, config):
        self.config = config

    #--------------------------------------------------------------------------
    def do_transaction(self, function, *args, **kwargs):
        """execute a function within the context of a transaction"""
        with self.config.db_transaction() as trans:
            function(trans, *args, **kwargs)


#==============================================================================
class TransactionExecutorWithBackoff(TransactionExecutor):
    # back off times
    required_config = Namespace()
    required_config.add_option('backoff_delays',
                               default=[2, 4, 6, 10, 15],
                               doc='delays in seconds between retries',
                               from_string_converter=eval)
    # wait_log_interval
    required_config.add_option('wait_log_interval',
                               default=1,
                               doc='seconds between log during retries')

    #--------------------------------------------------------------------------
    def backoff_generator(self):
        """Generate a series of integers used for the length of the sleep
        between retries.  It produces after exhausting the list, it repeats
        the last value from the list forever.  This generator will never raise
        the StopIteration exception."""
        for x in self.config.backoff_delays:
            yield x
        while True:
            yield self.config.backoff_delays[-1]

    #--------------------------------------------------------------------------
    def responsive_sleep(self, seconds, wait_reason=''):
        """Sleep for the specified number of seconds, logging every
        'wait_log_interval' seconds with progress info."""
        for x in xrange(int(seconds)):
            if (self.config.wait_log_interval and
                not x % self.config.wait_log_interval):
                print '%s: %dsec of %dsec' % (wait_reason,
                                              x,
                                              seconds)
            time.sleep(1.0)

    #--------------------------------------------------------------------------
    def do_transaction(self, function, *args, **kwargs):
        """execute a function within the context of a transaction"""
        for wait_in_seconds in self.backoff_generator():
            try:
                with self.config.db_transaction() as trans:
                    function(trans, *args, **kwargs)
                    trans.commit()
                    break
            except self.config.db_transaction.operational_exceptions:
                pass
            print ('failure in transaction - retry in %s seconds' %
                   wait_in_seconds)
            self.responsive_sleep(wait_in_seconds,
                                  "waiting for retry after failure in "
                                  "transaction")


#------------------------------------------------------------------------------
def query1(conn):
    """a transaction to be executed by the database"""
    conn.query('select * from life')


#------------------------------------------------------------------------------
def query2(conn):
    """another transaction to be executed by the database"""
    raise Exception("not a database related error")

#==============================================================================
if __name__ == "__main__":
    definition_source = Namespace()
    definition_source.add_option('transaction_executor_class',
                                 default=TransactionExecutorWithBackoff,
                                 doc='a class that will execute transactions')

    c = ConfigurationManager(definition_source,
                             app_name='advanced_demo_3',
                             app_description=__doc__)

    with c.context() as config:
        # the configuration has a class that can execute transactions
        # we instantiate it here.
        executor = config.transaction_executor_class(config)

        # this first query has a 50% probability of failing due to a database
        # connectivity problem.  If the transaction_executor_class is a class
        # with backing off retry, you'll see the transaction tried over and
        # over until it succeeds.
        print "\n**** First query"
        executor.do_transaction(query1)

        # this second query has a 50% probability of failing due to a non-
        # database problem.  Because the exception raised is not recoverable
        # by the database, it won't get retried even if the
        # transaction_executor_class has the capability
        print "\n**** Second query"
        executor.do_transaction(query2)

        print "\n**** about to leave the config context"
