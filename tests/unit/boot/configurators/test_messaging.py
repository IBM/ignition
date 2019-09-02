from .utils import ConfiguratorTestCase
from unittest.mock import MagicMock
from ignition.boot.config import BootstrapApplicationConfiguration, BootProperties
from ignition.boot.configurators.messaging import MessagingConfigurator
from ignition.service.messaging import MessagingProperties, DeliveryCapability, PostalCapability, KafkaDeliveryService, PostalService, KafkaInboxService
from ignition.service.framework import ServiceRegistration


class TestMessagingConfigurator(ConfiguratorTestCase):

    def __bootstrap_config(self):
        configuration = BootstrapApplicationConfiguration()
        boot_config = BootProperties()
        configuration.property_groups.add_property_group(boot_config)
        messaging_conf = MessagingProperties()
        configuration.property_groups.add_property_group(messaging_conf)
        return configuration

    def test_configure_nothing_when_disabled(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).messaging.postal_enabled = False
        configuration.property_groups.get_property_group(BootProperties).messaging.delivery_enabled = False
        configuration.property_groups.get_property_group(BootProperties).messaging.inbox_enabled = False
        MessagingConfigurator().configure(configuration, self.mock_service_register)
        self.mock_service_register.add_service.assert_not_called()

    def test_configure_postal(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).messaging.postal_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = None
        MessagingConfigurator().configure(configuration, self.mock_service_register)
        registered_service = self.assert_single_service_registered()
        self.assert_service_registration_equal(registered_service, ServiceRegistration(PostalService, delivery_service=DeliveryCapability))

    def test_configure_postal_fails_when_already_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).messaging.postal_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            MessagingConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'An existing service has been registered to serve the Postal Service capability but bootstrap.messaging.postal_enabled has not been disabled')

    def test_configure_delivery(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).messaging.delivery_enabled = True
        configuration.property_groups.get_property_group(MessagingProperties).connection_address = 'testaddr'
        self.mock_service_register.get_service_offering_capability.return_value = None
        MessagingConfigurator().configure(configuration, self.mock_service_register)
        registered_service = self.assert_single_service_registered()
        self.assert_service_registration_equal(registered_service, ServiceRegistration(KafkaDeliveryService, messaging_config=MessagingProperties))

    def test_configure_delivery_fails_when_already_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).messaging.delivery_enabled = True
        configuration.property_groups.get_property_group(MessagingProperties).connection_address = 'testaddr'
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            MessagingConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'An existing service has been registered to serve the Delivery Service capability but bootstrap.messaging.delivery_enabled has not been disabled')

    def test_configure_delivery_fails_when_messaging_connection_address_not_set(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).messaging.delivery_enabled = True
        configuration.property_groups.get_property_group(MessagingProperties).connection_address = None
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            MessagingConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'messaging.connection_address must be set when bootstrap.messaging.delivery_enabled is True')

    def test_configure_inbox(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).messaging.inbox_enabled = True
        configuration.property_groups.get_property_group(MessagingProperties).connection_address = 'testaddr'
        self.mock_service_register.get_service_offering_capability.return_value = None
        MessagingConfigurator().configure(configuration, self.mock_service_register)
        registered_service = self.assert_single_service_registered()
        self.assert_service_registration_equal(registered_service, ServiceRegistration(KafkaInboxService, messaging_config=MessagingProperties))

    def test_configure_inbox_fails_when_already_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).messaging.inbox_enabled = True
        configuration.property_groups.get_property_group(MessagingProperties).connection_address = 'testaddr'
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            MessagingConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'An existing service has been registered to serve the Inbox Service capability but bootstrap.messaging.inbox_enabled has not been disabled')

    def test_configure_inbox_fails_when_messaging_connection_address_not_set(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).messaging.inbox_enabled = True
        configuration.property_groups.get_property_group(MessagingProperties).connection_address = None
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            MessagingConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'messaging.connection_address must be set when bootstrap.messaging.inbox_enabled is True')
