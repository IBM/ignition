
SYSTEM_PROPERTIES_KEY = 'systemProperties'
DEPLOYMENT_LOCATION_KEY = 'deploymentLocationInst'

class ResourceContextBuilder:
    """
    Helper class to build dictionary to be used as the context for rendering a template 
    from the 3 expected property sources of any driver request (properties, system properties and the deployment location)

    Properties make up the root of the dictionary. System properties are added under the 'systemProperties' key. 
    Deployment Location data is added under the `deploymentLocationInst` so it does not collide with the 'deploymentLocation' property.

    Example:
        Input:
            properties: {'propertyA': 'valueA'}
            system_properties: {'resourceId': '123', 'resourceName': 'example'}
            deployment_location = {'name': 'example-location', 'type': 'test', 'properties': {'dlPropA': 'location property'}}
        Result:
        {
            'propertyA' : 'valueA',
            'systemProperties': {
                'resourceId': '123',
                'resourceName': 'example'
            },
            'deploymentLocationInst': {
                'name': 'example-location',
                'type': 'test',
                'properties': {
                    'dlPropA': 'location-property'
                }
            }
        }

    Attributes:
        result (dict): the context built with this instance
    """

    def __init__(self, system_properties, properties, deployment_location):
        """
        Initiate a builder

        Args:
            system_properties (dict or PropValueMap): dictionary of system_properties to include
            properties (dict or PropValueMap): dictionary of properties to include
            deployment_location (dict): dictionary representing the deployment location details
        """
        self.result = {
            SYSTEM_PROPERTIES_KEY: {},
            DEPLOYMENT_LOCATION_KEY: {}
        }
        self.add_system_properties(system_properties)
        self.add_properties(properties)
        self.set_deployment_location(deployment_location)

    def add_properties(self, properties):
        """
        Add extra properties. If any of the given properties are already present the existing values will be replaced by the incoming values

        Args:
            properties (dict or PropValueMap): dictionary of properties to include

        Returns:
            this builder
        """
        for k,v in properties.items():
            if k == SYSTEM_PROPERTIES_KEY:
                raise ValueError(f'property with name \'{SYSTEM_PROPERTIES_KEY}\' cannot be used as this is a reserved word')
            if k == DEPLOYMENT_LOCATION_KEY:
                raise ValueError(f'property with name \'{DEPLOYMENT_LOCATION_KEY}\' cannot be used as this is a reserved word')
            self.result[k] = v
        return self

    def add_property(self, key, value):
        """
        Add extra property. If the property is already present the existing value will be replaced by the incoming value

        Args:
            key (str): name of the property
            value: value to assign to the property

        Returns:
            this builder
        """
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