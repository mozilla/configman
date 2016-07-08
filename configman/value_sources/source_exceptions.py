# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function

from configman import config_exceptions


class ValueException(config_exceptions.ConfigmanException):
    pass


class NotEnoughInformationException(ValueException):
    pass


class LoadingIniFileFailsException(ValueException):
    pass


class UnknownFileExtensionException(ValueException):
    pass


class ModuleHandlesNothingException(ValueException):
    pass


class NoHandlerForType(ValueException):
    pass


class AllHandlersFailedException(ValueException):
    pass


class CantHandleTypeException(ValueException):
    pass


class UnknownFileExtension(ValueException):
    pass
