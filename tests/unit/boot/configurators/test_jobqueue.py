from .utils import ConfiguratorTestCase
from unittest.mock import MagicMock
from ignition.boot.config import BootstrapApplicationConfiguration, BootProperties
from ignition.boot.configurators.jobqueue import JobQueueConfigurator
from ignition.service.queue import JobQueueCapability, MessagingJobQueueService
from ignition.service.messaging import MessagingProperties, TopicsProperties, PostalCapability, InboxCapability
from ignition.service.framework import ServiceRegistration


class TestJobQueueConfigurator(ConfiguratorTestCase):

    def __bootstrap_config(self):
        configuration = BootstrapApplicationConfiguration()
        boot_config = BootProperties()
        configuration.property_groups.add_property_group(boot_config)
        messaging_conf = MessagingProperties()
        configuration.property_groups.add_property_group(messaging_conf)
        return configuration

    def test_configure_nothing_when_disabled(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).job_queue.service_enabled = False
        JobQueueConfigurator().configure(configuration, self.mock_service_register)
        self.mock_service_register.add_service.assert_not_called()

    def test_configure(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).job_queue.service_enabled = True
        configuration.property_groups.get_property_group(MessagingProperties).connection_address = 'testaddr'
        configuration.property_groups.get_property_group(MessagingProperties).topics.job_queue = 'job_queue_topic'
        self.mock_service_register.get_service_offering_capability.return_value = None
        JobQueueConfigurator().configure(configuration, self.mock_service_register)
        registered_service = self.assert_single_service_registered()
        self.assert_service_registration_equal(registered_service, ServiceRegistration(
            MessagingJobQueueService, postal_service=PostalCapability, inbox_service=InboxCapability, topics_config=TopicsProperties))

    def test_configure_service_fails_when_already_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).job_queue.service_enabled = True
        configuration.property_groups.get_property_group(MessagingProperties).connection_address = 'testaddr'
        configuration.property_groups.get_property_group(MessagingProperties).topics.job_queue = 'job_queue_topic'
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            JobQueueConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'An existing service has been registered to serve the Job Queue capability but bootstrap.job_queue.service_enabled has not been disabled')

    def test_configure_fails_when_messaging_connection_address_not_set(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).job_queue.service_enabled = True
        configuration.property_groups.get_property_group(MessagingProperties).connection_address = None
        configuration.property_groups.get_property_group(MessagingProperties).topics.job_queue = 'job_queue_topic'
        self.mock_service_register.get_service_offering_capability.return_value = None
        with self.assertRaises(ValueError) as context:
            JobQueueConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'messaging.connection_address must be set when bootstrap.job_queue.service_enabled is True')

    def test_configure_creates_job_queue_topic_name_when_not_set(self):
        configuration = self.__bootstrap_config()
        configuration.app_name = 'TestApp'
        configuration.property_groups.get_property_group(BootProperties).job_queue.service_enabled = True
        configuration.property_groups.get_property_group(MessagingProperties).connection_address = 'testaddr'
        configuration.property_groups.get_property_group(MessagingProperties).topics.job_queue = None
        self.mock_service_register.get_service_offering_capability.return_value = None
        JobQueueConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(configuration.property_groups.get_property_group(MessagingProperties).topics.job_queue, 'TestApp_job_queue')
