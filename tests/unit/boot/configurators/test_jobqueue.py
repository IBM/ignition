from .utils import ConfiguratorTestCase
from unittest.mock import MagicMock, patch
from ignition.boot.config import BootstrapApplicationConfiguration, BootProperties
from ignition.boot.configurators.jobqueue import JobQueueConfigurator
from ignition.service.queue import JobQueueCapability, MessagingJobQueueService, JobQueueProperties
from ignition.service.messaging import MessagingProperties, TopicsProperties, PostalCapability, InboxCapability
from ignition.service.framework import ServiceRegistration


class TestJobQueueConfigurator(ConfiguratorTestCase):

    def __bootstrap_config(self):
        configuration = BootstrapApplicationConfiguration()
        configuration.app_name = 'TestJobQueueConfigurator'
        boot_config = BootProperties()
        configuration.property_groups.add_property_group(boot_config)
        messaging_conf = MessagingProperties()
        messaging_conf.connection_address = 'testaddr'
        configuration.property_groups.add_property_group(messaging_conf)
        job_queue_conf = JobQueueProperties()
        configuration.property_groups.add_property_group(job_queue_conf)
        return configuration

    def test_configure_nothing_when_disabled(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).job_queue.service_enabled = False
        JobQueueConfigurator().configure(configuration, self.mock_service_register)
        self.mock_service_register.add_service.assert_not_called()

    @patch('ignition.boot.configurators.jobqueue.TopicCreator')
    def test_configure(self, mock_topic_creator_init):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).job_queue.service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = None
        JobQueueConfigurator().configure(configuration, self.mock_service_register)
        registered_service = self.assert_single_service_registered()
        self.assert_service_registration_equal(registered_service, ServiceRegistration(
            MessagingJobQueueService, job_queue_config=JobQueueProperties, postal_service=PostalCapability, inbox_service=InboxCapability, topics_config=TopicsProperties, messaging_config=MessagingProperties))

    def test_configure_service_fails_when_already_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).job_queue.service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            JobQueueConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'An existing service has been registered to serve the Job Queue capability but bootstrap.job_queue.service_enabled has not been disabled')

    def test_configure_fails_when_messaging_connection_address_not_set(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).job_queue.service_enabled = True
        configuration.property_groups.get_property_group(MessagingProperties).connection_address = None
        self.mock_service_register.get_service_offering_capability.return_value = None
        with self.assertRaises(ValueError) as context:
            JobQueueConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'messaging.connection_address must be set when bootstrap.job_queue.service_enabled is True')

    @patch('ignition.boot.configurators.jobqueue.TopicCreator')
    def test_configure_creates_job_queue_topic_name_when_not_set(self, mock_topic_creator_init):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).job_queue.service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = None
        JobQueueConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(configuration.property_groups.get_property_group(MessagingProperties).topics.job_queue.name, 'TestJobQueueConfigurator_job_queue')

    @patch('ignition.boot.configurators.jobqueue.TopicCreator')
    def test_configure_creates_job_queue_topic_with_special_chars_removed(self, mock_topic_creator_init):
        configuration = self.__bootstrap_config()
        configuration.app_name = 'Testing Spaces And Special !"£$%^&*()+={}[]:;@~#<>?,./¬  Chars'
        configuration.property_groups.get_property_group(BootProperties).job_queue.service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = None
        JobQueueConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(configuration.property_groups.get_property_group(MessagingProperties).topics.job_queue.name, 'Testing_Spaces_And_Special_Chars_job_queue')

    @patch('ignition.boot.configurators.jobqueue.TopicCreator')
    def test_configure_creates_job_queue_topic_if_needed(self, mock_topic_creator_init):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).job_queue.service_enabled = True
        configuration.property_groups.get_property_group(MessagingProperties).topics.job_queue.auto_create = True
        self.mock_service_register.get_service_offering_capability.return_value = None
        JobQueueConfigurator().configure(configuration, self.mock_service_register)
        mock_topic_creator_init.assert_called_once()
        messaging_properties = MessagingProperties()
        messaging_properties.connection_address = 'testaddr'
        mock_topic_creator_init.return_value.create_topic_if_needed.assert_called_once_with(messaging_properties, configuration.property_groups.get_property_group(MessagingProperties).topics.job_queue)

