from .. import config_exceptions


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
