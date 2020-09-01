from ignition.utils.propvaluemap import PropValueMap
from ignition.model import associated_topology

SYSTEM_PROPERTIES_KEY = 'system_properties'
REQUEST_PROPERTIES_KEY = 'request_properties'
DEPLOYMENT_LOCATION_KEY = 'deployment_location'
ASSOCIATED_TOPOLOGY_KEY = 'associated_topology'

class ResourceContextBuilder:
    """
    Helper class to build dictionary to be used as the context for rendering a template 
    from the 4 expected property sources of any driver request (resource properties, system properties, request properties and the deployment location)

    Resource properties make up the root of the dictionary. System properties are added under the 'system_properties' key. 
    Deployment Location data is added under the `deployment_location` so it does not collide with the 'deploymentLocation' property.

    Example:
        Input:
            resource_properties: {'propertyA': 'valueA'}
            system_properties: {'resourceId': '123', 'resourceName': 'example'}
            deployment_location = {'name': 'example-location', 'type': 'test', 'properties': {'dlPropA': 'location property'}}
            request_properties: {'requestA': 'request valueA'}
            associated_topology: {'infrastructureNameA': {'infrastructureId': 'a58b884d-1209-49e0-8966-13fcad548f4a', 'infrastructureType': 'Openstack'}}
        Result:
        {
            'propertyA' : 'valueA',
            'system_properties': {
                'resourceId': '123',
                'resourceName': 'example'
            },
            'deployment_location': {
                'name': 'example-location',
                'type': 'test',
                'properties': {
                    'dlPropA': 'location-property'
                }
            },
            'request_properties': {
                'requestA': 'request_valueA'
            },
            associated_topology: {
                'infrastructureNameA': {
                    'infrastructureId': 'a58b884d-1209-49e0-8966-13fcad548f4a',
                    'infrastructureType': 'Openstack'
                }
            }
        }

    Attributes:
        result (dict): the context built with this instance
    """

    def __init__(self, system_properties, resource_properties, request_properties, deployment_location, associated_topology = None):
        """
        Initiate a builder

        Args:
            system_properties (dict or PropValueMap): dictionary of system_properties to include
            resource_properties (dict or PropValueMap): dictionary of resource properties to include
            request_properties (dict or PropValueMap): dictionary of request properties to include
            deployment_location (dict): dictionary representing the deployment location details
            associated_topology (dict): dictionary representing the infrastructure details
        """
        self.result = {
            SYSTEM_PROPERTIES_KEY: {},
            REQUEST_PROPERTIES_KEY: {},
            DEPLOYMENT_LOCATION_KEY: {},
            ASSOCIATED_TOPOLOGY_KEY: {}
        }
        self.add_system_properties(system_properties)
        self.add_resource_properties(resource_properties)
        self.add_request_properties(request_properties)
        self.set_deployment_location(deployment_location)
        self.set_associated_topology(associated_topology)

    def __reserved_key_error_msg(self, reserved_key):
        return f'property with name \'{reserved_key}\' cannot be used as this is a reserved word'

    def __check_for_reserved_key(self, key):
        if key in [SYSTEM_PROPERTIES_KEY, DEPLOYMENT_LOCATION_KEY, REQUEST_PROPERTIES_KEY, ASSOCIATED_TOPOLOGY_KEY]:
            raise ValueError(self.__reserved_key_error_msg(key))

    def add_resource_properties(self, resource_properties):
        """
        Add extra resource properties. If any of the given properties are already present the existing values will be replaced by the incoming values

        Args:
            resource_properties (dict or PropValueMap): dictionary of properties to include

        Returns:
            this builder
        """
        if isinstance(resource_properties, PropValueMap):
            for k,v in resource_properties.items_with_types():
                value_type = v.get('type')
                value = v.get('value')
                if value_type == 'key':
                    value = {
                        'keyName': v.get('keyName'),
                        'publicKey': v.get('publicKey'),
                        'privateKey': v.get('privateKey')
                    }
                self.__check_for_reserved_key(k)
                self.result[k] = value
        else:
            for k,v in resource_properties.items():
                self.__check_for_reserved_key(k)
                self.result[k] = v
        return self

    def add_resource_property(self, key, value):
        """
        Add extra resource property. If the property is already present the existing value will be replaced by the incoming value

        Args:
            key (str): name of the property
            value: value to assign to the property

        Returns:
            this builder
        """
        self.__check_for_reserved_key(key)
        self.result[key] = value 
        return self

    def add_system_properties(self, system_properties):
        """
        Add extra system properties. If any of the given system properties are already present the existing values will be replaced by the incoming values

        Args:
            system_properties (dict or PropValueMap): dictionary of system properties to include

        Returns:
            this builder
        """
        if isinstance(system_properties, PropValueMap):
            parsed_system_properties = {}
            for k,v in system_properties.items_with_types():
                value_type = v.get('type')
                value = v.get('value')
                if value_type == 'key':
                    value = {
                        'keyName': v.get('keyName'),
                        'publicKey': v.get('publicKey'),
                        'privateKey': v.get('privateKey')
                    }
                parsed_system_properties[k] = value
            self.result[SYSTEM_PROPERTIES_KEY].update(parsed_system_properties)
        else:
            self.result[SYSTEM_PROPERTIES_KEY].update(system_properties)
        return self

    def add_system_property(self, key, value):
        """
        Add extra system property. If the system property is already present the existing value will be replaced by the incoming value

        Args:
            key (str): name of the system property
            value: value to assign to the system property

        Returns:
            this builder
        """
        self.result[SYSTEM_PROPERTIES_KEY][key] = value 
        return self

    def add_request_properties(self, request_properties):
        """
        Add extra request properties. If any of the given request properties are already present the existing values will be replaced by the incoming values

        Args:
            request_properties (dict or PropValueMap): dictionary of request properties to include

        Returns:
            this builder
        """
        if isinstance(request_properties, PropValueMap):
            parsed_request_properties = {}
            for k,v in request_properties.items_with_types():
                value_type = v.get('type')
                value = v.get('value')
                if value_type == 'key':
                    value = {
                        'keyName': v.get('keyName'),
                        'publicKey': v.get('publicKey'),
                        'privateKey': v.get('privateKey')
                    }
                parsed_request_properties[k] = value
            self.result[REQUEST_PROPERTIES_KEY].update(parsed_request_properties)
        else:
            self.result[REQUEST_PROPERTIES_KEY].update(request_properties)
        return self

    def add_request_property(self, key, value):
        """
        Add extra request property. If the request property is already present the existing value will be replaced by the incoming value

        Args:
            key (str): name of the request property
            value: value to assign to the request property

        Returns:
            this builder
        """
        self.result[REQUEST_PROPERTIES_KEY][key] = value 
        return self

    def set_deployment_location(self, deployment_location):
        """
        Change the value of the deployment location instance

        Args:
            deployment_location (dict): dictionary representing the deployment location details

        Returns:
            this builder
        """
        self.result[DEPLOYMENT_LOCATION_KEY] = deployment_location
        return self
    
    def set_associated_topology(self, associated_topology):
        """
        Change the value of the associated topology

        Args:
            associated topology (dict): dictionary representing the associated topology details

        Returns:
            this builder
        """
        if associated_topology is not None:
            self.result[ASSOCIATED_TOPOLOGY_KEY] = associated_topology.to_dict()
        return self

    def add_deployment_location_property(self, key, value):
        """
        Add extra deployment location property. If the deployment location property is already present the existing value will be replaced by the incoming value

        Args:
            key (str): name of the system property
            value: value to assign to the system property

        Returns:
            this builder
        """
        if 'properties' not in self.result[DEPLOYMENT_LOCATION_KEY]:
            self.result[DEPLOYMENT_LOCATION_KEY]['properties'] = {}
        self.result[DEPLOYMENT_LOCATION_KEY]['properties'][key] = value
        return self