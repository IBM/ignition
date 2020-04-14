import unittest
import os
import yaml
from unittest.mock import patch
from ignition.locations.kubernetes import KubernetesDeploymentLocation

EXAMPLE_CONFIG = {
                    'apiVersion': 'v1',
                    'clusters': [
                        {'cluster': {'server': 'localhost'}, 'name': 'kubernetes'}
                    ],
                    'contexts': [
                        {'context': {'cluster': 'kubernetes', 'user': 'kubernetes-admin'}, 'name': 'kubernetes-admin@kubernetes' }
                    ],
                    'current-context': 'kubernetes-admin@kubernetes',
                    'kind': 'Config',
                    'preferences': {},
                    'users': [
                        {'name': 'kubernetes-admin', 'user': {}}
                    ]
                }

class TestKubernetesDeploymentLocation(unittest.TestCase):

    def test_from_dict(self):
        dl_dict = {
            'name': 'TestKube',
            'properties': {
                'client_config': EXAMPLE_CONFIG,
                'default_object_namespace': 'alternative'
            }
        }
        location = KubernetesDeploymentLocation.from_dict(dl_dict)
        self.assertEqual(location.name, 'TestKube')
        self.assertEqual(location.client_config, EXAMPLE_CONFIG)
        self.assertEqual(location.default_object_namespace, 'alternative')

    def test_from_dict_camel_case_config(self):
        dl_dict = {
            'name': 'TestKube',
            'properties': {
                'clientConfig': EXAMPLE_CONFIG,
                'defaultObjectNamespace': 'alternative'
            }
        }
        location = KubernetesDeploymentLocation.from_dict(dl_dict)
        self.assertEqual(location.name, 'TestKube')
        self.assertEqual(location.client_config, EXAMPLE_CONFIG)
        self.assertEqual(location.default_object_namespace, 'alternative')


    def test_write_config_file(self):
        location = KubernetesDeploymentLocation('TestKube', EXAMPLE_CONFIG)
        path = location.write_config_file()
        try:
            self.assertTrue(os.path.exists(path))
            with open(path, 'r') as f:
                config_from_file = yaml.safe_load(f.read())
            self.assertEqual(config_from_file, EXAMPLE_CONFIG)
        finally:
            os.remove(path)

    def test_write_config_file_provided_path(self):
        location = KubernetesDeploymentLocation('TestKube', EXAMPLE_CONFIG)
        provided_path = os.path.join(os.getcwd(), 'testconf.yaml')
        path = location.write_config_file(provided_path)
        try:
            self.assertEqual(path, provided_path)
        finally:
            os.remove(path)
