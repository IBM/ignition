import logging
from ignition.service.framework import ServiceRegistration
from ignition.boot.config import BootProperties
from ignition.boot.configurators.utils import validate_no_service_with_capability_exists
from ignition.service.messaging import PostalCapability, InboxCapability, MessagingProperties, TopicsProperties, TopicCreator
from ignition.service.queue import JobQueueCapability, MessagingJobQueueService, JobQueueProperties


logger = logging.getLogger(__name__)


class JobQueueConfigurator():

    def __init__(self):
        pass

    def configure(self, configuration, service_register):
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        if auto_config.job_queue.service_enabled is True:
            logger.debug('Bootstrapping Job Queue Service')
            validate_no_service_with_capability_exists(service_register, JobQueueCapability, 'Job Queue', 'bootstrap.job_queue.service_enabled')
            messaging_config = configuration.property_groups.get_property_group(MessagingProperties)
            if messaging_config.connection_address is None:
                raise ValueError('messaging.connection_address must be set when bootstrap.job_queue.service_enabled is True')
            if messaging_config.topics.job_queue is None:
                raise ValueError('messaging.topics.job_queue must be set when bootstrap.job_queue.service_enabled is True')
            if messaging_config.topics.job_queue.name is None:
                # Job Queue topic should be unique per VIM/Lifecycle driver cluster (not per instance) so we default the value at runtime to include the app name
                messaging_config.topics.job_queue.name = '{0}_job_queue'.format(configuration.app_name.replace(" ", "_"))
            TopicCreator().create_topic_if_needed(messaging_config.connection_address, messaging_config.topics.job_queue)
            service_register.add_service(ServiceRegistration(MessagingJobQueueService, job_queue_config=JobQueueProperties, postal_service=PostalCapability, inbox_service=InboxCapability, topics_config=TopicsProperties, messaging_config=MessagingProperties))
        else:
            logger.debug('Disabled: bootstrapped Job Queue API')
