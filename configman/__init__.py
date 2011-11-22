__version__ = '0.0.1'

# Having these here makes it possible to easily import once configman is
# installed.
# For example::
#
#    from configman import Namespace, ConfigurationManager
#

from .config_manager import ConfigurationManager
from .namespace import Namespace


# constants used to refer to Value Source concepts generically
from config_file_future_proxy import ConfigFileFutureProxy
from os import environ as environment
import getopt as command_line

