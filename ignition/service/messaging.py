import json
import threading
import logging
from ignition.service.framework import Capability, Service, interface
from ignition.service.config import ConfigurationPropertiesGroup, ConfigurationProperties
from kafka import KafkaProducer, KafkaConsumer

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
    - topics:
            configuration of topics to be used by the Message Delivery service
                (default: )
    """

    def __init__(self):
        super().__init__('messaging')
        self.connection_address = None
        self.topics = TopicsProperties()


class TopicsProperties(ConfigurationProperties, Service, Capability):

    def __init__(self):
        self.infrastructure_task_events = 'lm_vim_infrastructure_task_events'
        self.lifecycle_execution_events = 'lm_vnfc_lifecycle_execution_events'
        self.job_queue = None  # no default set as this needs to be unique per VIM/VNFC driver cluster


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
    def watch_inbox(self, address, read_func):
        pass


class Envelope():

    def __init__(self, address, message):
        self.address = address
        self.message = message


class Message():

    def __init__(self, content):
        self.content = str.encode(content)


class JsonContent():

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

    def post(self, envelope):
        if envelope is None:
            raise ValueError('An envelope must be passed to post a message')
        logger.debug('Posting envelope to {0} with message: {1}'.format(envelope.address, envelope.message))
        self.delivery_service.deliver(envelope)


class KafkaDeliveryService(Service, DeliveryCapability):

    def __init__(self, **kwargs):
        if 'messaging_config' not in kwargs:
            raise ValueError('messaging_config argument not provided')
        messaging_config = kwargs.get('messaging_config')
        self.bootstrap_servers = messaging_config.connection_address
        if self.bootstrap_servers is None:
            raise ValueError('connection_address not set on messaging_config')
        self.producer = None

    def __lazy_init_producer(self):
        if self.producer is None:
            self.producer = KafkaProducer(bootstrap_servers=self.bootstrap_servers)

    def __on_send_success(self, record_metadata):
        logger.info('Envelope successfully posted to {0} on partition {1} and offset {2}'.format(record_metadata.topic, record_metadata.partition, record_metadata.offset))

    def __on_send_error(self, excp):
        logger.error('Error sending envelope', exc_info=excp)

    def deliver(self, envelope):
        if envelope is None:
            raise ValueError('An envelope must be passed to deliver a message')
        self.__lazy_init_producer()
        content = envelope.message.content
        logger.info('Delivering envelope to {0} with message content: {1}'.format(envelope.address, content))
        self.producer.send(envelope.address, content).add_callback(self.__on_send_success).add_errback(self.__on_send_error)


class KafkaInboxService(Service, InboxCapability):

    def __init__(self, **kwargs):
        if 'messaging_config' not in kwargs:
            raise ValueError('messaging_config argument not provided')
        messaging_config = kwargs.get('messaging_config')
        self.bootstrap_servers = messaging_config.connection_address
        if self.bootstrap_servers is None:
            raise ValueError('connection_address not set on messaging_config')
        self.active_threads = []

    def __thread_exit_func(self, thread):
        self.active_threads.remove(thread)

    def watch_inbox(self, address, read_func):
        thread = KafkaInboxThread(self.bootstrap_servers, address, read_func, self.__thread_exit_func)
        self.active_threads.append(thread)
        try:
            thread.start()
        except Exception as e:
            self.active_threads.remove(thread)


class KafkaInboxThread(threading.Thread):

    def __init__(self, bootstrap_servers, topic, consumer_func, thread_exit_func):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.consumer_func = consumer_func
        self.thread_exit_func = thread_exit_func
        super().__init__()

    def run(self):
        consumer = KafkaConsumer(self.topic, bootstrap_servers=self.bootstrap_servers)
        try:
            for record in consumer:
                self.consumer_func(record.value.decode('utf-8'))
        finally:
            try:
                consumer.close()
            finally:
                self.thread_exit_func(self)
