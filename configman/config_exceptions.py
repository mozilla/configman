# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function


class ConfigmanException(Exception):
    pass


class ConfigFileMissingError(IOError, ConfigmanException):
    pass


class ConfigFileOptionNameMissingError(ConfigmanException):
    pass


class NotAnOptionError(ConfigmanException):
    pass


class OptionError(ConfigmanException):
    pass


class CannotConvertError(ConfigmanException):
    pass
