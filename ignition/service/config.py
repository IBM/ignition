import yaml
import logging
import pathlib
import os
from abc import ABC, abstractmethod
from ignition.service.framework import Service, Capability, interface

logger = logging.getLogger(__name__)


class ConfigurationProperties:

    def __init__(self):
        pass

    def read_from_dict(self, raw_dict):
        for k, v in raw_dict.items():
            if hasattr(self, k):
                current_value = getattr(self, k)
                new_value = v
                if isinstance(current_value, ConfigurationProperties) and type(new_value) is dict:
                    logger.debug('{0} reading nested configuration properties from: {1}'.format(self.__class__.__name__, k))
                    current_value.read_from_dict(new_value)
                else:
                    logger.debug('{0} reading configuration option: {1}'.format(self.__class__.__name__, k))
                    setattr(self, k, new_value)
            else:
                logger.debug('{0} ignoring unknown configuration option: {1}'.format(self.__class__.__name__, k))


class ConfigurationPropertiesGroup(ConfigurationProperties):

    def __init__(self, key_namespace):
        self.key_namespace = key_namespace


class ConfigParserService:

    def parse(self, property_sources, property_groups):
        return ConfigParserWorker(property_sources, property_groups).parse()


class ConfigParserWorker:

    def __init__(self, property_sources, property_groups):
        self.property_sources = property_sources
        self.property_groups = property_groups

    def __organise_property_groups_by_key_namespace(self, property_groups):
        organised_config = {}
        for property_group in property_groups:
            if isinstance(property_group, ConfigurationPropertiesGroup):
                key_namespace = property_group.key_namespace
                if key_namespace in organised_config:
                    organised_config[key_namespace].append(property_group)
                else:
                    organised_config[key_namespace] = [property_group]
            else:
                raise ValueError('Property group instance provided must be a subclass of ConfigurationPropertiesGroup: {0}'.format(property_group))
        return organised_config

    def __process_config_value(self, key_namespace, raw_config, organised_property_groups):
        if key_namespace in organised_property_groups:
            for property_group in organised_property_groups[key_namespace]:
                logger.debug('Reading properties at key namespace \'{0}\' into property group \'{1}\''.format(key_namespace, property_group.__class__.__name__))
                property_group.read_from_dict(raw_config)
        if type(raw_config) is dict:
            for k, v in raw_config.items():
                key_namespace += '.{0}'.format(k)
                self.__process_config_value(key_namespace, v, organised_property_groups)

    def parse(self):
        organised_property_groups = self.__organise_property_groups_by_key_namespace(self.property_groups)
        for source in self.property_sources:
            raw_config_dict = source.get()
            if raw_config_dict != None:
                if type(raw_config_dict) != dict:
                    raise ValueError('Source \'{0}\' must return a dict but instead returned {1}'.format(source, type(raw_config_dict)))
                for k, v in raw_config_dict.items():
                    key_namespace = k
                    self.__process_config_value(key_namespace, v, organised_property_groups)


class Source:

    @abstractmethod
    def get(self):
        pass


class YmlFileSource(Source):

    def __init__(self, file_path, **kwargs):
        if file_path is None or len(file_path) == 0:
            raise ValueError('file_path must be set')
        self.file_path = file_path
        allowed_kwargs = ['required']
        for k, v in kwargs.items():
            if k not in allowed_kwargs:
                raise ValueError('keyword argument not supported: {0}'.format(k))
        self.required = kwargs.get('required', False)

    def get(self):
        yml_tpl = None
        yml_path = self.file_path
        if not os.path.exists(yml_path):
            if self.required:
                raise FileNotFoundError('File not found: {0}'.format(yml_path))
        else:
            with open(yml_path, 'r') as stream:
                try:
                    yml_tpl = yaml.safe_load(stream)
                except yaml.YAMLError as exc:
                    raise ValueError('File does not include valid YAML: {0}') from exc
            logger.debug('Loaded yml content from file {0}:\n{1}'.format(yml_path, yml_tpl))
        return yml_tpl


class EnvironmentSourceError(Exception):
    pass


class EnvironmentVariableYmlFileSource(Source):

    def __init__(self, environment_variable, **kwargs):
        if not environment_variable:
            raise ValueError('environment_variable must be set')
        self.environment_variable = environment_variable
        allowed_kwargs = ['required']
        for k, v in kwargs.items():
            if k not in allowed_kwargs:
                raise ValueError('keyword argument not supported: {0}'.format(k))
        self.required = kwargs.get('required', False)

    def get(self):
        logger.info('Checking for file path on environment variable: {0}'.format(self.environment_variable))
        file_path = os.environ.get(self.environment_variable)
        if file_path is None:
            if self.required:
                raise EnvironmentSourceError('Required environment variable \'{0}\' not set'.format(self.environment_variable))
            logger.info('Environment variable \'{0}\' not set'.format(self.environment_variable))
            return None
        else:
            logger.info('Environment variable \'{0}\' set to file path {1}'.format(self.environment_variable, file_path))
            return YmlFileSource(file_path, required=self.required).get()


class DictSource(Source):

    def __init__(self, data):
        self.data = data

    def get(self):
        return self.data
