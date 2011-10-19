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
