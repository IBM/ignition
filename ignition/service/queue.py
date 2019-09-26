from ignition.service.framework import Capability, Service, interface
from ignition.service.messaging import Message, Envelope, JsonContent
from ignition.service.config import ConfigurationPropertiesGroup
import logging
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import BrokerResponseError, TopicAlreadyExistsError

logger = logging.getLogger(__name__)

############################
# Config
############################

class JobQueueConfigProperties(ConfigurationPropertiesGroup):
    """
    Configuration related to job queue topics config

    Attributes:
    - retention_ms:
            the name of the Kafka job queue topic
                (required: when delivery.bootstrap_service is enabled)
    - timestamp_difference_max_ms:
            the replication factor of the job queue topic
                (required: when delivery.bootstrap_service is enabled)
    - file_delete_delay_ms:
            the number of partitions in the job queue topic
                (required: when delivery.bootstrap_service is enabled)
    """

    def __init__(self):
        super().__init__('config')
        self.retention_ms = 60000
        self.timestamp_difference_max_ms = self.retention_ms
        self.file_delete_delay_ms = 60000

class JobQueueProperties(ConfigurationPropertiesGroup):
    """
    Configuration related to job queue topics

    Attributes:
    - name:
            the name of the Kafka job queue topic
                (required: when delivery.bootstrap_service is enabled)
    - replication_factor:
            the replication factor of the job queue topic
                (required: when delivery.bootstrap_service is enabled)
    - num_partitions:
            the number of partitions in the job queue topic
                (required: when delivery.bootstrap_service is enabled)
    """

    def __init__(self):
        super().__init__('jobqueue')
        self.name = None
        self.replication_factor = 1
        self.num_partitions = 1
        self.config = JobQueueConfigProperties()

class JobQueueCapability(Capability):
    
    @interface
    def queue_job(self, job):
        pass
    
    @interface
    def register_job_handler(self, job_type, handler_func):
        pass

class MessagingJobQueueService(Service, JobQueueCapability):

    JOB_TYPE_KEY = 'job_type'

    def __init__(self, kafka_connection_address, **kwargs):
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
        self.kafka_connection_address = kafka_connection_address
        if self.kafka_connection_address is None:
            raise ValueError('kafka_connection_address must be set')

        self.__init_jobqueue_topic()
        self.job_handlers = {}
        self.__init_watch_for_jobs()

    def __init_jobqueue_topic(self):
        admin_client = KafkaAdminClient(bootstrap_servers=self.kafka_connection_address, client_id='ignition')

        try:
            logger.info("Creating topic {0} with replication factor {1} and partitions {2}".format(self.job_queue_topic.name, self.job_queue_topic.replication_factor, self.job_queue_topic.num_partitions))
            topic_config = {
                "retention.ms": self.job_queue_topic.config.retention_ms,
                "message.timestamp.difference.max.ms": self.job_queue_topic.config.timestamp_difference_max_ms,
                "file.delete.delay.ms": self.job_queue_topic.config.file_delete_delay_ms
            }
            topic_list = [NewTopic(name=self.job_queue_topic.name, num_partitions=self.job_queue_topic.num_partitions, replication_factor=self.job_queue_topic.replication_factor, topic_configs=topic_config)]
            admin_client.create_topics(new_topics=topic_list, validate_only=False)
        except TopicAlreadyExistsError as _:
            logger.info("Topic {0} already exists, not creating".format(self.job_queue_topic.name))
        except BrokerResponseError as _:
            logger.exception("Unexpected exception creating topic {0}".format(self.job_queue_topic.name))
        finally:
            try:
                admin_client.close()
            except Exception as e:
                logger.debug("Exception closing Kafka admin client {0}".format(str(e)))

    def __init_watch_for_jobs(self):
        self.inbox_service.watch_inbox(self.job_queue_topic, self.__received_next_job_handler)
        pass

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