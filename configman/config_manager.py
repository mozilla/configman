#!/usr/bin/env python

import re
import sys
import os
import collections
import json
import inspect
import os.path
import functools

import converters as conv
import config_exceptions as exc
import value_sources
import def_sources

#==============================================================================
# for convenience define some external symbols here
from option import Option
from dotdict import DotDict
from namespace import Namespace


#==============================================================================
class RequiredConfig(object):
    #--------------------------------------------------------------------------
    @classmethod
    def get_required_config(cls):
        result = {}
        for a_class in cls.__mro__:
            try:
                result.update(a_class.required_config)
            except AttributeError:
                pass
        return result

    #--------------------------------------------------------------------------
    def config_assert(self, config):
        for a_parameter in self.required_config.keys():
            assert a_parameter in config, \
                   '%s missing from config' % a_parameter


#==============================================================================
class ConfigurationManager(object):

    #--------------------------------------------------------------------------
    def __init__(self,
                 definition_source=None,
                 values_source_list=None,
                 argv_source=None,
                 #use_config_files=True,
                 use_auto_help=True,
                 manager_controls=True,
                 quit_after_admin=True,
                 options_banned_from_help=None,
                 app_name=None,
                 app_version=None,
                 app_description=None
                 ):
        # instead of allowing mutables as default keyword argument values...
        if definition_source is None:
            definition_source_list = []
        elif (isinstance(definition_source, collections.Sequence) and
              not isinstance(definition_source, basestring)):
            definition_source_list = list(definition_source)
        else:
            definition_source_list = [definition_source]

        if values_source_list is None:
            values_source_list = []
        if argv_source is None:
            argv_source = sys.argv[1:]
        if options_banned_from_help is None:
            options_banned_from_help = ['_application']


        self.argv_source = argv_source
        self.option_definitions = Namespace()
        self.definition_source_list = definition_source_list

        self.use_auto_help = use_auto_help
        self.help_done = False
        self.admin_tasks_done = False
        self.manager_controls = manager_controls
        self.manager_controls_list = ['help', '_write', 'config_path',
                                      '_application']
        self.options_banned_from_help = options_banned_from_help

        if self.use_auto_help:
            self.setup_auto_help()
        if manager_controls:
            self.setup_manager_controls()

        for a_definition_source in self.definition_source_list:
            def_sources.setup_definitions(a_definition_source,
                                          self.option_definitions)

        if values_source_list:
            self.custom_values_source = True
        else:
            import getopt
            self.custom_values_source = False
            self.values_source_list = [os.environ,
                                       getopt,
                                      ]
        self.values_source_list = value_sources.wrap(values_source_list,
                                                     self)

        # first pass to get classes & config path - ignore bad options
        self.overlay_settings(ignore_mismatches=True)

        # walk tree expanding class options
        self.walk_expanding_class_options()

        # the app_name, app_version and app_description are to come from
        # if '_application' option if it is present.  If it is not present,
        # get the app_name,et al, from parameters passed into the constructor.
        # if those are empty, set app_name, et al, to empty strings
        try:
            app_option = self.get_option_by_name('_application')
            self.app_name = getattr(app_option.value, 'app_name', '')
            self.app_version = getattr(app_option.value, 'app_version', '')
            self.app_description = getattr(app_option.value,
                                           'app_description', '')
        except exc.NotAnOptionError:
            # there is no '_application' option, get the 'app_name'
            # from the parameters passed in, if they exist.
            self.app_name = app_name if app_name else ''
            self.app_version = app_version if app_version else ''
            self.app_description = app_description if app_description else ''

        # second pass to include config file values - ignore bad options
        self.overlay_settings(ignore_mismatches=True)

        # walk tree expanding class options
        self.walk_expanding_class_options()

        # third pass to get values - complain about bad options
        self.overlay_settings(ignore_mismatches=False)

        if self.use_auto_help and self.get_option_by_name('help').value:
            self.output_summary()
            self.help_done = True
            self.admin_tasks_done = True

        if manager_controls and self.get_option_by_name('_write').value:
            self.write_config()
            admin_tasks_done = True

        if quit_after_admin and self.admin_tasks_done:
            exit()

    #--------------------------------------------------------------------------
    #def read_config_files(self):
        ## try ini file
        #try:
            #app = self.get_option_by_name('_application')
            #application_name = app.value.app_name
        #except (AttributeError, KeyError):
            #self.ini_source = None
            #self.conf_source = None
            #self.json_source = None
            #return
        #path = self.get_option_by_name('config_path').value
        #file_name = os.path.join(path, '%s.ini' % application_name)
        #self.ini_source = IniValueSource(file_name)
        ## try conf file
        #file_name = os.path.join(path, '%s.conf' % application_name)
        #self.conf_source = ConfValueSource(file_name)
        ## try json file
        #file_name = os.path.join(path, '%s.json' % application_name)
        #try:
            #with open(file_name) as j_file:
                #self.json_source = json.load(j_file)
        #except IOError:
            #self.json_source = {}

    #--------------------------------------------------------------------------
    def walk_expanding_class_options(self, source=None):
        if source is None:
            source = self.option_definitions
        expanded_keys = []
        expansions_were_done = True
        while expansions_were_done:
            expansions_were_done = False
            # can't use iteritems in loop, we're changing the dict
            for key, val in source.items():
                if isinstance(val, Namespace):
                    self.walk_expanding_class_options(val)
                elif (key not in expanded_keys and
                        (inspect.isclass(val.value) or
                         inspect.ismodule(val.value))):
                    expanded_keys.append(key)
                    expansions_were_done = True
                    try:
                        for o_key, o_val in \
                                val.value.get_required_config().iteritems():
                            source.__setattr__(o_key, o_val)
                    except AttributeError:
                        pass  # there are no required_options for this class
                else:
                    pass  # don't need to touch other types of Options
            self.overlay_settings(ignore_mismatches=True)

    #--------------------------------------------------------------------------
    def setup_auto_help(self):
        help_option = Option(name='help', doc='print this', default=False)
        self.definition_source_list.append({'help': help_option})

    #--------------------------------------------------------------------------
    def setup_manager_controls(self):
        manager_options = Namespace()
        manager_options._write = Option(name='_write',
                                        doc='write config file to stdout '
                                            '(conf, ini, json)',
                                        default=None,
                                        )
        #manager_options._quit = Option(name='_quit',
                                       #doc='quit after doing admin commands',
                                       #default=False)
        manager_options.config_path = Option(name='config_path',
                                                 doc='path for config file '
                                                     '(not the filename)',
                                                 default='./')
        self.definition_source_list.append(manager_options)

    #--------------------------------------------------------------------------
    def overlay_settings(self, ignore_mismatches=True):
        for a_settings_source in self.values_source_list:
            #if isinstance(a_settings_source, collections.Mapping):
                #self.overlay_config_recurse(a_settings_source,
                                            #ignore_mismatches=True)
            #elif a_settings_source:
                #options = a_settings_source.get_values(self,
                                        #ignore_mismatches=ignore_mismatches)
                #self.overlay_config_recurse(options,
                                        #ignore_mismatches=ignore_mismatches)
            try:
                ignore_mismatches = ignore_mismatches or \
                                    a_settings_source.always_ignore_mismatches
            except AttributeError:
                # the settings source doesn't have the concept of always
                # ignoring mismatches, so the original value of
                # ignore_mismatches stands
                pass
            options = a_settings_source.get_values(self,
                                    ignore_mismatches=ignore_mismatches)
            self.overlay_config_recurse(options,
                                    ignore_mismatches=ignore_mismatches)

    #--------------------------------------------------------------------------
    def overlay_config_recurse(self, source, destination=None, prefix='',
                                ignore_mismatches=True):
        if destination is None:
            destination = self.option_definitions
        for key, val in source.items():
            try:
                sub_destination = destination
                for subkey in key.split('.'):
                    sub_destination = sub_destination[subkey]
            except KeyError:
                if ignore_mismatches:
                    continue
                if key == subkey:
                    raise exc.NotAnOptionError('%s is not an option' % key)
                raise exc.NotAnOptionError('%s subpart %s is not an option' %
                                       (key, subkey))
            except TypeError:
                pass
            if isinstance(sub_destination, Namespace):
                self.overlay_config_recurse(val, sub_destination,
                                            prefix=('%s.%s' % (prefix, key)))
            else:
                sub_destination.set_value(val)

    #--------------------------------------------------------------------------
    def walk_config_copy_values(self, source, destination):
        for key, val in source.items():
            value_type = type(val)
            if value_type == Option:
                destination[key] = val.value
            elif value_type == Namespace:
                destination[key] = d = DotDict()
                self.walk_config_copy_values(val, d)

    #--------------------------------------------------------------------------
    @staticmethod
    def option_sort(x_tuple):
        key, val = x_tuple
        if isinstance(val, Namespace):
            return 'zzzzzzzzzzz%s' % key
        else:
            return key

    #--------------------------------------------------------------------------
    @staticmethod
    def block_password(qkey, key, value, block_password=True):
        if block_password and 'password' in option.name.lower():
            value = '*********'
        return (qkey, key, value)

    #--------------------------------------------------------------------------
    def walk_config(self, source=None, prefix='', blocked_keys=[],
                    block_password=False):
        if source == None:
            source = self.option_definitions
        options_list = source.items()
        options_list.sort(key=ConfigurationManager.option_sort)
        for key, val in options_list:
            qualified_key = '%s%s' % (prefix, key)
            if key in blocked_keys:
                continue
            value_type = type(val)
            if value_type == Option:
                yield self.block_password(qualified_key, key, val,
                                          block_password)
            elif value_type == Namespace:
                yield qualified_key, key, val
                new_prefix = '%s%s.' % (prefix, key)
                for xqkey, xkey, xval in self.walk_config(val,
                                                          new_prefix,
                                                          blocked_keys,
                                                          block_password):
                    yield xqkey, xkey, xval

    #--------------------------------------------------------------------------
    def get_config(self):
        config = DotDict()
        self.walk_config_copy_values(self.option_definitions, config)
        return config

    #get definition from classes in defaults

    #--------------------------------------------------------------------------
    def get_option_by_name(self, name):
        source = self.option_definitions
        try:
            for sub_name in name.split('.'):
                candidate = source[sub_name]
                if isinstance(candidate, Option):
                    return candidate
                else:
                    source = candidate
        except KeyError:
            pass # we need to raise the exception below in either case
                 # of a key error or execution falling through the loop
        raise exc.NotAnOptionError('%s is not a known option name' % name)

    #--------------------------------------------------------------------------
    def get_option_names(self, source=None, names=None, prefix=''):
        if not source:
            source = self.option_definitions
        if names is None:
            names = []
        for key, val in source.items():
            if isinstance(val, Namespace):
                new_prefix = '%s%s.' % (prefix, key)
                self.get_option_names(val, names, new_prefix)
            else:
                names.append("%s%s" % (prefix, key))
        return names

    #--------------------------------------------------------------------------
    def get_options(self, source=None, options=None, prefix=''):
        if not source:
            source = self.option_definitions
        if options is None:
            options = []
        for key, val in source.items():
            if isinstance(val, Namespace):
                new_prefix = '%s%s.' % (prefix, key)
                self.get_options(val, options, new_prefix)
            else:
                options.append(("%s%s" % (prefix, key), val))
        return options

    #--------------------------------------------------------------------------
    def output_summary(self,
                       output_stream=sys.stdout,
                       output_template="--{name}\n\t\t{doc} (default: "
                                       "{default})",
                       bool_output_template="--{name}\n\t\t{doc}",
                       short_form_template="\t-{short_form}, ",
                       no_short_form_template="\t    ",
                       block_password=True):
        """outputs the list of acceptable commands.  This is useful as the
        output of the 'help' option or usage.

        Parameters:
          outputStream: where to send the output
          sortOption: 0 - sort by the single character option
                      1 - sort by the long option
          with_parameters_template: a string template for
          outputing options that have parameters from the long form onward
          outputTemplateForOptionsWithoutParameters: a string template for
          outputing options that have no parameters from the long form onward
          short_form_template: a string template for the first
          part of a listing where there is a single letter form of the command
          outputTemplatePrefixForNo: a string template for the first part of a
          listing where there is no single letter form of the command
        """
        if self.app_name:
            print >> output_stream, self.app_name, self.app_version
        if self.app_description:
            print >> output_stream, self.app_description
        names_list = self.get_option_names()
        names_list.sort()
        for x in names_list:
            if x in self.options_banned_from_help:
                continue
            option = self.get_option_by_name(x)
            if option.short_form:
                prefix = short_form_template
            else:
                prefix = no_short_form_template
            if isinstance(option.value, bool):
                template = bool_output_template
            else:
                template = output_template
            output_parameters = option.__dict__.copy()
            output_parameters['name'] = x
            if output_parameters['doc'] == None:
                output_parameters['doc'] = 'no documentation available'
            if block_password and 'password' in option.name.lower():
                output_parameters['default'] = '********'
                output_parameters['value'] = '********'
            template = '%s%s' % (prefix, template)
            # in the following line, we want the default to show the values
            # that have been read it from config files.  In other words,
            # we want to show the user what the values will be if they
            # make no further action
            try:
                value = output_parameters['value']
                type_of_value = type(value)
                converter_function = conv.to_string_converters[type_of_value]
                output_parameters['default'] = converter_function(value)
            except KeyError:
                output_parameters['default'] = output_parameters['value']
            print >> output_stream, template.format(**output_parameters)

    #--------------------------------------------------------------------------
    def write_config(self, config_file_type=None,
                     block_password=True,
                     opener=open):
        if not config_file_type:
            config_file_type = self.get_option_by_name('_write').value
        option_iterator = functools.partial(self.walk_config,
                                    blocked_keys=self.manager_controls_list)
        try:
            config_path = self.get_option_by_name('config_path').value
        except exc.NotAnOptionError:
            config_path = ''
        config_pathname = os.path.join(config_path,
                                       '.'.join((self.app_name,
                                                 config_file_type)))

        with opener(config_pathname, 'w') as config_fp:
            value_sources.write(config_file_type,
                                option_iterator,
                                config_fp)

    #--------------------------------------------------------------------------
    @staticmethod
    def option_value_str(an_option):
        import warnings
        warnings.warn(DeprecationWarning,
                      "This staticmethod is deprecated in favor of "
                      "option_value_str() in converters.py")
        return conv.option_value_str(an_option)


    #--------------------------------------------------------------------------
    def log_config(self, logger):
        app = self.get_option_by_name('_application')
        try:
            logger.info("app_name: %s", app.value.app_name)
            logger.info("app_version: %s", app.value.app_version)
        except AttributeError:
            pass
        logger.info("current configuration:")
        config = [(qkey, val.value) for qkey, key, val in
                                      self.walk_config(self.option_definitions)
                                    if qkey not in self.manager_controls_list
                                       and not isinstance(val, Namespace)]
        config.sort()
        for key, val in config:
            if 'password' in key.lower():
                logger.info('%s: *********', key)
            else:
                try:
                    logger.info('%s: %s', key,
                                conv.to_string_converters[type(key)](val))
                except KeyError:
                    logger.info('%s: %s', key, val)


def new_configuration(configurationModule=None,
                      applicationName=None,
                     ):
    definition_source = []
    if configurationModule:
        definition_source.append(configurationModule)
    config_manager = ConfigurationManager(definition_source,
                                          use_auto_help=True,
                                          application_name=applicationName)
    return config_manager.get_config()
