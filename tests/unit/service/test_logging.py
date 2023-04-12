import unittest
import logging
import json
from ignition.service.logging import SensitiveDataFormatter, LogstashFormatter

key = '''
-----BEGIN RSA PRIVATE KEY-----
MIIBOQIBAAJBAIOLepgdqXrM07O4dV/nJ5gSA12jcjBeBXK5mZO7Gc778HuvhJi+
RvqhSi82EuN9sHPx1iQqaCuXuS1vpuqvYiUCAwEAAQJATRDbCuFd2EbFxGXNxhjL
loj/Fc3a6UE8GeFoeydDUIJjWifbCAQsptSPIT5vhcudZgWEMDSXrIn79nXvyPy5
BQIhAPU+XwrLGy0Hd4Roug+9IRMrlu0gtSvTJRWQ/b7m0fbfAiEAiVB7bUMynZf4
SwVJ8NAF4AikBmYxOJPUxnPjEp8D23sCIA3ZcNqWL7myQ0CZ/W/oGVcQzhwkDbck
3GJEZuAB/vd3AiASmnvOZs9BuKgkCdhlrtlM6/7E+y1p++VU6bh2+mI8ZwIgf4Qh
u+zYCJfIjtJJpH1lHZW+A60iThKtezaCk7FiAC4= 
-----END RSA PRIVATE KEY-----
'''

class TestSensitiveDataFormatter(unittest.TestCase):

    def test_obfuscate_sensitive_data(self):
        formatter = SensitiveDataFormatter(logging.Formatter())
        record = logging.makeLogRecord({
            'msg': 'some logging of a key {0} to be obfuscated'.format(key)
        })
        result = formatter.format(record)
        self.assertEqual(result, 'some logging of a key \n-----BEGIN RSA PRIVATE KEY-----***obfuscated private key***-----END RSA PRIVATE KEY-----\n to be obfuscated')

    def test_obfuscate_sensitive_data(self):
        formatter = SensitiveDataFormatter(logging.Formatter())
        record = logging.makeLogRecord({
            'msg': 'some logging of a key {0} to be obfuscated, and then the key is mentioned again {0} to check we match both'.format(key)
        })
        result = formatter.format(record)
        self.assertEqual(result, 'some logging of a key \n-----BEGIN RSA PRIVATE KEY-----***obfuscated private key***-----END RSA PRIVATE KEY-----\n to be obfuscated, and then the key is mentioned again \n-----BEGIN RSA PRIVATE KEY-----***obfuscated private key***-----END RSA PRIVATE KEY-----\n to check we match both')

    def test_obfuscate_sensitive_data_logstash(self):
        formatter = SensitiveDataFormatter(LogstashFormatter())
        record = logging.makeLogRecord({
            'msg': 'some logging of a key {0} to be obfuscated'.format(key)
        })
        result = formatter.format(record)
        result_dict = json.loads(result)
        self.assertEqual(result_dict.get('message', None), 'some logging of a key \n-----BEGIN RSA PRIVATE KEY-----***obfuscated private key***-----END RSA PRIVATE KEY-----\n to be obfuscated')