from .utils import ConfiguratorTestCase
from unittest.mock import MagicMock, patch
from ignition.boot.config import BootstrapApplicationConfiguration, BootProperties
from ignition.boot.configurators.management import ManagementApiConfigurator, ManagmentServicesConfigurator
from ignition.service.management import ManagementProperties, ManagementApi, ManagementApiService, Management, ManagementService
from ignition.service.framework import ServiceRegistration
from ignition.service.health import HealthChecker, HealthCheckerService

class TestManagementApiConfigurator(ConfiguratorTestCase):

    def __bootstrap_config(self):
        configuration = BootstrapApplicationConfiguration()
        boot_config = BootProperties()
        configuration.property_groups.add_property_group(boot_config)
        management_config = ManagementProperties()
        configuration.property_groups.add_property_group(management_config)
        return configuration

    def test_configure_nothing_when_api_enabled_is_false(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).management.api_enabled = False
        ManagementApiConfigurator().configure(configuration, self.mock_service_register, self.mock_service_instances, self.mock_api_register)
        self.mock_service_register.add_service.assert_not_called()
        self.mock_api_register.register_api.assert_not_called()

    def test_configure_fails_when_api_spec_is_not_defined(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).management.api_enabled = True
        configuration.property_groups.get_property_group(ManagementProperties).api_spec = None
        with self.assertRaises(ValueError) as context:
            ManagementApiConfigurator().configure(configuration, self.mock_service_register, self.mock_service_instances, self.mock_api_register)
        self.assertEqual(str(context.exception), 'management.api_spec must be set when bootstrap.management.api_enabled is True')

    def test_configure_fails_when_api_service_not_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).management.api_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = None
        with self.assertRaises(ValueError) as context:
            ManagementApiConfigurator().configure(configuration, self.mock_service_register, self.mock_service_instances, self.mock_api_register)
        self.assertEqual(str(context.exception), 'No service has been registered with the Management API (ManagementApi) capability, did you forget to register one? Or try enabling bootstrap.management.api_service_enabled')

    def test_configure_fails_when_api_service_instance_not_available(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).management.api_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = ManagementApiService
        self.mock_service_instances.get_instance.return_value = None
        with self.assertRaises(ValueError) as context:
            ManagementApiConfigurator().configure(configuration, self.mock_service_register, self.mock_service_instances, self.mock_api_register)
        self.assertEqual(str(context.exception), 'No instance of the ManagementApi service has been built')

    @patch('ignition.boot.configurators.management.build_resolver_to_instance')
    def test_configure_api(self, mock_build_resolver_to_instance):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).management.api_enabled = True
        configuration.property_groups.get_property_group(ManagementProperties).api_spec = 'management.yaml'
        self.mock_service_register.get_service_offering_capability.return_value = ManagementApiService
        mock_resolver = MagicMock()
        mock_build_resolver_to_instance.return_value = mock_resolver
        ManagementApiConfigurator().configure(configuration, self.mock_service_register, self.mock_service_instances, self.mock_api_register)
        self.mock_service_register.get_service_offering_capability.assert_called_once_with(ManagementApi)
        self.mock_service_instances.get_instance.assert_called_once_with(ManagementApiService)
        mock_build_resolver_to_instance.assert_called_once_with(self.mock_service_instances.get_instance.return_value)
        self.mock_api_register.register_api.assert_called_once_with('management.yaml', resolver=mock_resolver)

class TestManagmentServicesConfigurator(ConfiguratorTestCase):

    def __bootstrap_config(self):
        configuration = BootstrapApplicationConfiguration()
        boot_config = BootProperties()
        boot_config.management.api_service_enabled = False
        boot_config.management.service_enabled = False
        boot_config.management.health.service_enabled = False
        configuration.property_groups.add_property_group(boot_config)
        management_config = ManagementProperties()
        configuration.property_groups.add_property_group(management_config)
        return configuration
    
    def test_configure_nothing_when_disabled(self):
        configuration = self.__bootstrap_config()
        boot_conf = configuration.property_groups.get_property_group(BootProperties)
        boot_conf.management.api_service_enabled = False
        boot_conf.management.service_enabled = False
        boot_conf.management.health.service_enabled = False
        ManagmentServicesConfigurator().configure(configuration, self.mock_service_register)
        self.mock_service_register.add_service.assert_not_called()

    def test_configure_api_service(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).management.api_service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = None
        ManagmentServicesConfigurator().configure(configuration, self.mock_service_register)
        registered_service = self.assert_single_service_registered()
        self.assert_service_registration_equal(registered_service, ServiceRegistration(ManagementApiService, service=Management))

    def test_configure_api_service_fails_when_already_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).management.api_service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            ManagmentServicesConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'An existing service has been registered to serve the Management API (ManagementApi) capability but bootstrap.management.api_service_enabled has not been disabled')

    def test_configure_service(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).management.service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = None
        ManagmentServicesConfigurator().configure(configuration, self.mock_service_register)
        service_registrations = self.assert_services_registered(1)
        self.assert_service_registration_equal(service_registrations[0], ServiceRegistration(ManagementService, health_checker=HealthChecker))

    def test_configure_service_fails_when_already_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).management.service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            ManagmentServicesConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'An existing service has been registered to serve the Management capability but bootstrap.management.service_enabled has not been disabled')

    def test_configure_health_service(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).management.health.service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = None
        ManagmentServicesConfigurator().configure(configuration, self.mock_service_register)
        service_registrations = self.assert_services_registered(1)
        self.assert_service_registration_equal(service_registrations[0], ServiceRegistration(HealthCheckerService))

    def test_configure_health_service_fails_when_already_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).management.health.service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            ManagmentServicesConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'An existing service has been registered to serve the HealthChecker capability but bootstrap.management.health.service_enabled has not been disabled')
