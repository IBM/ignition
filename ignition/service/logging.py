import logging
import uuid
import traceback
import logging
import socket
import sys
import os
import re
import connexion
from datetime import datetime
from frozendict import frozendict
try:
    import json
except ImportError:
    import simplejson as json
import threading

PRIVATE_KEY_PREFIX = '-----BEGIN RSA PRIVATE KEY-----'
PRIVATE_KEY_SUFFIX = '-----END RSA PRIVATE KEY-----'
OBFUSCATED_PRIVATE_KEY = '***obfuscated private key***'

BEGIN_CERT_PREFIX = '-----BEGIN CERTIFICATE-----'
END_CERT_SUFFIX = '-----END CERTIFICATE-----'
OBFUSCATED_CERTIFICATE = '***obfuscated certificate***'

TOKEN_PREFIX = 'token'
TOKEN_SUFFIX = "'"

PWD_PREFIX = "Password"
PWD_SUFFIX = ","
PWD_SUFFIX_WITH_NEXTLINE = '\\\\n '

USERNAME_PREFIX = 'username'

LM_HTTP_HEADER_PREFIX = "x-tracectx-"
LOGGING_CONTEXT_KEY_PREFIX = "tracectx."
LM_HTTP_HEADER_TXNID = "TransactionId".lower()
LM_HTTP_HEADER_PROCESS_ID = "ProcessId".lower()

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

class SensitiveDataFormatter(logging.Formatter):

    def __init__(self, wrapped_formatter):
        self.wrapped_formatter = wrapped_formatter

    def format(self, record):
        result = self.wrapped_formatter.format(record)
        result = self._obfuscate_sensitive_data(result)
        return result

    def _mask_sensitive_data(self, suffix, prefix, message, rep=None):
        regex = re.compile('{0}(.*?){1}'.format(prefix, suffix), flags=re.DOTALL | re.IGNORECASE)
        abc = re.findall(regex, message)
        if len(abc) > 0:
            if rep is None:
                rep = '*' * len(abc[0])
                if abc[0][0] != "'" and abc[0][len(abc[0])-1] == "'":
                    rep = ":" + rep + "'"
                elif abc[0].find("'") != -1:
                    rep = "':'" + rep + "'"
                elif abc[0].find('"') != -1:
                    rep = '":"' + rep + '"'
                else:
                    rep = ":" + rep
            masked_value = prefix + rep + suffix
            message = re.sub(regex, masked_value, message)
        return message

    def _obfuscate_sensitive_data(self, record_message):
        if record_message is None:
            return record_message
        
        pwd_message = self._mask_sensitive_data(PWD_SUFFIX_WITH_NEXTLINE, PWD_PREFIX, record_message)
        if pwd_message == record_message:
            pwd_message = self._mask_sensitive_data(PWD_SUFFIX, PWD_PREFIX, record_message)

        username_message = self._mask_sensitive_data(PWD_SUFFIX_WITH_NEXTLINE, USERNAME_PREFIX, pwd_message)
        if username_message == pwd_message:
            username_message = self._mask_sensitive_data(PWD_SUFFIX, USERNAME_PREFIX, pwd_message)

        replacements=[(PRIVATE_KEY_PREFIX, PRIVATE_KEY_SUFFIX, OBFUSCATED_PRIVATE_KEY), (TOKEN_PREFIX, TOKEN_SUFFIX, None),
                      (BEGIN_CERT_PREFIX, END_CERT_SUFFIX, OBFUSCATED_CERTIFICATE)]
        for pre,suf,rep in replacements:
            username_message = self._mask_sensitive_data(suf, pre, username_message, rep)

        return username_message

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
            'HOSTNAME': self.host,
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



# configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
log_level = os.environ.get('LOG_LEVEL')
if log_level is None:
    log_level = 'INFO'

log_type = os.environ.get('LOG_TYPE')
if log_type is None:
    # "flat" is the default, nothing specific to configure for this
    log_type = 'flat'

if log_type.lower() == 'logstash':
    log_formatter = LogstashFormatter('logstash')
else:
    log_formatter = logging.Formatter()

logging.getLogger().setLevel(log_level)
[handler.setFormatter(SensitiveDataFormatter(log_formatter)) for handler in logging.getLogger().handlers]

logging.getLogger('kafka').setLevel('INFO')

logging_context = LoggingContext()
