from .utils import ConfiguratorTestCase
from unittest.mock import MagicMock
from ignition.boot.config import BootstrapApplicationConfiguration, BootProperties
from ignition.boot.configurators.progress_events import ProgressEventLogConfigurator
from ignition.service.framework import ServiceRegistration
from ignition.service.progress_events import ProgressEventLogWriterService, YAMLProgressEventLogSerializer, ProgressEventLogSerializerCapability

class TestProgressEventLogConfigurator(ConfiguratorTestCase):

    def __bootstrap_config(self):
        configuration = BootstrapApplicationConfiguration()
        configuration.app_name = 'TestProgressEventLogConfigurator'
        boot_config = BootProperties()
        configuration.property_groups.add_property_group(boot_config)
        return configuration

    def test_configure_nothing_when_disabled(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).progress_event_log.service_enabled = False
        ProgressEventLogConfigurator().configure(configuration, self.mock_service_register)
        self.mock_service_register.add_service.assert_not_called()

    def test_configure_service(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).progress_event_log.service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = None
        ProgressEventLogConfigurator().configure(configuration, self.mock_service_register)
        registered_service = self.assert_single_service_registered()
        self.assert_service_registration_equal(registered_service, ServiceRegistration(ProgressEventLogWriterService, serializer_service=ProgressEventLogSerializerCapability))

    def test_configure_service_fails_when_already_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).progress_event_log.service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            ProgressEventLogConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'An existing service has been registered to serve the ProgressEventLogWriter capability but bootstrap.progress_event_log.service_enabled has not been disabled')

    def test_configure_serializer_service(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).progress_event_log.serializer_service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = None
        ProgressEventLogConfigurator().configure(configuration, self.mock_service_register)
        registered_service = self.assert_single_service_registered()
        self.assert_service_registration_equal(registered_service, ServiceRegistration(YAMLProgressEventLogSerializer))

    def test_configure_serializer_service_fails_when_already_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).progress_event_log.serializer_service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            ProgressEventLogConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'An existing service has been registered to serve the ProgressEventLogSerializer capability but bootstrap.progress_event_log.serializer_service_enabled has not been disabled')
