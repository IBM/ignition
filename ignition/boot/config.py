from ignition.service.framework import Service, Capability, ServiceRegistration
from ignition.boot.connexionutils import build_resolver_to_instance
from ignition.service.config import ConfigurationPropertiesGroup, ConfigurationProperties, ConfigParserService


class BootProperties(ConfigurationPropertiesGroup):

    def __init__(self):
        super().__init__('bootstrap')
        self.messaging = BootMessagingProperties()
        self.job_queue = BootJobQueueProperties()
        self.resource_driver = BootResourceDriverProperties()
        self.management = BootManagementProperties()
        self.request_queue = BootRequestQueueProperties()
        self.templating = BootTemplatingProperties()
        self.movedapis = BootMovedApisProperties()
        self.progress_event_log = BootProgressEventLogProperties()

class BootMovedApisProperties(ConfigurationProperties):
    
    def __init__(self):
        self.infrastructure_enabled = False
        self.lifecycle_enabled = False

class BootManagementProperties(ConfigurationProperties):

    def __init__(self):
        self.api_enabled = True
        self.api_service_enabled = True
        self.service_enabled = True
        self.health = BootManagementHealthProperties()

class BootManagementHealthProperties(ConfigurationProperties):

    def __init__(self):
        self.service_enabled = True


class BootRequestQueueProperties(ConfigurationProperties):

    def __init__(self):
        self.enabled = False

class BootResourceDriverProperties(ConfigurationProperties):

    def __init__(self):
        self.api_enabled = False
        self.api_service_enabled = False
        self.service_enabled = False
        self.service_driver = None
        self.lifecycle_monitoring_service_enabled = False
        self.lifecycle_messaging_service_enabled = False
        self.driver_files_manager_service_enabled = False


class BootMessagingProperties(ConfigurationProperties):

    def __init__(self):
        self.postal_enabled = False
        self.delivery_enabled = False
        self.inbox_enabled = False


class BootJobQueueProperties(ConfigurationProperties):

    def __init__(self):
        self.service_enabled = False

class BootTemplatingProperties(ConfigurationProperties):

    def __init__(self):
        self.service_enabled = False
        self.resource_context_service_enabled = False

class BootProgressEventLogProperties(ConfigurationProperties):
    
    def __init__(self):
        self.service_enabled = False
        self.serializer_service_enabled = False

class ApiProperties(ConfigurationPropertiesGroup, Service, Capability):

    def __init__(self):
        super().__init__('api')
        self.specification_dir = None


class ApplicationProperties(ConfigurationPropertiesGroup, Service, Capability):

    def __init__(self):
        super().__init__('application')
        self.port = None
        self.connexion_init_props = {}
        self.connexion_runtime_props = {}
        self.ssl = SSLProperties()


class SSLProperties(ConfigurationProperties):

    def __init__(self):
        self.enabled = False
        self.cert_dir = None


class PropertyGroupError(Exception):
    pass


class PropertyGroups:

    def __init__(self):
        self.property_groups = {}

    def add_property_group(self, property_group):
        if property_group.__class__ in self.property_groups:
            raise PropertyGroupError('Attempt to add duplicate instance for property group class: {0}'.format(property_group.__class__))
        self.property_groups[property_group.__class__] = property_group

    def get_property_group(self, property_group_class):
        if property_group_class in self.property_groups:
            instance = self.property_groups[property_group_class]
            return instance
        else:
            raise PropertyGroupError('No instance for property group class: {0}'.format(property_group_class))

    def all_groups(self):
        return list(self.property_groups.values())


class BootstrapApplicationConfiguration:

    def __init__(self, app_name=None, property_sources=[], property_groups=None, service_configurators=[], api_configurators=[], api_error_converter=None):
        self.app_name = app_name
        self.property_sources = property_sources
        if property_groups is None:
            property_groups = PropertyGroups()
        self.property_groups = property_groups
        self.service_configurators = service_configurators
        self.api_configurators = api_configurators
        self.api_error_converter = api_error_converter


class DynamicServiceConfigurator:
    def __init__(self, service_class, *args, **required_capabilities):
        self.service_class = service_class
        self.args = args
        self.required_capabilities = required_capabilities

    def configure(self, configuration, service_register):
        service_register.add_service(ServiceRegistration(self.service_class, *self.args, **self.required_capabilities))


class DynamicApiConfigurator:
    def __init__(self, api_spec, api_capability):
        self.api_spec = api_spec
        self.api_capability = api_capability

    def configure(self, configuration, service_register, service_instances, api_register):
        api_service_class = service_register.get_service_offering_capability(self.api_capability)
        if api_service_class is None:
            raise ValueError('No service has been registered with the capability: {0}'.format(self.api_capability))
        api_service_instance = service_instances.get_instance(api_service_class)
        if api_service_instance is None:
            raise ValueError('No instance of the {0} service has been built'.format(self.api_capability))
        api_register.register_api(self.api_spec, resolver=build_resolver_to_instance(api_service_instance))
