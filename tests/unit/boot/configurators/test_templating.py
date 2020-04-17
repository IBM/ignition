from .utils import ConfiguratorTestCase
from unittest.mock import MagicMock
from ignition.boot.config import BootstrapApplicationConfiguration, BootProperties
from ignition.boot.configurators.templating import TemplatingConfigurator
from ignition.service.framework import ServiceRegistration
from ignition.service.templating import Jinja2TemplatingService, ResourceTemplateContextService

class TestTemplatingConfigurator(ConfiguratorTestCase):

    def __bootstrap_config(self):
        configuration = BootstrapApplicationConfiguration()
        configuration.app_name = 'TestTemplatingConfigurator'
        boot_config = BootProperties()
        configuration.property_groups.add_property_group(boot_config)
        return configuration

    def test_configure_nothing_when_disabled(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).templating.service_enabled = False
        TemplatingConfigurator().configure(configuration, self.mock_service_register)
        self.mock_service_register.add_service.assert_not_called()

    def test_configure_service(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).templating.service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = None
        TemplatingConfigurator().configure(configuration, self.mock_service_register)
        registered_service = self.assert_single_service_registered()
        self.assert_service_registration_equal(registered_service, ServiceRegistration(Jinja2TemplatingService))

    def test_configure_service_fails_when_already_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).templating.service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            TemplatingConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'An existing service has been registered to serve the Templating capability but bootstrap.templating.service_enabled has not been disabled')

    def test_configure_resource_context_service(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).templating.resource_context_service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = None
        TemplatingConfigurator().configure(configuration, self.mock_service_register)
        registered_service = self.assert_single_service_registered()
        self.assert_service_registration_equal(registered_service, ServiceRegistration(ResourceTemplateContextService))

    def test_configure_resource_context_service_fails_when_already_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).templating.resource_context_service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            TemplatingConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'An existing service has been registered to serve the Resource Template Context capability but bootstrap.templating.resource_context_service_enabled has not been disabled')
