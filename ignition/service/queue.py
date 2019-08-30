from ignition.service.framework import Capability, Service, interface
from ignition.service.messaging import Message, Envelope, JsonContent
import logging

logger = logging.getLogger(__name__)

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
        if 'postal_service' not in kwargs:
            raise ValueError('postal_service argument not provided')
        self.postal_service = kwargs.get('postal_service')
        if 'inbox_service' not in kwargs:
            raise ValueError('inbox_service argument not provided')
        self.inbox_service = kwargs.get('inbox_service')
        if 'topics_config' not in kwargs:
            raise ValueError('topics_config argument not provided')
        self.job_queue_topic = kwargs.get('topics_config').job_queue
        if self.job_queue_topic is None:
            raise ValueError('job_queue topic must be set')
        self.job_handlers = {}
        self.__init_watch_for_jobs()
        
    def __init_watch_for_jobs(self):
        self.inbox_service.watch_inbox(self.job_queue_topic, self.__received_next_job_handler)

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
        self.postal_service.post(Envelope(self.job_queue_topic, msg))
    
    def register_job_handler(self, job_type, handler_func):
        if job_type in self.job_handlers:
            raise ValueError('Handler for job_type \'{0}\' has already been registered'.format(job_type))
        if not callable(handler_func):
            raise ValueError('handler_func argument must be a callable function')
        self.job_handlers[job_type] = handler_func