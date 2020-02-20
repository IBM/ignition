import logging
import uuid
import traceback
import logging
import socket
import sys
import os
import connexion
from ignition.api.exceptions import ApiException
from ignition.service.framework import Service, Capability, interface
from ignition.service.config import ConfigurationPropertiesGroup
from datetime import datetime
from frozendict import frozendict

try:
    import json
except ImportError:
    import simplejson as json
import threading

LM_HTTP_HEADER_PREFIX = "X-Tracectx-"
LOGGING_CONTEXT_KEY_PREFIX = "traceCtx."
LM_HTTP_HEADER_TXNID = "TransactionId".lower()
LM_HTTP_HEADER_PROCESS_ID = "ProcessId".lower()

class LogstashFormatter(logging.Formatter):

    def __init__(self, message_type='Logstash', tags=None, fqdn=False):
        self.message_type = message_type
        self.tags = tags if tags is not None else []

        if fqdn:
            self.host = socket.getfqdn()
        else:
            self.host = socket.gethostname()

    def get_debug_fields(self, record):
        fields = {
            'stack_trace': self.format_exception(record.exc_info),
            'lineno': record.lineno,
            'process': record.process,
        }

        # funcName was added in 2.5
        if not getattr(record, 'funcName', None):
            fields['funcName'] = record.funcName

        # processName was added in 2.6
        if not getattr(record, 'processName', None):
            fields['processName'] = record.processName

        return fields

    @classmethod
    def format_source(cls, message_type, host, path):
        return "%s://%s/%s" % (message_type, host, path)

    @classmethod
    def format_timestamp(cls, time):
        tstamp = datetime.utcfromtimestamp(time)
        return tstamp.strftime("%Y-%m-%dT%H:%M:%S") + ".%03d" % (tstamp.microsecond / 1000) + "Z"

    @classmethod
    def format_exception(cls, exc_info):
        return ''.join(traceback.format_exception(*exc_info)) if exc_info else ''

    @classmethod
    def serialize(cls, message):
        return json.dumps(message)

    def format(self, record):
        message = {
            '@timestamp': self.format_timestamp(record.created),
            '@version': '1',
            'message': record.getMessage(),
            'host': self.host,
            'path': record.pathname,
            'tags': self.tags,
            'type': self.message_type,
            'thread_name': record.threadName,
            'level': record.levelname,
            'logger_name': record.name
        }

        # add LM transactional context to log message
        message.update(logging_context.get_all())

        # If exception, add debug info
        if record.exc_info:
            message.update(self.get_debug_fields(record))

        return self.serialize(message)

class LogManager(Capability):
    
    @interface
    def get_logger_details(self, logger_name):
        pass

    @interface
    def update_logger_details(self, logger_name, update_request):
        pass

class InvalidLoggerUpdateRequestError(ApiException):
    status_code = 400

class LoggerUpdateRequest:

    def __init__(self, level=None):
        self.level = level

class LogManagerService(Service, LogManager):
    """
    Out-of-the-box service for managing loggers 
    """

    def __init__(self):
        pass

    def get_logger_details(self, logger_name):
        retrieved_logger = logging.getLogger(logger_name)
        level = logging.getLevelName(retrieved_logger.getEffectiveLevel())
        return LoggerDetails(level)

    def update_logger_details(self, logger_name, update_request):
        retrieved_logger = logging.getLogger(logger_name)
        if update_request.level is not None:
            try:
                retrieved_logger.setLevel(update_request.level)
            except ValueError as e:
                if str(e) != None and str(e).startswith('Unknown level'):
                    raise InvalidLoggerUpdateRequestError(str(e)) from e
                else:
                    raise

class LoggerDetails:

    def __init__(self, level):
        self.level = level

    def dict_copy(self):
        details = {
            'level': self.level
        }
        return details


class LogInitialiser:

    LOGGER_FIELDS = ['level']

    def __init__(self):
        self.env_vars = LogEnvironmentVariables()

    def initialise(self):
        if self.env_vars.boot_enabled is True:
            logging.basicConfig(level=logging.INFO)
            self.__configure_formatter_from_env()
            self.__configure_root_level_from_env()
            self.__configure_ignition_level_from_env()

    def __configure_formatter_from_env(self):
        root_logger = logging.getLogger()
        if self.env_vars.format is not None and self.env_vars.format.lower() == 'logstash':
            log_formatter = LogstashFormatter('logstash')
        else:
            log_formatter = logging.Formatter()
        for handler in root_logger.handlers:
            handler.setFormatter(log_formatter)

    def __configure_root_level_from_env(self):
        root_logger = logging.getLogger()
        if self.env_vars.root_level is not None:
            root_logger.setLevel(self.env_vars.root_level)

    def __configure_ignition_level_from_env(self):
        if self.env_vars.ignition_level is not None:
            ignition_logger = logging.getLogger('ignition')
            ignition_level = self.env_vars.ignition_level
            ignition_logger.setLevel(ignition_level)
        if self.env_vars.ignition_boot_level is not None:
            ignition_boot_logger = logging.getLogger('ignition.boot')
            ignition_boot_level = self.env_vars.ignition_boot_level
            ignition_boot_logger.setLevel(ignition_boot_level)

    def update_from_props(self, props):
        if props.boot_enabled is True:
            self.__configure_loggers(props)

    def __configure_loggers(self, props):
        if len(props.loggers) > 0:
            for logger_name, logger_config in props.loggers.items():
                logger_details = self.__read_logger(logger_name, logger_config)
                if logger_name == '$':
                    the_logger = logging.getLogger()
                else:
                    the_logger = logging.getLogger(logger_name)
                if logger_details.level is not None:
                    the_logger.setLevel(logger_details.level)

    def __read_logger(self, logger_name, raw_logger_config):
        level = None
        if raw_logger_config is not None:
            level = raw_logger_config.get('level', None)
            invalid_keys = []
            for k in raw_logger_config.keys():
                if k not in LOGGER_FIELDS:
                    invalid_keys.append(k)
            if len(invalid_keys) > 1:
                raise ValueError('Logger configuration \'{0}\' has invalid fields: {1}. Allowed fields: {2}'.format(logger_name, invalid_keys, self.LOGGER_FIELDS))
        return LoggerDetails(level)

class LogEnvironmentVariables:

    LOG_BOOTSTRAPPING_ENABLED = 'LOG_BOOT_ENABLED'
    LOG_TYPE = 'LOG_TYPE'
    LOG_FORMAT = 'LOG_FORMAT'
    ROOT_LOG_LEVEL = 'LOG_LEVEL'
    IGNITION_LOG_LEVEL = 'IGNITION_LOG_LEVEL'
    IGNITION_BOOT_LOG_LEVEL = 'IGNITION_BOOT_LOG_LEVEL'

    def __init__(self):
        self.boot_enabled = self._read_env_var(LogEnvironmentVariables.LOG_BOOTSTRAPPING_ENABLED)
        if self.boot_enabled is not None:
            self.boot_enabled = self.boot_enabled.upper() == 'TRUE'
        self.format = self._read_env_var(LogEnvironmentVariables.LOG_FORMAT)
        if self.format is None:
            self.format = self._read_env_var(LogEnvironmentVariables.LOG_TYPE)
        self.root_level = self._read_env_var(LogEnvironmentVariables.ROOT_LOG_LEVEL)
        self.ignition_level = self._read_env_var(LogEnvironmentVariables.IGNITION_LOG_LEVEL)
        self.ignition_boot_level = self._read_env_var(LogEnvironmentVariables.IGNITION_BOOT_LOG_LEVEL)

    def _read_env_var(self, env_var_name):
        value = os.getenv(env_var_name)
        if value is None or len(value.strip()) == 0:
            return None
        else:
            return value.strip()

class LogProperties(ConfigurationPropertiesGroup, Service, Capability):

    def __init__(self):
        super().__init__('logging')
        env_conf = LogEnvironmentVariables()
        self.boot_enabled = env_conf.boot_enabled
        self.loggers = {}

class LoggingContext(threading.local):

    def __init__(self):
        self.data = {}

    def set_from_headers(self):
        # extract tracing headers such as transactionid, convert their names to logging format and set them in the thread context
        self.data.update(list(map(lambda header: (LOGGING_CONTEXT_KEY_PREFIX + header[0][len(LM_HTTP_HEADER_PREFIX):].lower(), header[1]),
            filter(lambda header: header[0].lower().startswith(LM_HTTP_HEADER_PREFIX.lower()), connexion.request.headers.items()))))

    def set_from_dict(self, d):
        self.data.update(d)

    def get(self, name, default=''):
        return self.data.get(name, default)

    def get_all(self):
        # protect the dictionary from changes - use the setters to do this
        return frozendict(self.data)
    
    def clear(self):
        self.data = {}

logging_context = LoggingContext()