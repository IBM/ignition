import logging
from ignition.boot.connexionutils import build_resolver_to_instance
from ignition.boot.config import BootProperties
from ignition.service.framework import ServiceRegistration
from ignition.service.messaging import PostalCapability, TopicsProperties, MessagingProperties, TopicCreator
from ignition.service.queue import JobQueueCapability
from ignition.service.infrastructure import InfrastructureProperties, InfrastructureApiCapability, InfrastructureServiceCapability, InfrastructureDriverCapability, InfrastructureTaskMonitoringCapability, InfrastructureMessagingCapability, InfrastructureApiService, InfrastructureService, InfrastructureTaskMonitoringService, InfrastructureMessagingService
from ignition.boot.configurators.utils import validate_no_service_with_capability_exists

logger = logging.getLogger(__name__)


class InfrastructureApiConfigurator():

    def __init__(self):
        pass

    def configure(self, configuration, service_register, service_instances, api_register):
        self.__configure_api_spec(configuration, service_register, service_instances, api_register)

    def __configure_api_spec(self, configuration, service_register, service_instances, api_register):
        infrastructure_config = configuration.property_groups.get_property_group(InfrastructureProperties)
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        if auto_config.infrastructure.api_enabled is True:
            logger.debug('Bootstrapping Infrastructure API')
            api_spec = infrastructure_config.api_spec
            if api_spec is None:
                raise ValueError('infrastructure.api_spec must be set when bootstrap.infrastructure.api_enabled is True')
            api_service_class = service_register.get_service_offering_capability(InfrastructureApiCapability)
            if api_service_class is None:
                raise ValueError('No service has been registered with the InfrastructureApiCapability, did you forget to register one? Or try enabling bootstrap.infrastructure.api_service_enabled')
            api_service_instance = service_instances.get_instance(api_service_class)
            if api_service_instance is None:
                raise ValueError('No instance of the Infrastructure API service has been built')
            api_register.register_api(api_spec, resolver=build_resolver_to_instance(api_service_instance))
        else:
            logger.debug('Disabled: bootstrapped Infrastructure API')


class InfrastructureServicesConfigurator():

    def configure(self, configuration, service_register):
        self.__configure_api_service(configuration, service_register)
        self.__configure_service(configuration, service_register)
        self.__configure_monitoring(configuration, service_register)
        self.__configure_messaging(configuration, service_register)

    def __configure_api_service(self, configuration, service_register):
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        if auto_config.infrastructure.api_service_enabled is True:
            logger.debug('Bootstrapping Infrastructure API Service')
            # Check if a user has enabled the auto configuration of the Infrastructure API service but has also added their own
            validate_no_service_with_capability_exists(service_register, InfrastructureApiCapability, 'Infrastructure API', 'bootstrap.infrastructure.api_service_enabled')
            service_register.add_service(ServiceRegistration(InfrastructureApiService, service=InfrastructureServiceCapability))
        else:
            logger.debug('Disabled: bootstrapped Infrastructure API Service')

    def __configure_service(self, configuration, service_register):
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        if auto_config.infrastructure.service_enabled is True:
            logger.debug('Bootstrapping Infrastructure Service')
            # Check if a user has enabled the auto configuration of the Infrastructure service but has also added their own
            validate_no_service_with_capability_exists(service_register, InfrastructureServiceCapability, 'Infrastructure Service', 'bootstrap.infrastructure.service_enabled')
            required_capabilities = {
                'driver': InfrastructureDriverCapability,
                'infrastructure_config': InfrastructureProperties
            }
            infrastructure_config = configuration.property_groups.get_property_group(InfrastructureProperties)
            if infrastructure_config.async_messaging_enabled is True:
                required_capabilities['inf_monitor_service'] = InfrastructureTaskMonitoringCapability
            service_register.add_service(ServiceRegistration(InfrastructureService, **required_capabilities))
        else:
            logger.debug('Disabled: bootstrapped Infrastructure Service')

    def __configure_monitoring(self, configuration, service_register):
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        if auto_config.infrastructure.monitoring_service_enabled is True:
            logger.debug('Bootstrapping Infrastructure Monitoring Service')
            validate_no_service_with_capability_exists(service_register, InfrastructureTaskMonitoringCapability,
                                                       'Infrastructure Task Monitoring Service', 'bootstrap.infrastructure.monitoring_service_enabled')
            service_register.add_service(ServiceRegistration(InfrastructureTaskMonitoringService, job_queue_service=JobQueueCapability,
                                                             inf_messaging_service=InfrastructureMessagingCapability, driver=InfrastructureDriverCapability))
        else:
            logger.debug('Disabled: bootstrapped Infrastructure Monitoring Service')

    def __configure_messaging(self, configuration, service_register):
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        if auto_config.infrastructure.messaging_service_enabled is True:
            logger.debug('Bootstrapping Infrastructure Messaging Service')
            validate_no_service_with_capability_exists(service_register, InfrastructureMessagingCapability, 'Infrastructure Messaging Service', 'bootstrap.infrastructure.messaging_service_enabled')
            messaging_config = configuration.property_groups.get_property_group(MessagingProperties)
            if messaging_config.connection_address is None:
                raise ValueError('messaging.connection_address must be set when bootstrap.infrastructure.messaging_service_enabled')
            if messaging_config.topics.infrastructure_task_events is None:
                raise ValueError('messaging.topics.infrastructure_task_events must be set when bootstrap.infrastructure.messaging_service_enabled')
            TopicCreator().create_topic_if_needed(messaging_config.connection_address, messaging_config.topics.infrastructure_task_events)
            service_register.add_service(ServiceRegistration(InfrastructureMessagingService, postal_service=PostalCapability, topics_configuration=TopicsProperties))
        else:
            logger.debug('Disabled: bootstrapped Infrastructure Messaging Service')
