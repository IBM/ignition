import logging
import re
from ignition.service.framework import ServiceRegistration
from ignition.boot.config import BootProperties
from ignition.boot.configurators.utils import validate_no_service_with_capability_exists
from ignition.service.messaging import PostalCapability, InboxCapability, MessagingProperties, TopicsProperties, TopicCreator
from ignition.service.queue import JobQueueCapability, MessagingJobQueueService, JobQueueProperties
from ignition.service.infrastructure import InfrastructureServiceCapability, InfrastructureProperties
from ignition.service.lifecycle import LifecycleServiceCapability, LifecycleScriptFileManagerCapability, LifecycleProperties
from ignition.service.requestqueue import KafkaRequestQueueService, RequestQueueCapability

logger = logging.getLogger(__name__)

class RequestQueueConfigurator():

    def __init__(self):
        pass

    def configure(self, configuration, service_register):
        logger.debug('Bootstrapping Infrastructure Request Queue Service')

        messaging_config = configuration.property_groups.get_property_group(MessagingProperties)
        infrastructure_config = configuration.property_groups.get_property_group(InfrastructureProperties)
        lifecycle_config = configuration.property_groups.get_property_group(LifecycleProperties)

        validate_no_service_with_capability_exists(service_register, RequestQueueCapability, 'Request Queue', None)
        self.configure_topics(configuration, messaging_config, infrastructure_config.request_queue, lifecycle_config.request_queue)

        service_register.add_service(ServiceRegistration(KafkaRequestQueueService, messaging_config=MessagingProperties, infrastructure_config=InfrastructureProperties,
            lifecycle_config=LifecycleProperties, postal_service=PostalCapability, script_file_manager=LifecycleScriptFileManagerCapability))

    def configure_topics(self, configuration, messaging_config, infrastructure_request_queue_config, lifecycle_request_queue_config):
        safe_topic_name = re.sub('[^A-Za-z0-9-_ ]+', '', configuration.app_name)
        # Remove any concurrent spaces
        safe_topic_name = ' '.join(safe_topic_name.split())
        # Replace spaces with underscore
        safe_topic_name = safe_topic_name.replace(' ', '_')

        if infrastructure_request_queue_config.topic.name is None:
            infrastructure_request_queue_config.topic.name = '{0}_infrastructure_request_queue'.format(safe_topic_name)
        if lifecycle_request_queue_config.topic.name is None:
            lifecycle_request_queue_config.topic.name = '{0}_lifecycle_request_queue'.format(safe_topic_name)

        TopicCreator().create_topic_if_needed(messaging_config.connection_address, infrastructure_request_queue_config.topic)
        TopicCreator().create_topic_if_needed(messaging_config.connection_address, lifecycle_request_queue_config.topic)
