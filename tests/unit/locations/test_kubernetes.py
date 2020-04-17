import unittest
import os
import yaml
import copy
from unittest.mock import patch
from ignition.locations.exceptions import InvalidDeploymentLocationError
from ignition.locations.kubernetes import KubernetesDeploymentLocation, KubernetesSingleConfigValidator, KubernetesConfigValidationError

EXAMPLE_CONFIG = {
                    'apiVersion': 'v1',
                    'clusters': [
                        {'cluster': {'server': 'localhost'}, 'name': 'kubernetes'}
                    ],
                    'contexts': [
                        {'context': {'cluster': 'kubernetes', 'user': 'kubernetes-admin'}, 'name': 'kubernetes-admin@kubernetes'}
                    ],
                    'current-context': 'kubernetes-admin@kubernetes',
                    'kind': 'Config',
                    'preferences': {},
                    'users': [
                        {'name': 'kubernetes-admin', 'user': {}}
                    ]
                }

class TestKubernetesDeploymentLocation(unittest.TestCase):

    def test_init_validates_config(self):
        config = copy.deepcopy(EXAMPLE_CONFIG)
        config.pop('clusters')
        with self.assertRaises(KubernetesConfigValidationError) as context:    
            location = KubernetesDeploymentLocation('Test', config)
        self.assertEqual(str(context.exception), 'Config missing \'clusters\'')

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

    def test_from_dict_missing_name_raises_error(self):
        dl_dict = {
            'properties': {
                'clientConfig': EXAMPLE_CONFIG,
                'defaultObjectNamespace': 'alternative'
            }
        }
        with self.assertRaises(InvalidDeploymentLocationError) as context:
            KubernetesDeploymentLocation.from_dict(dl_dict)
        self.assertEqual(str(context.exception), 'Deployment location missing \'name\' value')
    
    def test_from_dict_missing_properties_raises_error(self):
        dl_dict = {
            'name': 'Test'
        }
        with self.assertRaises(InvalidDeploymentLocationError) as context:
            KubernetesDeploymentLocation.from_dict(dl_dict)
        self.assertEqual(str(context.exception), 'Deployment location missing \'properties\' value')
    
    def test_from_dict_missing_client_config_raises_error(self):
        dl_dict = {
            'name': 'Test',
            'properties': {}
        }
        with self.assertRaises(InvalidDeploymentLocationError) as context:
            KubernetesDeploymentLocation.from_dict(dl_dict)
        self.assertEqual(str(context.exception), 'Deployment location properties missing value for property \'clientConfig\' (or: \'client_config\')')

    def test_from_dict_invalid_client_config_yaml_raises_error(self):
        dl_dict = {
            'name': 'Test',
            'properties': {
                'client_config': 'not valid: YAML; : '
            }
        }
        with self.assertRaises(InvalidDeploymentLocationError) as context:
            KubernetesDeploymentLocation.from_dict(dl_dict)
        try:
            yaml.safe_load(dl_dict['properties']['client_config'])
        except yaml.YAMLError as e:
            expected_error = InvalidDeploymentLocationError(f'Deployment location property value for \'clientConfig/client_config\' is invalid, YAML parsing error: {str(e)}')
        self.assertEqual(str(context.exception), str(expected_error))

    def test_from_dict_invalid_client_config_type_raises_error(self):
        dl_dict = {
            'name': 'Test',
            'properties': {
                'client_config': 123
            }
        }
        with self.assertRaises(InvalidDeploymentLocationError) as context:
            KubernetesDeploymentLocation.from_dict(dl_dict)
        self.assertEqual(str(context.exception), 'Deployment location property value for \'clientConfig/client_config\' is invalid, expected a YAML string or dictionary but got <class \'int\'>')

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

    def test_clear_config_files(self):
        location = KubernetesDeploymentLocation('TestKube', EXAMPLE_CONFIG)
        pathA = None
        pathB = None
        try:
            pathA = location.write_config_file()
            pathB = location.write_config_file()
            self.assertTrue(os.path.exists(pathA))
            self.assertTrue(os.path.exists(pathB))
            location.clear_config_files()
            self.assertFalse(os.path.exists(pathA))
            self.assertFalse(os.path.exists(pathB))
        finally:
            if pathA != None and os.path.exists(pathA):
                os.remove(pathA)
            if pathB != None and os.path.exists(pathB):
                os.remove(pathB)

    def test_clear_config_files_keep_non_temp(self):
        location = KubernetesDeploymentLocation('TestKube', EXAMPLE_CONFIG)
        pathA = os.path.join(os.getcwd(), 'testconf.yaml')
        pathB = None
        try:
            location.write_config_file(pathA)
            pathB = location.write_config_file()
            self.assertTrue(os.path.exists(pathA))
            self.assertTrue(os.path.exists(pathB))
            location.clear_config_files(temp_only=True)
            self.assertTrue(os.path.exists(pathA))
            self.assertFalse(os.path.exists(pathB))
            self.assertEqual(location.config_files_created, [{'path': pathA, 'is_temp': False}])
        finally:
            if pathA != None and os.path.exists(pathA):
                os.remove(pathA)
            if pathB != None and os.path.exists(pathB):
                os.remove(pathB)

    def test_clear_config_files_removes_non_temp(self):
        location = KubernetesDeploymentLocation('TestKube', EXAMPLE_CONFIG)
        pathA = os.path.join(os.getcwd(), 'testconf.yaml')
        pathB = None
        try:
            location.write_config_file(pathA)
            pathB = location.write_config_file()
            self.assertTrue(os.path.exists(pathA))
            self.assertTrue(os.path.exists(pathB))
            location.clear_config_files()
            self.assertFalse(os.path.exists(pathA))
            self.assertFalse(os.path.exists(pathB))
            self.assertEqual(location.config_files_created, [])
        finally:
            if pathA != None and os.path.exists(pathA):
                os.remove(pathA)
            if pathB != None and os.path.exists(pathB):
                os.remove(pathB)

    def test_clear_config_files_handles_already_removed(self):
        location = KubernetesDeploymentLocation('TestKube', EXAMPLE_CONFIG)
        pathA = None
        pathB = None
        try:
            pathA = location.write_config_file()
            pathB = location.write_config_file()
            self.assertTrue(os.path.exists(pathA))
            self.assertTrue(os.path.exists(pathB))
            os.remove(pathA)
            self.assertFalse(os.path.exists(pathA))
            location.clear_config_files()
            self.assertFalse(os.path.exists(pathA))
            self.assertFalse(os.path.exists(pathB))
        finally:
            if pathA != None and os.path.exists(pathA):
                os.remove(pathA)
            if pathB != None and os.path.exists(pathB):
                os.remove(pathB)

class TestKubernetesSingleConfigValidator(unittest.TestCase):

    def setUp(self):
        self.config = copy.deepcopy(EXAMPLE_CONFIG)

    def __assert_validation_error(self, config, expected_err_msg):
        with self.assertRaises(KubernetesConfigValidationError) as context:
            KubernetesSingleConfigValidator(config).run_validation()
        self.assertEqual(str(context.exception), expected_err_msg)

    def test_validate_no_errors_for_valid_config(self):
        KubernetesSingleConfigValidator(self.config).run_validation()
        
    def test_validate_error_when_no_clusters(self):
        self.config.pop('clusters')
        self.__assert_validation_error(self.config, 'Config missing \'clusters\'')

    def test_validate_error_when_clusters_is_not_a_list(self):
        self.config['clusters'] = 'some clusters'
        self.__assert_validation_error(self.config, 'Config item \'clusters\' expected to be a list but was \'str\'')

    def test_validate_error_when_clusters_is_not_a_list(self):
        self.config['clusters'] = [{'cluster': {'server': 'localhost'}, 'name': 'kubernetesA'}, {'cluster': {'server': 'localhost'}, 'name': 'kubernetesB'}]
        self.__assert_validation_error(self.config, 'Config item \'clusters\' expected to be a list of one but there are 2 elements')

    def test_validate_error_when_cluster_missing_name(self):
        self.config['clusters'] = [{'cluster': {'server': 'localhost'}}]
        self.__assert_validation_error(self.config, 'Config item \'clusters[0]\' missing \'name\'')

    def test_validate_error_when_no_users(self):
        self.config.pop('users')
        self.__assert_validation_error(self.config, 'Config missing \'users\'')

    def test_validate_error_when_users_is_not_a_list(self):
        self.config['users'] = 'some users'
        self.__assert_validation_error(self.config, 'Config item \'users\' expected to be a list but was \'str\'')

    def test_validate_error_when_users_is_not_a_list(self):
        self.config['users'] = [{'name': 'kubernetes-admin', 'user': {}}, {'name': 'kubernetes-adminB', 'user': {}}]
        self.__assert_validation_error(self.config, 'Config item \'users\' expected to be a list of one but there are 2 elements')

    def test_validate_error_when_users_missing_name(self):
        self.config['users'] = [{'user': {}}]
        self.__assert_validation_error(self.config, 'Config item \'users[0]\' missing \'name\'')

    def test_validate_error_when_no_contexts(self):
        self.config.pop('contexts')
        self.__assert_validation_error(self.config, 'Config missing \'contexts\'')

    def test_validate_error_when_contexts_is_not_a_list(self):
        self.config['contexts'] = 'some contexts'
        self.__assert_validation_error(self.config, 'Config item \'contexts\' expected to be a list but was \'str\'')

    def test_validate_error_when_contexts_is_not_a_list(self):
        self.config['contexts'] = [{'context': {'cluster': 'kubernetes', 'user': 'kubernetes-admin'}, 'name': 'kubernetes-admin@kubernetesA'}, {'context': {'cluster': 'kubernetes', 'user': 'kubernetes-admin'}, 'name': 'kubernetes-admin@kubernetesB'}]
        self.__assert_validation_error(self.config, 'Config item \'contexts\' expected to be a list of one but there are 2 elements')

    def test_validate_error_when_contexts_missing_name(self):
        self.config['contexts'] = [{'context': {}}]
        self.__assert_validation_error(self.config, 'Config item \'contexts[0]\' missing \'name\'')

    def test_validate_error_when_context_not_for_cluster(self):
        self.config['contexts'][0]['context']['cluster'] = 'NotTheClusterYouAreLookingFor'
        self.__assert_validation_error(self.config, 'Config context \'kubernetes-admin@kubernetes\' should have a cluster value of \'kubernetes\' but was \'NotTheClusterYouAreLookingFor\'')

    def test_validate_error_when_context_not_for_user(self):
        self.config['contexts'][0]['context']['user'] = 'NotTheUserYouAreLookingFor'
        self.__assert_validation_error(self.config, 'Config context \'kubernetes-admin@kubernetes\' should have a user value of \'kubernetes-admin\' but was \'NotTheUserYouAreLookingFor\'')

    def test_validate_error_when_context_not_current(self):
        self.config['current-context'] = 'NotTheContextYouAreLookingFor'
        self.__assert_validation_error(self.config, 'Config current-context should be \'kubernetes-admin@kubernetes\' but was \'NotTheContextYouAreLookingFor\'')
