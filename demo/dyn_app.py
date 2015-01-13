#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"This sample application demonstrates dynamic class loading with configman."
# there are two ways to invoke this app:
#    .../generic_app.py --admin.application=dyn_app.Dyn_app
#    .../dyn_app.py

# this app simulates passing a group of records from one datasource to
# another.  It offers fake versions of Postgres, MySQL and HBase as the
# data sources and sinks.

from configman import RequiredConfig, Namespace
from configman.converters import class_converter


# the following class embodies the business logic of the application.
class DynApp(RequiredConfig):

    app_name = 'dyn'
    app_version = '0.1'
    app_description = __doc__

    # create the definitions for the parameters that are to come from
    # the command line or config file.
    required_config = Namespace()
    # we're going to have two namespaces, one for the source and another
    # for the destination.  We use separate namespaces to avoid name
    # collisions.  For example, both the source and destination are going
    # to have 'hostname' and we don't want to mix them up.
    required_config.source = s = Namespace()
    required_config.destination = d = Namespace()
    # when the data source class is loaded, it will bring in more
    # configuration parameters gleaned from the loaded class itself.
    s.add_option('storage', 'data_store.CannedDataSource',
                 'the class to handle database interaction for input',
                 short_form='s',
                 from_string_converter=class_converter)
    d.add_option('storage', 'data_store.CannedDataSink',
                 'the class to handle database interaction for output',
                 short_form='d',
                 from_string_converter=class_converter)

    def __init__(self, config):
        super(DynApp, self).__init__()
        self.config = config

    def main(self):
        # the config object now has reference to a source and destination
        # classes. We need to instantiate the classes
        print self.config.source.storage
        source = self.config.source.storage(self.config)
        destination = self.config.destination.storage(self.config)
        # this is the actual functional part of the script.  Read rows from
        # source's 'fetch' iterator and spool them into the destination's
        # write function
        for row in source.fetch():
            destination.write(row)

# if you'd rather invoke the app directly with its source file, this will
# allow it.
if __name__ == "__main__":
    import generic_app
    generic_app.main(DynApp)
