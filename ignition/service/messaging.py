import json
import threading
import _thread
import logging
from ignition.service.framework import Capability, Service, interface
from ignition.service.config import ConfigurationPropertiesGroup, ConfigurationProperties
from kafka import KafkaProducer, KafkaConsumer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import BrokerResponseError, TopicAlreadyExistsError

logger = logging.getLogger(__name__)

############################
# Config
############################


class MessagingProperties(ConfigurationPropertiesGroup, Service, Capability):
    """
    Configuration related to the messaging

    Attributes:
    - connection_address:
        the bootstrap servers string for the Kafka cluster to connect with
            (required: when delivery.bootstrap_service is enabled)
    - config:
            configuration relating to the messaging backend e.g. Kafka.
    - topics:
            configuration of topics to be used by the Message Delivery service
                (default: )
    """

    def __init__(self):
        super().__init__('messaging')
        self.connection_address = None
        self.topics = TopicsProperties()
        self.config = {
            'api_version_auto_timeout_ms': 5000
        }

    def __eq__(self, other):
        if not type(self) == type(other):
            return False
        return self.connection_address == other.connection_address and self.config == other.config

    def get_api_version_auto_timeout_ms(self):
        return self.config.get('api_version_auto_timeout_ms', 5000)


class TopicsProperties(ConfigurationProperties, Service, Capability):

    def __init__(self):
        self.lifecycle_execution_events = TopicConfigProperties(name='lm_vnfc_lifecycle_execution_events')
        # TODO externalize these properties by exposing them in a Properties class
        # No default name set on job_queue topic as this needs to be unique per driver
        self.job_queue = TopicConfigProperties(auto_create=True, config={'retention.ms': 60000, 'message.timestamp.difference.max.ms': 60000, 'file.delete.delay.ms': 60000})


class TopicConfigProperties(ConfigurationProperties):

    def __init__(self, name=None, auto_create=False, replication_factor=1, num_partitions=1, config=None):
        self.name = name
        self.auto_create = auto_create
        self.replication_factor = replication_factor
        self.num_partitions = num_partitions
        if config is None:
            self.config = {}
        self.config = config


class TopicCreator:

    def create_topic_if_needed(self, messaging_properties, topic_config_properties):
        if topic_config_properties.auto_create:
            # KafkaAdminClient is picky about which keyword arguments are passed in, so build the parameters from KafkaAdminClient.DEFAULT_CONFIG
            config = {key:messaging_properties.config.get(key, None) for key in KafkaAdminClient.DEFAULT_CONFIG if messaging_properties.config.get(key, None) is not None }
            config['bootstrap_servers'] = messaging_properties.connection_address
            config['client_id'] ='ignition'
            admin_client = KafkaAdminClient(**config)
            try:
                logger.info("Creating topic {0} with replication factor {1}, partitions {2} and config {3}".format(topic_config_properties.name, topic_config_properties.replication_factor, topic_config_properties.num_partitions, topic_config_properties.config))
                topic_list = [NewTopic(name=topic_config_properties.name, num_partitions=topic_config_properties.num_partitions, replication_factor=topic_config_properties.replication_factor, topic_configs=topic_config_properties.config)]
                admin_client.create_topics(new_topics=topic_list, validate_only=False)
            except TopicAlreadyExistsError as _:
                logger.info("Topic {0} already exists, not creating".format(topic_config_properties.name))
            finally:
                try:
                    admin_client.close()
                except Exception as e:
                    logger.debug("Exception closing Kafka admin client {0}".format(str(e)))
        else:
            logger.info("Not creating job queue topic {0}".format(topic_config_properties.name))


############################
# Core Classes
############################

# MessageService/SendingService
#    a service that will take a Message, wrap it in an Envelope with the required address ("topic") before sending it.
#    the main use of the MessagingService would be to send a message, so this is the main entry point to the Messaging service
# PostalService
#    a service that will take an Envelope and get it to the DeliveryService
#    a client wouldn't typically use this directory. The main use of the Postal Service would be to wrap all Messages, sent from a MessageService, with any global information e.g. headers
# DeliveryService
#   a service that will take an Envelope and get it to the target address
#   the Delivery Service actually takes care of getting the Message to the chosen message bus/queue

class DeliveryCapability(Capability):

    @interface
    def deliver(self, envelope):
        pass


class PostalCapability(Capability):

    @interface
    def post(self, envelope):
        pass


class MessagingCapability(Capability):

    @interface
    def send(self, message):
        pass


class InboxCapability(Capability):

    @interface
    def watch_inbox(self, group_id, address, read_func):
        pass


class Envelope():

    def __init__(self, address, message):
        self.address = address
        self.message = message

    def __str__(self):
        return 'Envelope[address: {0.address} message: {0.message}]'.format(self)

    def __eq__(self, other):
        if not other:
            return False

        return self.address == other.address and self.message.content == other.message.content

class Message():

    def __init__(self, content):
        self.content = str.encode(content)


class JsonContent():

    ERROR_TYPE = json.JSONDecodeError

    def __init__(self, dict_val):
        self.dict_val = dict_val

    def get(self):
        return json.dumps(self.dict_val)

    @staticmethod
    def read(str_val):
        return JsonContent(json.loads(str_val))

############################
# Provided Implementations
############################


class PostalService(Service, PostalCapability):

    def __init__(self, **kwargs):
        if 'delivery_service' not in kwargs:
            raise ValueError('delivery_service argument not provided')
        self.delivery_service = kwargs.get('delivery_service')

    def post(self, envelope, key=None):
        if envelope is None:
            raise ValueError('An envelope must be passed to post a message')
        if key is None:
            logger.debug('Posting envelope to {0} with message: {1}'.format(envelope.address, envelope.message))
            self.delivery_service.deliver(envelope)
        else:
            logger.debug('Posting envelope to {0} with key: {1} and message: {2}'.format(envelope.address, key, envelope.message))
            self.delivery_service.deliver(envelope, key=key)

class KafkaDeliveryService(Service, DeliveryCapability):

    def __init__(self, **kwargs):
        if 'messaging_properties' not in kwargs:
            raise ValueError('messaging_properties argument not provided')
        messaging_properties = kwargs.get('messaging_properties')        
        self.bootstrap_servers = messaging_properties.connection_address
        if self.bootstrap_servers is None:
            raise ValueError('connection_address not set on messaging_properties')
        self.messaging_config = messaging_properties.config
        self.producer = None

    def __lazy_init_producer(self):
        if self.producer is None:
            # KafkaProducer is picky about which keyword arguments are passed in, so build the parameters from KafkaProducer.DEFAULT_CONFIG
            config = {key:self.messaging_config.get(key, None) for key in KafkaProducer.DEFAULT_CONFIG if self.messaging_config.get(key, None) is not None}
            config['bootstrap_servers'] = self.bootstrap_servers
            config['client_id'] = 'ignition'
            self.producer = KafkaProducer(**config)

    def __on_send_success(self, record_metadata):
        logger.debug('Envelope successfully posted to {0} on partition {1} and offset {2}'.format(record_metadata.topic, record_metadata.partition, record_metadata.offset))

    def __on_send_error(self, excp):
        logger.error('Error sending envelope', exc_info=excp)

    def deliver(self, envelope, key=None):
        if envelope is None:
            raise ValueError('An envelope must be passed to deliver a message')
        self.__lazy_init_producer()
        content = envelope.message.content
        logger.debug('Delivering envelope to {0} with message content: {1}'.format(envelope.address, content))
        if key is None:
            self.producer.send(envelope.address, content).add_callback(self.__on_send_success).add_errback(self.__on_send_error)
        else:
            self.producer.send(envelope.address, key=str.encode(key), value=content).add_callback(self.__on_send_success).add_errback(self.__on_send_error)


class KafkaInboxService(Service, InboxCapability):

    def __init__(self, test_mode=False, **kwargs):
        self.test_mode = test_mode
        self.exited = False
        if 'messaging_properties' not in kwargs:
            raise ValueError('messaging_properties argument not provided')
        messaging_properties = kwargs.get('messaging_properties')
        self.bootstrap_servers = messaging_properties.connection_address
        self.messaging_config = messaging_properties.config
        if self.bootstrap_servers is None:
            raise ValueError('connection_address not set on messaging_properties')
        self.active_threads = []

    def __thread_exit_func(self, thread, closing_error):
        self.active_threads.remove(thread)
        if closing_error:
            if self.test_mode:
                self.exited = True
            else:
                logger.error('Interrupting application due to error in inbox thread {0}: {1}'.format(thread.topic, str(closing_error)))
                _thread.interrupt_main()

    def watch_inbox(self, group_id, address, read_func):
        thread = KafkaInboxThread(self.bootstrap_servers, group_id, address, read_func, self.__thread_exit_func, self.messaging_config)
        thread.setDaemon(True)
        self.active_threads.append(thread)
        try:
            thread.start()
        except Exception as _:
            self.active_threads.remove(thread)


class KafkaInboxThread(threading.Thread):

    def __init__(self, bootstrap_servers, group_id, topic, consumer_func, thread_exit_func, messaging_config):
        self.parent = threading.currentThread()
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topic = topic
        self.consumer_func = consumer_func
        self.thread_exit_func = thread_exit_func
        self.messaging_config = messaging_config

        super().__init__()

    def run(self):
        logger.info('Starting watch on inbox topic: {0}'.format(self.topic))
        closing_error = None

        # KafkaConsumer is picky about which keyword arguments are passed in, so build the parameters from KafkaProducer.DEFAULT_CONFIG
        config = {key:self.messaging_config.get(key, None) for key in KafkaConsumer.DEFAULT_CONFIG if self.messaging_config.get(key, None) is not None }
        config['bootstrap_servers'] = self.bootstrap_servers
        config['group_id'] = self.group_id
        config['enable_auto_commit'] = False
        config['client_id'] = 'ignition'
        consumer = KafkaConsumer(self.topic, **config)

        try:
            for record in consumer:
                logger.debug('Inbox ({0}) has received a new message: {1}'.format(self.topic, record))
                record_content = record.value.decode('utf-8')
                logger.debug('Inbox ({0}) message has content: {1}'.format(self.topic, record_content))
                self.consumer_func(record_content)
                # If consumer func returns without error we are ok to move on
                consumer.commit()
        except Exception as e:
            logger.exception('Inbox thread for topic {0} is closing due to error (see below):'.format(self.topic))
            closing_error = e
        finally:
            try:
                consumer.close()
            except Exception as e:
                logger.exception('Error closing consumer for inbox thread on topic {0}'.format(self.topic))
            finally:
                self.thread_exit_func(self, closing_error)
