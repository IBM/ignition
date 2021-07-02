import logging
import re
from ignition.service.framework import ServiceRegistration
from ignition.boot.config import BootProperties
from ignition.boot.configurators.utils import validate_no_service_with_capability_exists
from ignition.service.messaging import PostalCapability, InboxCapability, MessagingProperties, TopicsProperties, TopicCreator
from ignition.service.queue import JobQueueCapability, MessagingJobQueueService, JobQueueProperties
from ignition.service.resourcedriver import ResourceDriverServiceCapability, DriverFilesManagerCapability, ResourceDriverProperties, LifecycleMessagingCapability
from ignition.service.requestqueue import LifecycleRequestQueueCapability, KafkaLifecycleRequestQueueService, LifecycleConsumerFactoryCapability, KafkaLifecycleConsumerFactory

logger = logging.getLogger(__name__)

LIFECYCLE_REQUEST_QUEUE_TOPIC = "{0}_lifecycle_request_queue"
FAILED_REQUEST_QUEUE = "{0}_failed"


class RequestQueueConfigurator():

    def __init__(self, topic_creator):
        self.topic_creator = topic_creator

    def configure(self, configuration, service_register):
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        if auto_config.request_queue.enabled is True:
            logger.debug('Bootstrapping Request Queue Service')

            messaging_config = configuration.property_groups.get_property_group(MessagingProperties)
            resource_driver_config = configuration.property_groups.get_property_group(ResourceDriverProperties)
            self.configure_topics(configuration, messaging_config, resource_driver_config.lifecycle_request_queue)

            if auto_config.resource_driver.api_enabled is True:
                validate_no_service_with_capability_exists(service_register, LifecycleRequestQueueCapability, 'Lifecycle Request Queue', 'bootstrap.request_queue.enabled')
                service_register.add_service(ServiceRegistration(KafkaLifecycleConsumerFactory, resource_driver_config.lifecycle_request_queue, messaging_properties=MessagingProperties))
                service_register.add_service(ServiceRegistration(KafkaLifecycleRequestQueueService, lifecycle_messaging_service=LifecycleMessagingCapability, messaging_properties=MessagingProperties, resource_driver_config=ResourceDriverProperties,
                    postal_service=PostalCapability, driver_files_manager=DriverFilesManagerCapability, lifecycle_consumer_factory=LifecycleConsumerFactoryCapability))
        else:
            logger.debug('Disabled: bootstrapped Request Queue Service')


    def configure_topics(self, configuration, messaging_config, lifecycle_request_queue_config):
        safe_topic_name = re.sub('[^A-Za-z0-9-_ ]+', '', configuration.app_name)
        # Remove any concurrent spaces
        safe_topic_name = ' '.join(safe_topic_name.split())
        # Replace spaces with underscore
        safe_topic_name = safe_topic_name.replace(' ', '_')

        if lifecycle_request_queue_config.topic.name is None:
            lifecycle_request_queue_config.topic.name = LIFECYCLE_REQUEST_QUEUE_TOPIC.format(safe_topic_name)
            lifecycle_request_queue_config.failed_topic.name = FAILED_REQUEST_QUEUE.format(lifecycle_request_queue_config.topic.name)

        self.topic_creator.create_topic_if_needed(messaging_config, lifecycle_request_queue_config.topic)
        self.topic_creator.create_topic_if_needed(messaging_config, lifecycle_request_queue_config.failed_topic)
