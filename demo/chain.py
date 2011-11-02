import os
import datetime
from configman import Namespace, ConfigurationManager
from configman.namespace import Namespace
from configman import ConfigurationManager
from configman import config_manager

def to_conf(config):
    filename = 'sample-chain.conf'
    if os.path.isfile(filename):
        os.remove(filename)
    with open(filename, 'w') as f:
        config.write_conf(f)
    return filename

def from_conf(filename):
    assert os.path.isfile(filename)
    g = config_manager.OptionsByConfFile(filename)
    return ConfigurationManager([n], [g])

def to_ini(config):
    filename = 'sample-chain.ini'
    if os.path.isfile(filename):
        os.remove(filename)
    with open(filename, 'w') as f:
        config.write_ini(f)
    return filename

def from_ini(filename):
    assert os.path.isfile(filename)
    g = config_manager.OptionsByIniFile(filename)
    return ConfigurationManager([n], [g])

def to_json(config):
    filename = 'sample-chain.json'
    if os.path.isfile(filename):
        os.remove(filename)
    with open(filename, 'w') as f:
        config.write_json(f)
    return filename

def from_json(filename):
    assert os.path.isfile(filename)
    return config_manager.ConfigurationManager(
      [open(filename).read()],
    )

n = Namespace()
n.add_option('name')
n.add_option('age', doc="Age in years")
n.add_option('password')
n.add_option('bday', default=datetime.date(1979, 12, 13))

def start():
    ## 1. Set up a config
    orig_config = config = ConfigurationManager([n])
    assert orig_config.option_definitions == config.option_definitions

    config2 = ConfigurationManager([n])
    assert orig_config.option_definitions == config.option_definitions

    # Config file
    filename = to_conf(config)
    print "\tCreated", filename
    config = from_conf(filename)
    assert config.option_definitions == orig_config.option_definitions

    # INI file
    filename = to_ini(config)
    print "\tCreated", filename
    config = from_ini(filename)
    assert config.option_definitions == orig_config.option_definitions

    # JSON
    filename = to_json(config)
    print "\tCreated", filename
    config = from_json(filename)
    from pprint import pprint
    pprint(config.option_definitions)
    pprint(orig_config.option_definitions)
    assert config.option_definitions == orig_config.option_definitions





if __name__ == '__main__':
    start()
