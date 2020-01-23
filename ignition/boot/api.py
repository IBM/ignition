from ignition.boot.config import BootProperties, ApplicationProperties, ApiProperties, DynamicServiceConfigurator, DynamicApiConfigurator, PropertyGroups, BootstrapApplicationConfiguration
from ignition.boot.app import BootstrapRunner
from ignition.api.exceptions import ErrorResponseConverter, validation_error_handler
from ignition.service.config import YmlFileSource, EnvironmentVariableYmlFileSource
from ignition.boot.configurators.infrastructureapi import InfrastructureApiConfigurator, InfrastructureServicesConfigurator
from ignition.boot.configurators.lifecycleapi import LifecycleApiConfigurator, LifecycleServicesConfigurator
from ignition.boot.configurators.messaging import MessagingConfigurator
from ignition.boot.configurators.jobqueue import JobQueueConfigurator
from ignition.boot.configurators.management import ManagementApiConfigurator, ManagmentServicesConfigurator
from ignition.service.infrastructure import InfrastructureProperties
from ignition.service.lifecycle import LifecycleProperties
from ignition.service.messaging import MessagingProperties
from ignition.service.queue import JobQueueProperties
from ignition.service.management import ManagementProperties
from jsonschema import ValidationError

SERVICE_CONFIGURATORS = [InfrastructureServicesConfigurator(), LifecycleServicesConfigurator(), MessagingConfigurator(), JobQueueConfigurator(), ManagmentServicesConfigurator()]
API_CONFIGURATORS = [InfrastructureApiConfigurator(), LifecycleApiConfigurator(), ManagementApiConfigurator()]
MANDATORY_PROPERTY_GROUPS = [ApplicationProperties, ApiProperties]
ADDITIONAL_PROPERTY_GROUPS = [BootProperties, InfrastructureProperties, LifecycleProperties, MessagingProperties, JobQueueProperties, ManagementProperties]


def build_driver(app_name, vim=False, lifecycle=False):
    builder = build_app(app_name)
    if vim == True:
        builder = configure_vim_driver(builder)
    if lifecycle == True:
        builder = configure_lifecycle_driver(builder)
    return builder
    
def build_vim_driver(app_name):
    builder = build_app(app_name)
    return configure_vim_driver(builder)

def configure_vim_driver(builder):
    boot_config = builder.property_groups.get_property_group(BootProperties)
    boot_config.infrastructure.api_enabled = True
    boot_config.infrastructure.api_service_enabled = True
    boot_config.infrastructure.service_enabled = True
    boot_config.infrastructure.monitoring_service_enabled = True
    boot_config.infrastructure.messaging_service_enabled = True
    boot_config.messaging.postal_enabled = True
    boot_config.messaging.delivery_enabled = True
    boot_config.messaging.inbox_enabled = True
    boot_config.job_queue.service_enabled = True
    return builder

def build_lifecycle_driver(app_name):
    builder = build_app(app_name)
    return configure_lifecycle_driver(builder)

def configure_lifecycle_driver(builder):
    boot_config = builder.property_groups.get_property_group(BootProperties)
    boot_config.lifecycle.api_enabled = True
    boot_config.lifecycle.api_service_enabled = True
    boot_config.lifecycle.service_enabled = True
    boot_config.lifecycle.monitoring_service_enabled = True
    boot_config.lifecycle.messaging_service_enabled = True
    boot_config.lifecycle.script_file_manager_service_enabled = True
    boot_config.messaging.postal_enabled = True
    boot_config.messaging.delivery_enabled = True
    boot_config.messaging.inbox_enabled = True
    boot_config.job_queue.service_enabled = True
    return builder

def build_vnfc_driver(app_name):
    return build_lifecycle_driver(app_name)

def build_app(app_name):
    builder = ApplicationBuilder(app_name)
    for property_group in ADDITIONAL_PROPERTY_GROUPS:
        builder.add_property_group(property_group())
    builder.service_configurators = SERVICE_CONFIGURATORS.copy()
    builder.api_configurators = API_CONFIGURATORS.copy()
    error_converter = ErrorResponseConverter()
    error_converter.register_handler(ValidationError, validation_error_handler)
    builder.set_error_converter(error_converter)
    return builder

class ApplicationBuilder:

    def __init__(self, app_name=None):
        self.app_name = app_name
        self.property_sources = []
        self.property_groups = PropertyGroups()
        for property_group in MANDATORY_PROPERTY_GROUPS:
            self.property_groups.add_property_group(property_group())
        self.service_configurators = []
        self.api_configurators = []
        self.api_error_converter = None

    def include_file_config_properties(self, file_path, **kwargs):
        self.property_sources.append(YmlFileSource(file_path, **kwargs))
        return self

    def include_environment_config_properties(self, environment_variable, **kwargs):
        self.property_sources.append(EnvironmentVariableYmlFileSource(environment_variable, **kwargs))
        return self

    def add_property_group(self, property_group):
        self.property_groups.add_property_group(property_group)
        return self

    def add_api_configurator(self, api_configurator):
        self.api_configurators.append(api_configurator)
        return self

    def add_service_configurator(self, service_configurator):
        self.service_configurators.append(service_configurator)
        return self

    def add_service(self, service_class, *args, **required_capabilities):
        self.service_configurators.append(DynamicServiceConfigurator(service_class, *args, **required_capabilities))
        return self

    def add_api(self, api_spec, api_capability):
        self.api_configurators.append(DynamicApiConfigurator(api_spec, api_capability))
        return self

    def set_error_converter(self, error_converter):
        self.api_error_converter = error_converter
        return self

    def build(self):
        return BootstrapApplicationConfiguration(self.app_name, self.property_sources, self.property_groups, self.service_configurators, self.api_configurators, self.api_error_converter)

    def configure(self):
        configuration = self.build()
        return BootstrapRunner(configuration).init_app()

    def run(self):
        app = self.configure()
        app.run()
        return app
