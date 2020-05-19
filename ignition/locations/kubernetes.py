from .utils import get_property_or_default
from .exceptions import InvalidDeploymentLocationError
import tempfile
import os
import yaml

DEFAULT_NAMESPACE = 'default'

class KubernetesDeploymentLocation:
    """
    Kubernetes based deployment location

    Attributes:
      name (str): name of the location
      client_config (dict): dictionary of the Kubernetes config for client connections to this location
      default_object_namespace (str): Optional, the default namespace to use when managing objects in this location. Default: 'default' 
    """

    NAME = 'name'
    PROPERTIES = 'properties'
    CONFIG_PROP = 'clientConfig'
    CONFIG_ALT2_PROP = 'client_config'
    DEFAULT_OBJECT_NAMESPACE_PROP = 'defaultObjectNamespace'
    DEFAULT_OBJECT_NAMESPACE_ALT2_PROP = 'default_object_namespace'

    @staticmethod
    def from_dict(dl_data):
        """
        Creates a Kubernetes deployment location from dictionary format

        Args:
            dl_data (dict): the deployment location data. Should have a 'name' field and 'properties' for the location configuration

        Returns:
            a KubernetesDeploymentLocation instance
        """
        name = dl_data.get(KubernetesDeploymentLocation.NAME)
        if name is None:
            raise InvalidDeploymentLocationError(f'Deployment location missing \'{KubernetesDeploymentLocation.NAME}\' value')
        properties = dl_data.get(KubernetesDeploymentLocation.PROPERTIES)
        if properties is None:
            raise InvalidDeploymentLocationError(f'Deployment location missing \'{KubernetesDeploymentLocation.PROPERTIES}\' value')
        client_config = get_property_or_default(properties, KubernetesDeploymentLocation.CONFIG_PROP, KubernetesDeploymentLocation.CONFIG_ALT2_PROP, error_if_not_found=True)
        if type(client_config) is str:
            try:
                client_config = yaml.safe_load(client_config)
            except yaml.YAMLError as e:
                raise InvalidDeploymentLocationError(f'Deployment location property value for \'{KubernetesDeploymentLocation.CONFIG_PROP}/{KubernetesDeploymentLocation.CONFIG_ALT2_PROP}\' is invalid, YAML parsing error: {str(e)}') from e
        elif type(client_config) != dict:
            raise InvalidDeploymentLocationError(f'Deployment location property value for \'{KubernetesDeploymentLocation.CONFIG_PROP}/{KubernetesDeploymentLocation.CONFIG_ALT2_PROP}\' is invalid, expected a YAML string or dictionary but got {type(client_config)}')
        kwargs = {}
        default_object_namespace = get_property_or_default(properties, KubernetesDeploymentLocation.DEFAULT_OBJECT_NAMESPACE_PROP, KubernetesDeploymentLocation.DEFAULT_OBJECT_NAMESPACE_ALT2_PROP)
        if default_object_namespace is not None:
            kwargs['default_object_namespace'] = default_object_namespace
        return KubernetesDeploymentLocation(name, client_config, **kwargs)

    def __init__(self, name, client_config, default_object_namespace=DEFAULT_NAMESPACE):
        self.name = name
        KubernetesSingleConfigValidator.validate(client_config)
        self.client_config = client_config
        self.default_object_namespace = default_object_namespace
        self.config_files_created = []

    def write_config_file(self, path=None):
        """
        Writes the client configuration to a file on disk so it may be used by the Kubernetes client

        Args:
            path (str): Optionally control the path the configuration is written to. Defaults to a temporary file created with tempfile.mkstemp()

        Returns:
            the path to the configuration file
        """
        is_temp = False
        if path is None:
            is_temp = True
            file_handle, path = tempfile.mkstemp(prefix='kubeconf', suffix='.yaml')
            os.close(file_handle)
        with open(path, 'w') as f:
            yaml.dump(self.client_config, f)
        self.config_files_created.append({'path': path, 'is_temp': is_temp})
        return path

    def clear_config_files(self, temp_only=False):
        remaining_config_files = []
        for config_file in self.config_files_created:
            should_remove = temp_only == False or config_file['is_temp']
            if should_remove and os.path.exists(config_file['path']):
                os.remove(config_file['path'])
            else:
                remaining_config_files.append(config_file)
        self.config_files_created = remaining_config_files
        
    def to_dict(self):
        """
        Produces a dictionary copy of the deployment location

        Returns: 
            the deployment location configuration as a dictionary. For example:
            
            {
                'name': 'Test',
                'properties': {
                    'clientConfig': { ... },
                    'defaultObjectNamespace': 'default'
                }
            }
        """
        return {
            KubernetesDeploymentLocation.NAME: self.name,
            KubernetesDeploymentLocation.PROPERTIES: {
                KubernetesDeploymentLocation.CONFIG_PROP: self.client_config,
                KubernetesDeploymentLocation.DEFAULT_OBJECT_NAMESPACE_PROP: self.default_object_namespace
            }
        }

class KubernetesConfigValidationError(Exception):
    pass

class KubernetesSingleConfigValidator:
    """
    Validates Kubernetes configuration is for a single cluster
    """

    @staticmethod
    def validate(config):
        KubernetesSingleConfigValidator(config).run_validation()

    def __init__(self, config):
        self.config = config

    def run_validation(self):
        cluster = self.__validate_single_named_item('clusters')
        user = self.__validate_single_named_item('users')
        context = self.__validate_single_named_item('contexts')
        self.__validate_context_is_for_cluster(context, cluster)
        self.__validate_context_is_for_user(context, user)
        self.__validate_context_is_current(context)

    def __validate_single_named_item(self, in_key):
        if in_key not in self.config:
            raise KubernetesConfigValidationError(f'Config missing \'{in_key}\'')
        values = self.config.get(in_key)
        if not isinstance(values, list):
            raise KubernetesConfigValidationError(f'Config item \'{in_key}\' expected to be a list but was \'{type(values).__name__}\'')
        num_of_values = len(values)
        if num_of_values != 1:
            raise KubernetesConfigValidationError(f'Config item \'{in_key}\' expected to be a list of one but there are {num_of_values} elements')
        if 'name' not in values[0]:
            raise KubernetesConfigValidationError(f'Config item \'{in_key}[0]\' missing \'name\'')
        return values[0]

    def __validate_context_is_for_cluster(self, context, cluster):
        context_name = context.get('name')
        context_details = context.get('context')
        context_cluster = context_details.get('cluster')
        cluster_name = cluster.get('name')
        if context_cluster != cluster_name:
            raise KubernetesConfigValidationError(f'Config context \'{context_name}\' should have a cluster value of \'{cluster_name}\' but was \'{context_cluster}\'')
    
    def __validate_context_is_for_user(self, context, user):
        context_name = context.get('name')
        context_details = context.get('context')
        context_user = context_details.get('user')
        username = user.get('name')
        if context_user != username:
            raise KubernetesConfigValidationError(f'Config context \'{context_name}\' should have a user value of \'{username}\' but was \'{context_user}\'')
        
    def __validate_context_is_current(self, context):
        current_context = self.config.get('current-context')
        context_name = context.get('name')
        if current_context != context_name:
            raise KubernetesConfigValidationError(f'Config current-context should be \'{context_name}\' but was \'{current_context}\'')