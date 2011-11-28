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

"""This file is the source of the simulated database classes used in the
dyn_app example."""

import sys
import datetime as dt

import configman.config_manager as cm
import configman.namespace as ns
import configman.converters as conv

def log(message):
    print >>sys.stderr, dt.datetime.now(), message


class Database(cm.RequiredConfig):
    """This is the base class for the Postgres and MySQL simulators.  It
    defines the common config parameters and implements the input and
    output functions. Since these are fake and don't really connect to
    any database, we arbitrarily chose to use a tuple as a "connection"
    object"""
    # setup common config parameters to be used by Postgres and MySQL
    required_config = ns.Namespace()
    required_config.add_option('hostname', 'localhost', 'the hostname')
    required_config.add_option('username', 'fred', 'the username')
    required_config.add_option('password', 'secrets', 'the password')

    def __init__(self, config):
        super(Database, self).__init__()
        self.config = config
        self.class_as_string = conv.py_obj_to_str(self.__class__)
        self.connection = (0, 0)

    def canned_query(self):
        """a generator that yield simulated database rows, logging each one"""
        for i in range(*self.connection):
            row = (i, i*10, chr(i+32))
            log('%s fetching row: %s' % (self.class_as_string, row))
            yield row

    def write(self, row):
        """since this is a simulation, no actual insert take place.  We just
        log that we've gotten a row to insert"""
        log('%s inserting: %s' % (self.class_as_string, row))

class Postgres(Database):
    required_config = ns.Namespace()
    # we setup the 'port' config parameter to match the default Postgres
    # port number.
    required_config.add_option('port', 5432, 'the connection port')

    def __init__(self, config):
        super(Postgres, self).__init__(config)
        log('connecting to Fake Postgres with %s' % self.class_as_string)
        self.connection = (10,20)


class MySQL(Database):
    required_config = ns.Namespace()
    # we setup the 'port' config parameter to match the default MySQL
    # port number.
    required_config.add_option('port', 3306, 'the connection port')

    def __init__(self, config):
        super(MySQL, self).__init__(config)
        log('connecting to Fake MySQL with %s' % self.class_as_string)
        self.connection = (50,60)


class HBase(cm.RequiredConfig):
    """Since HBase isn't really a relational database, we use a separate
    class hierarchy for it."""
    required_config = ns.Namespace()
    required_config.add_option('hostname', 'localhost', 'the HBase hostname')
    required_config.add_option('port', 9090, 'the HBase port')

    def __init__(self, config):
        super(HBase, self).__init__()
        self.class_as_string = conv.py_obj_to_str(self.__class__)
        self.config = config
        log('connecting to Fake HBase with %s' % self.class_as_string)
        self.connection = (100, 90, -1)

    def canned_query(self):
        for i in range(*self.connection):
            log('%s fetching row: %s' % (self.class_as_string, i))
            yield i, i*10, chr(i+32)

    def write(self, row):
        log('%s inserting %s' % (self.class_as_string, str(row)))


class CannedDataSource(cm.RequiredConfig):
    required_config = ns.Namespace()
    required_config.add_option('database_type', 'data_store.Postgres',
                               'the type of database to connect to',
                               from_string_converter=conv.class_converter)

    def __init__(self, config):
        print self.__class__
        self.class_as_string = conv.py_obj_to_str(self.__class__)
        log('starting %s' % self.class_as_string)
        self.config = config
        self.datasource = config.source.database_type(config)

    def fetch(self):
        log('starting fetch from %s' % self.class_as_string)
        return self.datasource.canned_query()

class CannedDataSink(cm.RequiredConfig):
    required_config = ns.Namespace()
    required_config.add_option('database_type', 'data_store.HBase',
                               'the type of database to connect to',
                               from_string_converter=conv.class_converter)

    def __init__(self, config):
        self.class_as_string = conv.py_obj_to_str(self.__class__)
        log('starting %s' % self.class_as_string)
        self.config = config
        self.data_sink = config.destination.database_type(config)

    def write(self, row):
        self.data_sink.write(row)