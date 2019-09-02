from unittest.mock import patch, MagicMock
from .utils import ConfiguratorTestCase
from ignition.boot.config import BootstrapApplicationConfiguration, BootProperties
from ignition.boot.configurators.infrastructureapi import InfrastructureApiConfigurator, InfrastructureServicesConfigurator
from ignition.service.infrastructure import InfrastructureProperties, InfrastructureApiCapability, InfrastructureServiceCapability, InfrastructureDriverCapability, InfrastructureTaskMonitoringCapability, InfrastructureMessagingCapability, InfrastructureApiService, InfrastructureService, InfrastructureTaskMonitoringService, InfrastructureMessagingService
from ignition.service.messaging import TopicsProperties, PostalCapability
from ignition.service.queue import JobQueueCapability
from ignition.service.framework import Service, ServiceRegistration


class TestInfrastructureApiConfigurator(ConfiguratorTestCase):

    def __bootstrap_config(self):
        configuration = BootstrapApplicationConfiguration()
        boot_config = BootProperties()
        configuration.property_groups.add_property_group(boot_config)
        infrastructure_config = InfrastructureProperties()
        configuration.property_groups.add_property_group(infrastructure_config)
        return configuration

    def test_configure_nothing_when_api_enabled_is_false(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).infrastructure.api_enabled = False
        InfrastructureApiConfigurator().configure(configuration, self.mock_service_register, self.mock_service_instances, self.mock_api_register)
        self.mock_service_register.add_service.assert_not_called()
        self.mock_api_register.register_api.assert_not_called()

    def test_configure_fails_when_api_spec_is_not_defined(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).infrastructure.api_enabled = True
        configuration.property_groups.get_property_group(InfrastructureProperties).api_spec = None
        with self.assertRaises(ValueError) as context:
            InfrastructureApiConfigurator().configure(configuration, self.mock_service_register, self.mock_service_instances, self.mock_api_register)
        self.assertEqual(str(context.exception), 'infrastructure.api_spec must be set when bootstrap.infrastructure.api_enabled is True')

    def test_configure_fails_when_api_service_not_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).infrastructure.api_enabled = True
        configuration.property_groups.get_property_group(BootProperties).infrastructure.api_enabled = True
        configuration.property_groups.get_property_group(InfrastructureProperties).api_spec = 'vim_infrastructure.yml'
        self.mock_service_register.get_service_offering_capability.return_value = None
        with self.assertRaises(ValueError) as context:
            InfrastructureApiConfigurator().configure(configuration, self.mock_service_register, self.mock_service_instances, self.mock_api_register)
        self.assertEqual(str(context.exception), 'No service has been registered with the InfrastructureApiCapability, did you forget to register one? Or try enabling bootstrap.infrastructure.api_service_enabled')

    def test_configure_fails_when_api_service_instance_not_available(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).infrastructure.api_enabled = True
        configuration.property_groups.get_property_group(InfrastructureProperties).api_spec = 'vim_infrastructure.yml'
        self.mock_service_register.get_service_offering_capability.return_value = InfrastructureApiService
        self.mock_service_instances.get_instance.return_value = None
        with self.assertRaises(ValueError) as context:
            InfrastructureApiConfigurator().configure(configuration, self.mock_service_register, self.mock_service_instances, self.mock_api_register)
        self.assertEqual(str(context.exception), 'No instance of the Infrastructure API service has been built')

    @patch('ignition.boot.configurators.infrastructureapi.build_resolver_to_instance')
    def test_configure_api(self, mock_build_resolver_to_instance):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).infrastructure.api_enabled = True
        configuration.property_groups.get_property_group(InfrastructureProperties).api_spec = 'vim_infrastructure.yml'
        self.mock_service_register.get_service_offering_capability.return_value = InfrastructureApiService
        mock_resolver = MagicMock()
        mock_build_resolver_to_instance.return_value = mock_resolver
        InfrastructureApiConfigurator().configure(configuration, self.mock_service_register, self.mock_service_instances, self.mock_api_register)
        self.mock_service_register.get_service_offering_capability.assert_called_once_with(InfrastructureApiCapability)
        self.mock_service_instances.get_instance.assert_called_once_with(InfrastructureApiService)
        mock_build_resolver_to_instance.assert_called_once_with(self.mock_service_instances.get_instance.return_value)
        self.mock_api_register.register_api.assert_called_once_with('vim_infrastructure.yml', resolver=mock_resolver)


class TestInfrastructureServicesConfigurator(ConfiguratorTestCase):

    def __bootstrap_config(self):
        configuration = BootstrapApplicationConfiguration()
        boot_config = BootProperties()
        configuration.property_groups.add_property_group(boot_config)
        infrastructure_config = InfrastructureProperties()
        configuration.property_groups.add_property_group(infrastructure_config)
        return configuration

    def test_configure_nothing_when_disabled(self):
        configuration = self.__bootstrap_config()
        boot_conf = configuration.property_groups.get_property_group(BootProperties)
        boot_conf.infrastructure.api_service_enabled = False
        boot_conf.infrastructure.service_enabled = False
        boot_conf.infrastructure.service_enabled = False
        boot_conf.infrastructure.monitoring_service_enabled = False
        boot_conf.infrastructure.messaging_service_enabled = False
        self.mock_service_register.add_service.assert_not_called()

    def test_configure_api_service(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).infrastructure.api_service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = None
        InfrastructureServicesConfigurator().configure(configuration, self.mock_service_register)
        registered_service = self.assert_single_service_registered()
        self.assert_service_registration_equal(registered_service, ServiceRegistration(InfrastructureApiService, service=InfrastructureServiceCapability))

    def test_configure_api_service_fails_when_already_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).infrastructure.api_service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            InfrastructureServicesConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'An existing service has been registered to serve the Infrastructure API capability but bootstrap.infrastructure.api_service_enabled has not been disabled')

    def test_configure_service(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).infrastructure.service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = None
        InfrastructureServicesConfigurator().configure(configuration, self.mock_service_register)
        service_registrations = self.assert_services_registered(1)
        self.assert_service_registration_equal(service_registrations[0], ServiceRegistration(InfrastructureService, driver=InfrastructureDriverCapability,
                                                                                             infrastructure_config=InfrastructureProperties, inf_monitor_service=InfrastructureTaskMonitoringCapability))

    def test_configure_service_does_not_include_monitoring_when_async_messaging_disabled(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).infrastructure.service_enabled = True
        configuration.property_groups.get_property_group(InfrastructureProperties).async_messaging_enabled = False
        self.mock_service_register.get_service_offering_capability.return_value = None
        InfrastructureServicesConfigurator().configure(configuration, self.mock_service_register)
        service_registrations = self.assert_services_registered(1)
        self.assert_service_registration_equal(service_registrations[0], ServiceRegistration(
            InfrastructureService, driver=InfrastructureDriverCapability, infrastructure_config=InfrastructureProperties))

    def test_configure_service_fails_when_already_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).infrastructure.service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            InfrastructureServicesConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'An existing service has been registered to serve the Infrastructure Service capability but bootstrap.infrastructure.service_enabled has not been disabled')

    def test_configure_monitoring(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).infrastructure.monitoring_service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = None
        InfrastructureServicesConfigurator().configure(configuration, self.mock_service_register)
        service_registrations = self.assert_services_registered(1)
        self.assert_service_registration_equal(service_registrations[0], ServiceRegistration(InfrastructureTaskMonitoringService,
                                                                                             job_queue_service=JobQueueCapability, inf_messaging_service=InfrastructureMessagingCapability, driver=InfrastructureDriverCapability))

    def test_configure_messaging(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).infrastructure.messaging_service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = None
        InfrastructureServicesConfigurator().configure(configuration, self.mock_service_register)
        registered_service = self.assert_single_service_registered()
        self.assert_service_registration_equal(registered_service, ServiceRegistration(InfrastructureMessagingService, postal_service=PostalCapability, topics_configuration=TopicsProperties))

    def test_configure_messaging_fails_when_already_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).infrastructure.messaging_service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            InfrastructureServicesConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'An existing service has been registered to serve the Infrastructure Messaging Service capability but bootstrap.infrastructure.messaging_service_enabled has not been disabled')
