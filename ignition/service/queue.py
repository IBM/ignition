from ignition.service.framework import Capability, Service, interface
from ignition.service.messaging import Message, Envelope, JsonContent, TopicCreator
from ignition.service.config import ConfigurationPropertiesGroup
import logging

logger = logging.getLogger(__name__)

############################
# Config
############################

class JobQueueProperties(ConfigurationPropertiesGroup, Service, Capability):
    """
    Configuration related to job queue

    Attributes:
    - consumer_group_id:
            the ID of the consumer group to join on the job queue topic
                (required: when job_queue.service_enabled is enabled)
    """
    def __init__(self):
        super().__init__('job_queue')
        self.consumer_group_id = 'job_queue_consumer'

class JobQueueCapability(Capability):
    
    @interface
    def queue_job(self, job):
        pass
    
    @interface
    def register_job_handler(self, job_type, handler_func):
        pass

class MessagingJobQueueService(Service, JobQueueCapability):

    JOB_TYPE_KEY = 'job_type'

    def __init__(self, **kwargs):
        if 'job_queue_config' not in kwargs:
            raise ValueError('job_queue_config argument not provided')
        self.job_queue_config = kwargs.get('job_queue_config')
        if 'postal_service' not in kwargs:
            raise ValueError('postal_service argument not provided')
        self.postal_service = kwargs.get('postal_service')
        if 'inbox_service' not in kwargs:
            raise ValueError('inbox_service argument not provided')
        self.inbox_service = kwargs.get('inbox_service')
        if 'topics_config' not in kwargs:
            raise ValueError('topics_config argument not provided')
        topics_config = kwargs.get('topics_config')
        if topics_config is None:
            raise ValueError('topics_config must be set')
        if topics_config.job_queue is None:
            raise ValueError('topics_config.job_queue must be set')
        self.job_queue_topic = topics_config.job_queue
        self.messaging_config = kwargs.get('messaging_config')
        if self.messaging_config is None:
            raise ValueError('messaging_config argument not provided')
        self.job_handlers = {}
        self.__init_watch_for_jobs()


    def __init_watch_for_jobs(self):
        self.inbox_service.watch_inbox(self.job_queue_config.consumer_group_id, self.job_queue_topic.name, self.__received_next_job_handler)

    def __received_next_job_handler(self, job_definition_str):
        job_definition = JsonContent.read(job_definition_str).dict_val
        if self.JOB_TYPE_KEY not in job_definition:
            logger.warning('Job received from queue without job_type: {0}'.format(job_definition_str))
            return None
        job_type = job_definition[self.JOB_TYPE_KEY]
        if job_type not in self.job_handlers:
            logger.warning('No handler for job received from queue with job_type {0}'.format(job_type))
            self.queue_job(job_definition)
            return None
        job_handler = self.job_handlers[job_type]
        finished = job_handler(job_definition)
        if finished is not True:
            self.queue_job(job_definition)

    def queue_job(self, job_definition):
        logger.debug('Adding job to queue: {0}'.format(job_definition))
        if self.JOB_TYPE_KEY not in job_definition:
            raise ValueError('job_definition must have a job_type key')
        if job_definition[self.JOB_TYPE_KEY] is None:
            raise ValueError('job_definition must have a job_type value (not None)')
        msg_content = JsonContent(job_definition).get()
        msg = Message(msg_content)
        self.postal_service.post(Envelope(self.job_queue_topic.name, msg))
    
    def register_job_handler(self, job_type, handler_func):
        if job_type in self.job_handlers:
            raise ValueError('Handler for job_type \'{0}\' has already been registered'.format(job_type))
        if not callable(handler_func):
            raise ValueError('handler_func argument must be a callable function')
        self.job_handlers[job_type] = handler_func