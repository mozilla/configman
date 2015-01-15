# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from os import path
with open(path.join(path.dirname(__file__), 'version.txt')) as f:
    __version__ = f.read().strip()

# Having these here makes it possible to easily import once configman is
# installed.
# For example::
#
#    from configman import Namespace, ConfigurationManager
#

from configman.config_manager import ConfigurationManager
from configman.required_config import RequiredConfig
from configman.namespace import Namespace
from configman.config_file_future_proxy import ConfigFileFutureProxy
from configman.converters import (
    class_converter,
    regex_converter,
    timedelta_converter
)
from configman.environment import environment
from configman.command_line import command_line


#------------------------------------------------------------------------------
def configuration(*args, **kwargs):
    """this function just instantiates a ConfigurationManager and returns
    the configuration dictionary.  It accepts all the same parameters as the
    constructor for the ConfigurationManager class."""
    try:
        config_kwargs = {'mapping_class': kwargs.pop('mapping_class')}
    except KeyError:
        config_kwargs = {}
    cm = ConfigurationManager(*args, **kwargs)
    return cm.get_config(**config_kwargs)

