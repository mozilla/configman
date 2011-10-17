# this is a temporary implementation pending a dynamic discovery implementation

import collections
import os.path
import re

import for_argparse
import for_getopt
import for_json
import for_ini
import for_conf
#import for_xml

dispatch = { 'ini': for_ini,
             'conf': for_conf,
             'json': for_json,
             #'xml': for_xml,
           }

def file_source(file_name):
    position_of_dot = file_name.find('.')
    extension = file_name[position_of_dot+1:]
    return dispatch[extension].ValueSource(file_name)


def wrap(value_source_list):
    wrapped_sources = []
    for a_source in value_source_list:
        wrapped_source = None
        if isinstance(a_source, basestring):
            # this must be a pathname for a config file
            wrapped_source = file_source(a_source)
        elif isinstance(a_source, collections.Mapping):
            # this is dict of some sort
            wrapped_source = mapping_source(a_source)
        elif for_argparse.is_argparse(a_source):
            # this is an argparse object
            wrapped_source = for_argparse.wrap(a_source)
        elif for_getopt.is_getopt(a_source):
            # this is something representing getopt
            wrapped_source = for_getopt.wrap(a_source)

        if wrapped_source:
            wrapped_sources.append(wrapped_source)
    return wrapped_sources
