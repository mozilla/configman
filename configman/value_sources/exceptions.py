import configman.config_exceptions as ex

class ValueException(ex.ConfigmanException):
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