from .utils import ConfiguratorTestCase
from unittest.mock import MagicMock
from ignition.boot.config import BootstrapApplicationConfiguration, BootProperties
from ignition.boot.configurators.requestqueue import RequestQueueConfigurator
from ignition.service.messaging import MessagingProperties, DeliveryCapability, PostalCapability, KafkaDeliveryService, PostalService, KafkaInboxService, TopicConfigProperties
from ignition.service.framework import ServiceRegistration, ServiceRegister
from ignition.service.infrastructure import InfrastructureProperties, InfrastructureRequestQueueProperties
from ignition.service.lifecycle import LifecycleProperties, LifecycleScriptFileManagerCapability, LifecycleRequestQueueProperties
from ignition.service.requestqueue import InfrastructureConsumerFactoryCapability, LifecycleConsumerFactoryCapability, KafkaRequestQueueService

class TestRequestQueueConfigurator(ConfiguratorTestCase):

    def __bootstrap_config(self):
        configuration = BootstrapApplicationConfiguration()
        configuration.app_name = "TestApp"
        boot_config = BootProperties()
        configuration.property_groups.add_property_group(boot_config)
        messaging_conf = MessagingProperties()
        messaging_conf.connection_address = "kafka"
        configuration.property_groups.add_property_group(messaging_conf)

        infrastructure_conf = InfrastructureProperties()
        configuration.property_groups.add_property_group(infrastructure_conf)
        lifecycle_conf = LifecycleProperties()
        configuration.property_groups.add_property_group(lifecycle_conf)

        self.mock_topic_creator = MagicMock()

        return configuration

    def test_configure_nothing_when_disabled(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).request_queue.enabled = False
        RequestQueueConfigurator(self.mock_topic_creator).configure(configuration, self.mock_service_register)
        self.mock_service_register.add_service.assert_not_called()
        self.mock_topic_creator.create_topic_if_needed.assert_not_called()

    def test_configure_request_queue_service_with_real_service_register(self):
        service_register = ServiceRegister()
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).request_queue.enabled = True
        RequestQueueConfigurator(self.mock_topic_creator).configure(configuration, service_register)

    def test_configure_request_queue_service(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).request_queue.enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = None
        RequestQueueConfigurator(self.mock_topic_creator).configure(configuration, self.mock_service_register)
        registered_service = self.assert_services_registered(3)

        self.assert_service_registration_equal(registered_service[2], ServiceRegistration(KafkaRequestQueueService, messaging_config=MessagingProperties, infrastructure_config=InfrastructureProperties,
                lifecycle_config=LifecycleProperties, postal_service=PostalCapability, script_file_manager=LifecycleScriptFileManagerCapability,
                infrastructure_consumer_factory=InfrastructureConsumerFactoryCapability, lifecycle_consumer_factory=LifecycleConsumerFactoryCapability))

        self.mock_topic_creator.create_topic_if_needed.assert_called()
        service_calls = self.mock_topic_creator.create_topic_if_needed.call_args_list
        self.assertEqual(len(service_calls), 4)

        service_call = service_calls[0]
        service_call_args, kwargs = service_call
        self.assertEqual(len(service_call_args), 2)
        connection_address = service_call_args[0]
        self.assertEqual(connection_address, "kafka")
        topic_config_properties = service_call_args[1]
        self.assertIsInstance(topic_config_properties, TopicConfigProperties)

        service_call = service_calls[1]
        service_call_args, kwargs = service_call
        self.assertEqual(len(service_call_args), 2)
        connection_address = service_call_args[0]
        self.assertEqual(connection_address, "kafka")
        topic_config_properties = service_call_args[1]
        self.assertIsInstance(topic_config_properties, TopicConfigProperties)

        service_call = service_calls[2]
        service_call_args, kwargs = service_call
        self.assertEqual(len(service_call_args), 2)
        connection_address = service_call_args[0]
        self.assertEqual(connection_address, "kafka")
        topic_config_properties = service_call_args[1]
        self.assertIsInstance(topic_config_properties, TopicConfigProperties)

        service_call = service_calls[3]
        service_call_args, kwargs = service_call
        self.assertEqual(len(service_call_args), 2)
        connection_address = service_call_args[0]
        self.assertEqual(connection_address, "kafka")
        topic_config_properties = service_call_args[1]
        self.assertIsInstance(topic_config_properties, TopicConfigProperties)

    def test_configure_request_queue_service_fails_when_already_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).request_queue.enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            RequestQueueConfigurator(self.mock_topic_creator).configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'An existing service has been registered to serve the Request Queue capability but bootstrap.request_queue.enabled has not been disabled')
