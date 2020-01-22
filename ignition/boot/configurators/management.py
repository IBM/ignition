import logging
from ignition.boot.connexionutils import build_resolver_to_instance
from ignition.boot.config import BootProperties
from ignition.service.management import ManagementApi, Management, ManagementProperties, ManagementApiService, ManagementService
from ignition.service.health import HealthChecker, HealthCheckerService
from ignition.boot.configurators.utils import validate_no_service_with_capability_exists
from ignition.service.framework import ServiceRegistration

logger = logging.getLogger(__name__)


class ManagementApiConfigurator():

    def __init__(self):
        pass

    def configure(self, configuration, service_register, service_instances, api_register):
        self.__configure_api_spec(configuration, service_register, service_instances, api_register)

    def __configure_api_spec(self, configuration, service_register, service_instances, api_register):
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        mgmt_config = configuration.property_groups.get_property_group(ManagementProperties)
        if auto_config.management.api_enabled is True:
            logger.debug('Bootstrapping Management API')
            api_spec = mgmt_config.api_spec
            if api_spec is None:
                raise ValueError('management.api_spec must be set when bootstrap.management.api_enabled is True')
            api_service_class = service_register.get_service_offering_capability(ManagementApi)
            if api_service_class is None:
                raise ValueError('No service has been registered with the Management API (ManagementApi) capability, did you forget to register one? Or try enabling bootstrap.management.api_service_enabled')
            api_service_instance = service_instances.get_instance(api_service_class)
            if api_service_instance is None:
                raise ValueError('No instance of the ManagementApi service has been built')
            api_register.register_api(api_spec, resolver=build_resolver_to_instance(api_service_instance))
        else:
            logger.debug('Disabled: bootstrapped Management API')

class ManagmentServicesConfigurator():

    def configure(self, configuration, service_register):
        self.__configure_api_service(configuration, service_register)
        self.__configure_service(configuration, service_register)
        self.__configure_health_service(configuration, service_register)

    def __configure_api_service(self, configuration, service_register):
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        if auto_config.management.api_service_enabled is True:
            logger.debug('Bootstrapping Management API Service')
            # Check if a user has enabled the auto configuration of the Management API service but has also added their own
            validate_no_service_with_capability_exists(service_register, ManagementApi, 'Management API (ManagementApi)', 'bootstrap.management.api_service_enabled')
            service_register.add_service(ServiceRegistration(ManagementApiService, service=Management))
        else:
            logger.debug('Disabled: bootstrapped Management API Service')

    def __configure_service(self, configuration, service_register):
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        if auto_config.management.service_enabled is True:
            logger.debug('Bootstrapping Management Service')
            # Check if a user has enabled the auto configuration of the Management service but has also added their own
            validate_no_service_with_capability_exists(service_register, Management, 'Management', 'bootstrap.management.service_enabled')
            required_capabilities = {
                'health_checker': HealthChecker
            }
            service_register.add_service(ServiceRegistration(ManagementService, **required_capabilities))
        else:
            logger.debug('Disabled: bootstrapped Management Service')

    def __configure_health_service(self, configuration, service_register):
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        if auto_config.management.health.service_enabled is True:
            logger.debug('Bootstrapping Health Checker Service')
            # Check if a user has enabled the auto configuration of the HealthChecker service but has also added their own
            validate_no_service_with_capability_exists(service_register, HealthChecker, 'HealthChecker', 'bootstrap.management.health.service_enabled')
            service_register.add_service(ServiceRegistration(HealthCheckerService))
        else:
            logger.debug('Disabled: bootstrapped Health Checker Service')
