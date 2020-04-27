# Kubernetes Deployment Location

This deployment location structure is intended for any driver connecting to Kubernetes.

# Properties

An example Kubernetes deployment location has the following properties structure:

| Name            | Default | Required                           | Detail                                                                                                                     |
| --------------- | ------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| client_config/clientConfig      | -       | Y                                  | A multiline string version of the kubectl config file used to access the target cluster (see more details below) |
| default_object_namespace/defaultObjectNamespace | default | N | The default namespace to be used when deploying Kubernetes objects. This value should only be used when the object does not have a specified namespace in the metadata section of it's configuration |

Example location:

```
{
  'name': 'MyKubeCluster',
  'properties': {
    'default_object_namespace': 'default',
    'client_config': |
      apiVersion: v1
      clusters:
      - cluster:
          certificate-authority-data: <sensitive data removed from docs>
          server: https://1.2.3.4:6443
        name: kubernetes
      contexts:
      - context:
          cluster: kubernetes
          user: kubernetes-admin
        name: kubernetes-admin@kubernetes
      current-context: kubernetes-admin@kubernetes
      kind: Config
      preferences: {}
      users:
      - name: kubernetes-admin
        user:
          client-certificate-data: <sensitive data removed from docs>
  }
}
```

The `clientConfig` will be checked for configurations considered unreasonable for use on a single Kubernetes cluster, that means the config must:

- have only ONE entry in the `clusters` list
- have only ONE entry in the `users` list
- have only ONE entry in the `contexts` list
- the single entry in the `contexts` list must be configured with the name of the user in `users` and name of the cluster in `clusters`
- the `current-context` must be set to the name of the single entry in `contexts`

This ensures your configuration does not contain unnecessary details about users and clusters which are not used.  

# Obtaining clientConfig/client_config

The easiest way to obtain the client configuration for your Kubernetes cluster is to run the `config view` command from a machine with existing kubectl access:

```
# --raw is required to prevent omission certificate values
kubectl config view --raw
```

This will output a YAML document. If you don't have kubectl access you can obtain this document by accessing `/etc/kubernetes/admin.conf` from your Kubernetes master host:

```
sudo cat /etc/kubernetes/admin.conf
```

Copy the contents from the console into your deployment location properties as a multiline string value:

```
clientConfig: |
  apiVersion: v1
  clusters:
  - cluster:
      certificate-authority-data: <sensitive data removed from docs>
      server: https://1.2.3.4:6443
    name: kubernetes
  contexts:
  - context:
      cluster: kubernetes
      user: kubernetes-admin
    name: kubernetes-admin@kubernetes
  current-context: kubernetes-admin@kubernetes
  kind: Config
  preferences: {}
  users:
  - name: kubernetes-admin
    user:
      client-certificate-data: <sensitive data removed from docs>
```

**Note: ensure you have only one cluster, user and context and the current context is configured with the correct context name**

# Usage

The classes for the Kubernetes deployment location can be found in the `igniton.locations.kubernetes` module. 

You can easily parse the raw deployment location data passed to a request using the `from_dict` static method on the class:

```python
from igniton.locations.kubernetes import KubernetesDeploymentLocation

class ResourceDriver(Service, ResourceDriverCapability):
  
    def execute_lifecycle(self, lifecycle_name, driver_files, system_properties, resource_properties, request_properties, internal_resources, deployment_location):
        kube_location = KubernetesDeploymentLocation.from_dict(deployment_location)
```

Once you have a Kubernetes location you can access the client configuration dictionary with the `client_config` attribute. To use most Kubernetes client libraries, you will need to write this client configuration to a file before it can be used. The `KubernetesDeploymentLocation` class offers a function to achieve this for you:

```
# Writes to a temporary file created with the tempfile module
path = kube_location.write_config_file()

# Write to a custom path
path = 'path/of/my/choosing.yaml'
kube_location.write_config_file(path)
```

It is the responsibility of the user to remove config files that are no longer required. For convenience, the deployment location class offers a function to clear out any configuration files created with `write_config_file`:

```
# Removes all configuration files created by this location
kube_location.clear_config_files()

# Removes only the configuration files created without a given custom path and therefore using a temporary file
kube_location.clear_config_files(temp_only=True)
```

The `clear_config_files` will remove any reference to the file paths once they have been deleted and will not raise an error if the files have been deleted prior to being called.