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
        name = dl_data.get(KubernetesDeploymentLocation.NAME, None)
        if name is None:
            raise InvalidDeploymentLocationError('Deployment location missing \'{0}\' value'.format(KubernetesDeploymentLocation.NAME))
        properties = dl_data.get(KubernetesDeploymentLocation.PROPERTIES, None)
        if properties is None:
            raise InvalidDeploymentLocationError('Deployment location missing \'{0}\' value'.format(KubernetesDeploymentLocation.PROPERTIES))
        client_config = get_property_or_default(properties, KubernetesDeploymentLocation.CONFIG_PROP, KubernetesDeploymentLocation.CONFIG_ALT2_PROP, error_if_not_found=True)
        if type(client_config) is str:
            client_config = yaml.safe_load(client_config)
        kwargs = {}
        default_object_namespace = get_property_or_default(properties, KubernetesDeploymentLocation.DEFAULT_OBJECT_NAMESPACE_PROP, KubernetesDeploymentLocation.DEFAULT_OBJECT_NAMESPACE_ALT2_PROP)
        if default_object_namespace is not None:
            kwargs['default_object_namespace'] = default_object_namespace
        return KubernetesDeploymentLocation(name, client_config, **kwargs)

    def __init__(self, name, client_config, default_object_namespace=DEFAULT_NAMESPACE):
        self.name = name
        self.client_config = client_config
        self.default_object_namespace = default_object_namespace

    def write_config_file(self, path=None):
        """
        Writes the client configuration to a file on disk so it may be used by the Kubernetes client

        Args:
            path (str): Optionally control the path the configuration is written to. Defaults to a temporary file created with tempfile.mkstemp()

        Returns:
            the path to the configuration file
        """
        if path is None:
            file_handle, path = tempfile.mkstemp(prefix='kubeconf', suffix='.yaml')
            os.close(file_handle)
        with open(path, 'w') as f:
            yaml.dump(self.client_config, f)
        return path

    def to_dict(self):
        """
        Produces a dictionary copy of the deployment location

        Returns: 
            the deployment location configuration as a dictionary. For example:
            
            {
                'name': 'Test',
                'properties': {
                    'client_config': { ... },
                    'default_object_namespace': 'default'
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