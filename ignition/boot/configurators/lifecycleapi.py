import logging
from ignition.boot.config import BootProperties
from ignition.boot.connexionutils import build_resolver_to_instance
from ignition.service.framework import ServiceRegistration
from ignition.service.messaging import PostalCapability, TopicsProperties, TopicCreator, MessagingProperties
from ignition.service.queue import JobQueueCapability
from ignition.service.lifecycle import LifecycleProperties, LifecycleApiCapability, LifecycleServiceCapability, LifecycleDriverCapability, LifecycleExecutionMonitoringCapability, LifecycleMessagingCapability, LifecycleScriptFileManagerCapability, LifecycleApiService, LifecycleService, LifecycleExecutionMonitoringService, LifecycleMessagingService, LifecycleScriptFileManagerService
from ignition.boot.configurators.utils import validate_no_service_with_capability_exists

logger = logging.getLogger(__name__)


class LifecycleApiConfigurator():

    def __init__(self):
        pass

    def configure(self, configuration, service_register, service_instances, api_register):
        self.__configure_api_spec(configuration, service_register, service_instances, api_register)

    def __configure_api_spec(self, configuration, service_register, service_instances, api_register):
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        lifecycle_config = configuration.property_groups.get_property_group(LifecycleProperties)
        if auto_config.lifecycle.api_enabled is True:
            logger.debug('Bootstrapping Lifecycle API')
            api_spec = lifecycle_config.api_spec
            if api_spec is None:
                raise ValueError('lifecycle.api_spec must be set when bootstrap.lifecycle.api_enabled is True')
            api_service_class = service_register.get_service_offering_capability(LifecycleApiCapability)
            if api_service_class is None:
                raise ValueError('No service has been registered with the LifecycleApiCapability, did you forget to register one? Or try enabling bootstrap.lifecycle.api_service_enabled')
            api_service_instance = service_instances.get_instance(api_service_class)
            if api_service_instance is None:
                raise ValueError('No instance of the Lifecycle API service has been built')
            api_register.register_api(api_spec, resolver=build_resolver_to_instance(api_service_instance))
        else:
            logger.debug('Disabled: bootstrapped Lifecycle API')


class LifecycleServicesConfigurator():

    def __init__(self):
        self.driver_registered = False

    def configure(self, configuration, service_register):
        self.__configure_api_service(configuration, service_register)
        self.__configure_scripts_file_manager(configuration, service_register)
        self.__configure_service(configuration, service_register)
        self.__configure_monitoring(configuration, service_register)
        self.__configure_messaging(configuration, service_register)

    def __configure_api_service(self, configuration, service_register):
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        if auto_config.lifecycle.api_service_enabled is True:
            logger.debug('Bootstrapping Lifecycle API Service')
            # Check if a user has enabled the auto configuration of the Lifecycle API service but has also added their own
            validate_no_service_with_capability_exists(service_register, LifecycleApiCapability, 'Lifecycle API', 'bootstrap.lifecycle.api_service_enabled')
            service_register.add_service(ServiceRegistration(LifecycleApiService, service=LifecycleServiceCapability))
        else:
            logger.debug('Disabled: bootstrapped Lifecycle API Service')

    def __configure_scripts_file_manager(self, configuration, service_register):
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        if auto_config.lifecycle.script_file_manager_service_enabled is True:
            logger.debug('Bootstrapping Lifecycle Script File Manager Service')
            validate_no_service_with_capability_exists(service_register, LifecycleScriptFileManagerCapability, 'Lifecycle Script File Manager Service',
                                                       'bootstrap.lifecycle.script_file_manager_service_enabled')
            service_register.add_service(ServiceRegistration(LifecycleScriptFileManagerService, lifecycle_config=LifecycleProperties))
        else:
            logger.debug('Disabled: bootstrapped Lifecycle Script File Manager Service')

    def __configure_service(self, configuration, service_register):
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        if auto_config.lifecycle.service_enabled is True:
            logger.debug('Bootstrapping Lifecycle Service')
            # Check if a user has enabled the auto configuration of the Lifecycle service but has also added their own
            validate_no_service_with_capability_exists(service_register, LifecycleServiceCapability, 'Lifecycle Service', 'bootstrap.lifecycle.service_enabled')
            required_capabilities = {
                'driver': LifecycleDriverCapability,
                'lifecycle_config': LifecycleProperties,
                'script_file_manager': LifecycleScriptFileManagerCapability
            }
            lifecycle_config = configuration.property_groups.get_property_group(LifecycleProperties)
            if lifecycle_config.async_messaging_enabled is True:
                required_capabilities['lifecycle_monitor_service'] = LifecycleExecutionMonitoringCapability
            service_register.add_service(ServiceRegistration(LifecycleService, **required_capabilities))
        else:
            logger.debug('Disabled: bootstrapped Lifecycle Service')

    def __configure_monitoring(self, configuration, service_register):
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        if auto_config.lifecycle.monitoring_service_enabled is True:
            logger.debug('Bootstrapping Lifecycle Monitoring Service')
            validate_no_service_with_capability_exists(service_register, LifecycleExecutionMonitoringCapability,
                                                       'Lifecycle Execution Monitoring Service', 'bootstrap.lifecycle.monitoring_service_enabled')
            service_register.add_service(ServiceRegistration(LifecycleExecutionMonitoringService, job_queue_service=JobQueueCapability,
                                                             lifecycle_messaging_service=LifecycleMessagingCapability, driver=LifecycleDriverCapability))
        else:
            logger.debug('Disabled: bootstrapped Lifecycle Monitoring Service')

    def __configure_messaging(self, configuration, service_register):
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        if auto_config.lifecycle.messaging_service_enabled is True:
            logger.debug('Bootstrapping Lifecycle Messaging Service')
            validate_no_service_with_capability_exists(service_register, LifecycleMessagingCapability, 'Lifecycle Messaging Service', 'bootstrap.lifecycle.messaging_service_enabled')
            messaging_config = configuration.property_groups.get_property_group(MessagingProperties)
            if messaging_config.connection_address is None:
                raise ValueError('messaging.connection_address must be set when bootstrap.lifecycle.messaging_service_enabled')
            if messaging_config.topics.lifecycle_execution_events is None:
                raise ValueError('messaging.topics.lifecycle_execution_events must be set when bootstrap.lifecycle.messaging_service_enabled')
            TopicCreator().create_topic_if_needed(messaging_config.connection_address, messaging_config.topics.lifecycle_execution_events)
            service_register.add_service(ServiceRegistration(LifecycleMessagingService, postal_service=PostalCapability, topics_configuration=TopicsProperties))
        else:
            logger.debug('Disabled: bootstrapped Lifecycle Messaging Service')
