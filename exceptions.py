#==============================================================================
class ConfigFileMissingError (IOError):
    pass


#==============================================================================
class ConfigFileOptionNameMissingError (Exception):
    pass


#==============================================================================
class NotAnOptionError (Exception):
    pass


#==============================================================================
class OptionError (Exception):
    pass


#==============================================================================
class CannotConvert (ValueError):
    pass


