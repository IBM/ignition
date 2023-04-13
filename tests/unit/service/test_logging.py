import unittest
import logging
import json
from ignition.service.logging import SensitiveDataFormatter, LogstashFormatter

KEY_PRIVATE_KEY = '''
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

KEY_CERTIFICATE = '''
-----BEGIN CERTIFICATE-----
MIIBOQIBAAJBAIOLepgdqXrM07O4dV/nJ5gSA12jcjBeBXK5mZO7Gc778HuvhJi+
RvqhSi82EuN9sHPx1iQqaCuXuS1vpuqvYiUCAwEAAQJATRDbCuFd2EbFxGXNxhjL
loj/Fc3a6UE8GeFoeydDUIJjWifbCAQsptSPIT5vhcudZgWEMDSXrIn79nXvyPy5
BQIhAPU+XwrLGy0Hd4Roug+9IRMrlu0gtSvTJRWQ/b7m0fbfAiEAiVB7bUMynZf4
SwVJ8NAF4AikBmYxOJPUxnPjEp8D23sCIA3ZcNqWL7myQ0CZ/W/oGVcQzhwkDbck
3GJEZuAB/vd3AiASmnvOZs9BuKgkCdhlrtlM6/7E+y1p++VU6bh2+mI8ZwIgf4Qh
u+zYCJfIjtJJpH1lHZW+A60iThKtezaCk7FiAC4= 
-----END CERTIFICATE-----
'''
KEY_PASSWORD = '"os_auth_password":"abcdefgh", "os_auth_project_domain_name":"default"'

KEY_PASSWORD_NEXTLINE = 'ssh_pwauth: True\\\\n        password: ubuntu\\\\n        chpasswd:\\\\n '

KEY_USERNAME = '"os_authusername":"abcdefgh", "os_auth_project_domain_name":"default"'

KEY_USERNAME_NEXTLINE = 'ssh_pwauth: True\\\\n        username: ubuntu\\\\n        chpasswd:\\\\n '

KEY_TOKEN = "nuser:\\\\ntoken:sha256~cyJqmk4dzVshjBd_OFcyJwydrfyzrwu1CbTQEKyfvkA\\\\n'"

KEY_USERNAME_PASSWORD = '"password":"abcdefgh", "username":"abcdefgh", "name":"name"'

class TestSensitiveDataFormatter(unittest.TestCase):

    def test_obfuscate_sensitive_data(self):
        formatter = SensitiveDataFormatter(logging.Formatter())
        record = logging.makeLogRecord({
            'msg': 'some logging of a key {0} to be obfuscated'.format(KEY_PRIVATE_KEY)
        })
        result = formatter.format(record)
        self.assertEqual(result, 'some logging of a key \n-----BEGIN RSA PRIVATE KEY-----***obfuscated private key***-----END RSA PRIVATE KEY-----\n to be obfuscated')

    def test_obfuscate_sensitive_data(self):
        formatter = SensitiveDataFormatter(logging.Formatter())
        record = logging.makeLogRecord({
            'msg': 'some logging of a key {0} to be obfuscated, and then the key is mentioned again {0} to check we match both'.format(KEY_PRIVATE_KEY)
        })
        result = formatter.format(record)
        self.assertEqual(result, 'some logging of a key \n-----BEGIN RSA PRIVATE KEY-----***obfuscated private key***-----END RSA PRIVATE KEY-----\n to be obfuscated, and then the key is mentioned again \n-----BEGIN RSA PRIVATE KEY-----***obfuscated private key***-----END RSA PRIVATE KEY-----\n to check we match both')

    def test_obfuscate_sensitive_data_logstash(self):
        formatter = SensitiveDataFormatter(LogstashFormatter())
        record = logging.makeLogRecord({
            'msg': 'some logging of a key {0} to be obfuscated'.format(KEY_PRIVATE_KEY)
        })
        result = formatter.format(record)
        result_dict = json.loads(result)
        self.assertEqual(result_dict.get('message', None), 'some logging of a key \n-----BEGIN RSA PRIVATE KEY-----***obfuscated private key***-----END RSA PRIVATE KEY-----\n to be obfuscated')

    def test_obfuscate_sensitive_data_certificate(self):
        '''
        This unit test is for testing the certificate masking in logs.
        '''
        formatter = SensitiveDataFormatter(logging.Formatter())
        record = logging.makeLogRecord({
            'msg': 'some logging of a key {0} to be obfuscated'.format(KEY_CERTIFICATE)
        })
        result = formatter.format(record)
        self.assertEqual(result, 'some logging of a key \n-----BEGIN CERTIFICATE-----***obfuscated certificate***-----END CERTIFICATE-----\n to be obfuscated')

    def test_obfuscate_sensitive_data_multiple_certificate(self):
        '''
        This unit test is for testing multiple certificates masking in logs.
        '''
        formatter = SensitiveDataFormatter(logging.Formatter())
        record = logging.makeLogRecord({
            'msg': 'some logging of a key {0} to be obfuscated, and then the key is mentioned again {0} to check we match both'.format(KEY_CERTIFICATE)
        })
        result = formatter.format(record)
        self.assertEqual(result, 'some logging of a key \n-----BEGIN CERTIFICATE-----***obfuscated certificate***-----END CERTIFICATE-----\n to be obfuscated, and then the key is mentioned again \n-----BEGIN CERTIFICATE-----***obfuscated certificate***-----END CERTIFICATE-----\n to check we match both')

    def test_obfuscate_sensitive_data_password(self):
        '''
        This unit test is for testing the password masking in logs with suffix as comma in reqex.
        '''
        formatter = SensitiveDataFormatter(logging.Formatter())
        record = logging.makeLogRecord({
            'msg': 'some logging of a key {0} to be obfuscated'.format(KEY_PASSWORD)
        })
        result = formatter.format(record)
        self.assertEqual(result, 'some logging of a key "os_auth_password":"************", "os_auth_project_domain_name":"default" to be obfuscated')

    def test_obfuscate_sensitive_data_password_nextline(self):
        '''
        This unit test is for testing the password masking in logs with suffix as nextline in reqex.
        '''
        formatter = SensitiveDataFormatter(logging.Formatter())
        record = logging.makeLogRecord({
            'msg': 'some logging of a key {0} to be obfuscated'.format(KEY_PASSWORD_NEXTLINE)
        })
        result = formatter.format(record)
        self.assertEqual(result, 'some logging of a key ssh_pwauth: True\\\\n        password:*********\\n        chpasswd:\\\\n  to be obfuscated')

    def test_obfuscate_sensitive_data_username(self):
        '''
        This unit test is for testing the username masking in logs with suffix as comma in reqex.
        '''
        formatter = SensitiveDataFormatter(logging.Formatter())
        record = logging.makeLogRecord({
            'msg': 'some logging of a key {0} to be obfuscated'.format(KEY_USERNAME)
        })
        result = formatter.format(record)
        self.assertEqual(result, 'some logging of a key "os_authusername":"************", "os_auth_project_domain_name":"default" to be obfuscated')

    def test_obfuscate_sensitive_data_username_nextline(self):
        '''
        This unit test is for testing the username masking in logs with suffix as nextline in reqex.
        '''
        formatter = SensitiveDataFormatter(logging.Formatter())
        record = logging.makeLogRecord({
            'msg': 'some logging of a key {0} to be obfuscated'.format(KEY_USERNAME_NEXTLINE)
        })
        result = formatter.format(record)
        self.assertEqual(result, 'some logging of a key ssh_pwauth: True\\\\n        username:*********\\n        chpasswd:\\\\n  to be obfuscated')

    def test_obfuscate_sensitive_data_token(self):
        '''
        This unit test is for testing the token masking in logs with suffix as nextline in reqex.
        '''
        formatter = SensitiveDataFormatter(logging.Formatter())
        record = logging.makeLogRecord({
            'msg': 'some logging of a key {0} to be obfuscated'.format(KEY_TOKEN)
        })
        result = formatter.format(record)
        self.assertEqual(result, "some logging of a key nuser:\\\\ntoken:****************************************************\\n' to be obfuscated")

    def test_obfuscate_sensitive_data_username_password(self):
        '''
        This unit test is for testing the username and password masking in logs.
        '''
        formatter = SensitiveDataFormatter(logging.Formatter())
        record = logging.makeLogRecord({
            'msg': 'some logging of a key {0} to be obfuscated'.format(KEY_USERNAME_PASSWORD)
        })
        result = formatter.format(record)
        self.assertEqual(result, 'some logging of a key "password":"************", "username":"************", "name":"name" to be obfuscated')

    def test_obfuscate_sensitive_data_multiple_password(self):
        '''
        This unit test is for testing the multiple password masking in logs.
        '''
        formatter = SensitiveDataFormatter(logging.Formatter())
        record = logging.makeLogRecord({
            'msg': 'some logging of a key {0} to be obfuscated, and then the key is mentioned again {0} to check we match both'.format(KEY_PASSWORD)
        })
        result = formatter.format(record)
        self.assertEqual(result, 'some logging of a key "os_auth_password":"************", "os_auth_project_domain_name":"default" to be obfuscated, and then the key is mentioned again "os_auth_password":"************", "os_auth_project_domain_name":"default" to check we match both')

    def test_obfuscate_sensitive_data_multiple_username(self):
        '''
        This unit test is for testing the multiple username masking in logs.
        '''
        formatter = SensitiveDataFormatter(logging.Formatter())
        record = logging.makeLogRecord({
            'msg': 'some logging of a key {0} to be obfuscated, and then the key is mentioned again {0} to check we match both'.format(KEY_USERNAME)
        })
        result = formatter.format(record)
        self.assertEqual(result, 'some logging of a key "os_authusername":"************", "os_auth_project_domain_name":"default" to be obfuscated, and then the key is mentioned again "os_authusername":"************", "os_auth_project_domain_name":"default" to check we match both')

    def test_obfuscate_sensitive_data_multiple_token(self):
        '''
        This unit test is for testing the multiple token masking in logs.
        '''
        formatter = SensitiveDataFormatter(logging.Formatter())
        record = logging.makeLogRecord({
            'msg': 'some logging of a key {0} to be obfuscated, and then the key is mentioned again {0} to check we match both'.format(KEY_TOKEN)
        })
        result = formatter.format(record)
        self.assertEqual(result, "some logging of a key nuser:\\\\ntoken:****************************************************\\n' to be obfuscated, and then the key is mentioned again nuser:\\\\ntoken:****************************************************\\n' to check we match both")