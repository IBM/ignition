import logging
from ignition.boot.config import BootProperties
from ignition.boot.connexionutils import build_resolver_to_instance
from ignition.service.framework import ServiceRegistration
from ignition.service.messaging import PostalCapability, TopicsProperties, TopicCreator, MessagingProperties
from ignition.service.queue import JobQueueCapability
from ignition.service.requestqueue import LifecycleRequestQueueCapability
from ignition.service.resourcedriver import (ResourceDriverProperties, ResourceDriverApiCapability, ResourceDriverServiceCapability, 
                                        ResourceDriverHandlerCapability, LifecycleExecutionMonitoringCapability, LifecycleMessagingCapability, 
                                        DriverFilesManagerCapability, ResourceDriverApiService, ResourceDriverService, 
                                        LifecycleExecutionMonitoringService, LifecycleMessagingService, DriverFilesManagerService)
from ignition.boot.configurators.utils import validate_no_service_with_capability_exists

logger = logging.getLogger(__name__)


class ResourceDriverApiConfigurator():

    def __init__(self):
        pass

    def configure(self, configuration, service_register, service_instances, api_register):
        self.__configure_api_spec(configuration, service_register, service_instances, api_register)

    def __configure_api_spec(self, configuration, service_register, service_instances, api_register):
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        resource_driver_config = configuration.property_groups.get_property_group(ResourceDriverProperties)
        if auto_config.resource_driver.api_enabled is True:
            logger.debug('Bootstrapping Resource Driver API')
            api_spec = resource_driver_config.api_spec
            if api_spec is None:
                raise ValueError('resource_driver.api_spec must be set when bootstrap.resource_driver.api_enabled is True')
            api_service_class = service_register.get_service_offering_capability(ResourceDriverApiCapability)
            if api_service_class is None:
                raise ValueError('No service has been registered with the ResourceDriverApiCapability, did you forget to register one? Or try enabling bootstrap.resource_driver.api_service_enabled')
            api_service_instance = service_instances.get_instance(api_service_class)
            if api_service_instance is None:
                raise ValueError('No instance of the Resource Driver API service has been built')
            api_register.register_api(api_spec, resolver=build_resolver_to_instance(api_service_instance))
        else:
            logger.debug('Disabled: bootstrapped Resource Driver API')


class ResourceDriverServicesConfigurator():

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
        if auto_config.resource_driver.api_service_enabled is True:
            logger.debug('Bootstrapping Resource Driver API Service')
            # Check if a user has enabled the auto configuration of the Lifecycle API service but has also added their own
            validate_no_service_with_capability_exists(service_register, ResourceDriverApiCapability, 'Resource Driver API', 'bootstrap.resource_driver.api_service_enabled')
            service_register.add_service(ServiceRegistration(ResourceDriverApiService, service=ResourceDriverServiceCapability))
        else:
            logger.debug('Disabled: bootstrapped Resource Driver API Service')

    def __configure_scripts_file_manager(self, configuration, service_register):
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        if auto_config.resource_driver.driver_files_manager_service_enabled is True:
            logger.debug('Bootstrapping Driver File Manager Service')
            validate_no_service_with_capability_exists(service_register, DriverFilesManagerCapability, 'Driver File Manager Service',
                                                       'bootstrap.resource_driver.driver_files_manager_service_enabled')
            service_register.add_service(ServiceRegistration(DriverFilesManagerService, resource_driver_config=ResourceDriverProperties))
        else:
            logger.debug('Disabled: bootstrapped Driver File Manager Service')

    def __configure_service(self, configuration, service_register):
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        if auto_config.resource_driver.service_enabled is True:
            logger.debug('Bootstrapping Resource Driver Service')
            # Check if a user has enabled the auto configuration of the Resource Driver service but has also added their own
            validate_no_service_with_capability_exists(service_register, ResourceDriverServiceCapability, 'Resource Driver Service', 'bootstrap.resource_driver.service_enabled')
            resource_driver_config = configuration.property_groups.get_property_group(ResourceDriverProperties)

            required_capabilities = {}
            if resource_driver_config.async_messaging_enabled is True:
                required_capabilities['lifecycle_monitor_service'] = LifecycleExecutionMonitoringCapability
            required_capabilities['handler'] = ResourceDriverHandlerCapability
            required_capabilities['resource_driver_config'] = ResourceDriverProperties
            required_capabilities['driver_files_manager'] = DriverFilesManagerCapability

            if resource_driver_config.lifecycle_request_queue.enabled is True:
                required_capabilities['lifecycle_request_queue'] = LifecycleRequestQueueCapability

            service_register.add_service(ServiceRegistration(ResourceDriverService, **required_capabilities))
        else:
            logger.debug('Disabled: bootstrapped Resource Driver Service')

    def __configure_monitoring(self, configuration, service_register):
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        if auto_config.resource_driver.lifecycle_monitoring_service_enabled is True:
            logger.debug('Bootstrapping Resource Driver Lifecycle Monitoring Service')
            validate_no_service_with_capability_exists(service_register, LifecycleExecutionMonitoringCapability,
                                                       'Resource Driver Lifecycle Execution Monitoring Service', 'bootstrap.resource_driver.lifecycle_monitoring_service_enabled')
            service_register.add_service(ServiceRegistration(LifecycleExecutionMonitoringService, job_queue_service=JobQueueCapability,
                                                             lifecycle_messaging_service=LifecycleMessagingCapability, handler=ResourceDriverHandlerCapability))
        else:
            logger.debug('Disabled: bootstrapped Resource Driver Lifecycle Monitoring Service')

    def __configure_messaging(self, configuration, service_register):
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        if auto_config.resource_driver.lifecycle_messaging_service_enabled is True:
            logger.debug('Bootstrapping Resource Driver Lifecycle Messaging Service')
            validate_no_service_with_capability_exists(service_register, LifecycleMessagingCapability, 'Resource Driver Lifecycle Messaging Service', 'bootstrap.resource_driver.lifecycle_messaging_service_enabled')
            messaging_config = configuration.property_groups.get_property_group(MessagingProperties)
            if messaging_config.connection_address is None:
                raise ValueError('messaging.connection_address must be set when bootstrap.resource_driver.lifecycle_messaging_service_enabled')
            if messaging_config.topics.lifecycle_execution_events is None:
                raise ValueError('messaging.topics.lifecycle_execution_events must be set when bootstrap.resource_driver.lifecycle_messaging_service_enabled')
            TopicCreator().create_topic_if_needed(messaging_config, messaging_config.topics.lifecycle_execution_events)
            service_register.add_service(ServiceRegistration(LifecycleMessagingService, postal_service=PostalCapability, topics_configuration=TopicsProperties))
        else:
            logger.debug('Disabled: bootstrapped Resource Driver Lifecycle Messaging Service')
