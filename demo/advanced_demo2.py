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

"""This sample application demonstrates configuration as context."""
# this is an advanced demo that demonstrates using contextmanager with the
# configuration manager.  This is very useful in the case where the
# configuration includes objects that need to be shut down or closed at the
# before the end of the app.  Database connections are a perfect example.
# Using this contextmanager system, database connection closing is  automatic
# and guaranteed at when the app completes.

import contextlib
import threading

from configman import RequiredConfig, ConfigurationManager, Namespace

#------------------------------------------------------------------------------
class FakeDatabaseConnection():
    """this class substitutes for a real database connection"""
    def __init__(self, dsn):
        print "FakeDatabaseConnection - created"
        self.connection_open = True
        self.in_transaction = False

    def close(self):
        if self.connection_open:
            print "FakeDatabaseConnection - closed connection"
            self.connection_open = False
        else:
            print "FakeDatabaseConnection - already closed"

    def query(self, query):
        if self.connection_open:
            print 'FakeDatabaseConnection - yep, we did your query <wink>'
            self.in_transaction = True
        else:
            print "FakeDatabaseConnection - you can't query a close connection"

    def commit(self):
        print "FakeDatabaseConnection - commit"
        self.in_transaction = False

    def rollback(self):
        print "FakeDatabaseConnection - rollback"
        self.in_transaction = False


#==============================================================================
class PGTransaction(RequiredConfig):
    """a configman complient class for setup of a Postgres transaction"""
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
        doc='the name of the database',
    )
    required_config.add_option(
        name='database_user',
        default='breakpad_rw',
        doc='the name of the user within the database',
    )
    required_config.add_option(
        name='database_password',
        default='secrets',
        doc='the name of the database',
    )

    #--------------------------------------------------------------------------
    def __init__(self, config, local_config):
        super(PGTransaction, self).__init__()
        self.dsn = ("host=%(database_host)s "
                    "dbname=%(database_name)s "
                    "port=%(database_port)s "
                    "user=%(database_user)s "
                    "password=%(database_password)s") % local_config

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
        conn = self.connection(name)
        try:
            yield conn
        finally:
            if conn.in_transaction:
                conn.rollback()
            self.close_connection(conn)

    #--------------------------------------------------------------------------
    def close_connection(self, connection):
        """close the connection passed in.

        This function exists to allow derived classes to override the closing
        behavior.

        parameters:
            connection - the database connection object
        """
        print "PGTransaction - requestng connection to close"
        connection.close()

    #--------------------------------------------------------------------------
    def close(self):
        """close any pooled or cached connections.  Since this base class
        object does no caching, there is no implementation required.  Derived
        classes may implement it."""
        pass


#==============================================================================
class PGPooledTransaction(PGTransaction):
    """a condigman compliant class that pools database connections"""
    #--------------------------------------------------------------------------
    def __init__(self, config, local_config):
        super(PGPooledTransaction, self).__init__(config, local_config)
        print "PGPooledTransaction - setting up connection pool"
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
    def close_connection(self, connection):
        """overriding the baseclass function, this routine will decline to
        close a connection at the end of a transaction context.  This allows
        for reuse of connections."""
        print 'PGPooledTransaction - refusing to close connection'

    #--------------------------------------------------------------------------
    def close(self):
        """close all pooled connections"""
        print "PGPooledTransaction - shutting down connection pool"
        for name, conn in self.pool.iteritems():
            conn.close()
            print "PGPooledTransaction - connection %s closed" % name


#------------------------------------------------------------------------------
def transaction_factory(config, local_config, args):
    """instantiate a transaction object that will create database connections

    This function will be associated with an Aggregation object.  It will look
    at the value of the 'database' option which is a reference to one of
    PGTransaction or PGPooledTransaction from below.  This function will
    instantiate the class
    """
    return local_config.database(config, local_config)

if __name__ == "__main__":

    definition_source = Namespace()
    # setup the option that will specify which database connection/transaction
    # factory will be used.  Condfig man will query the class for additional
    # config options for the database connection parameters.
    definition_source.add_option('database',
                                 default=PGTransaction,
                                 doc='the database connection source',
                                 short_form='d')
    # this Aggregation will actually instatiate the class in the preceding
    # option called 'database'.  Once instantiated, it will be available as
    # 'db_transaction'.  It will then be used as a source of database
    # connections cloaked as a context.
    definition_source.add_aggregation(
        name='db_transaction',
        function=transaction_factory
    )

    c = ConfigurationManager(definition_source,
                             app_name='demo4',
                             app_description=__doc__)
    with c.context() as config:
        print "\n**** First query will succeed"
        with config.db_transaction() as trans:
            trans.query('select * from life')
            trans.commit()

        print "\n**** Second query will fail"
        with config.db_transaction() as trans:
            trans.query('select * from life')

        print "\n**** about to leave the config context"
