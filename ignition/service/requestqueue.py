from ignition.model.failure import FailureDetails, FAILURE_CODE_INTERNAL_ERROR
from ignition.model.lifecycle import LifecycleExecution, STATUS_FAILED
from ignition.model.associated_topology import AssociatedTopology
from ignition.service.config import ConfigurationPropertiesGroup
from ignition.service.framework import Capability, Service, interface
from ignition.service.messaging import TopicConfigProperties, Envelope, Message, JsonContent
from ignition.utils.propvaluemap import PropValueMap
from kafka import KafkaConsumer
import logging
import uuid
import threading
import traceback
import sys


logger = logging.getLogger(__name__)


MAX_POLL_INTERVAL = 2700000

class InfrastructureRequestQueueCapability(Capability):
    @interface
    def queue_infrastructure_request(self, request):
        pass

    @interface
    def get_infrastructure_request_queue(self, name):
        pass


class LifecycleRequestQueueCapability(Capability):
    @interface
    def queue_lifecycle_request(self, request):
        pass

    @interface
    def get_lifecycle_request_queue(self, name):
        pass


class LifecycleConsumerFactoryCapability(Capability):
    @interface
    def create_consumer(self):
        pass


class Request():
    @staticmethod
    def from_str_message(message_as_str, topic, partition, offset):
        return Request(message_as_str, topic, partition, offset)

    @staticmethod
    def from_kafka_message(message, topic, partition):
        return Request(message.value.decode('utf-8'), topic, partition, message.offset)

    def __init__(self, message_as_str, topic, partition, offset):
        self.message_as_str = message_as_str
        self.request_as_json = JsonContent.read(message_as_str)
        self.request_as_dict = self.request_as_json.dict_val
        self.request_id = self.request_as_dict.get("request_id", None)
        self.topic = topic
        self.partition = partition
        self.offset = offset
        self.exception_as_str = None

    def as_new_dict(self):
        return JsonContent.read(self.message_as_str).dict_val

    def as_message(self):
        return Message(self.request_as_json.get())

    def set_failed(self, exc_info):
        self.exception_as_str = ''.join(traceback.format_exception(*exc_info)) if exc_info else ''
        self.request_as_dict['exception'] = self.exception_as_str

    def __str__(self):
        return 'request_id: {0.request_id} topic: {0.topic} partition: {0.partition} offset: {0.offset}'.format(self)



class KafkaRequestQueueHandler():
    """
    Abstract handler for driver request queue requests
    """
    def __init__(self, messaging_service, postal_service, request_queue_config, kafka_consumer_factory):
        self.messaging_service = messaging_service
        self.postal_service = postal_service
        self.request_queue_config = request_queue_config
        self.requests_consumer = kafka_consumer_factory.create_consumer(request_queue_config.max_poll_interval_ms)

    
    def process_request(self):
        """
        Process a single request from the request queue. If processed successfully, the Kafka topic offsets
        are committed for the partition.
        """
        try:
            for topic_partition, messages in self.requests_consumer.poll(timeout_ms=200, max_records=1).items():
                if len(messages) > 0:
                    request = Request.from_kafka_message(messages[0], topic_partition.topic, topic_partition.partition)
                    try:
                        logger.debug("Read request {0}".format(request))
                        if request.request_id is None:
                            logger.warning('Request {0} is missing request_id. This request has been discarded.'.format(request))
                            self.handle_failed_request(request)
                        else:
                            self.handle_request(request)
                    except Exception as e:
                        # subclasses should handle any exceptions in their own way, this is just to catch any exceptions
                        # not handled by subclasses.
                        try:
                            logger.warning('Caught exception handling driver request {0} : {1}'.format(request, str(e)))
                            request.set_failed(sys.exc_info())
                            self.handle_failed_request(request)
                        except Exception as e:
                            # just log this and carry on
                            logger.exception('Caught exception handling failed driver request {0} for topic {1} : {2}'.format(request.request_id, self.request_queue_config.topic.name, str(e)))

                    # always commit, even with a failed request
                    self.commit(request)
        except Exception as e:
            # just log this because we don't know enough about the failed request to call handle_failed_request
            logger.exception('Caught exception handling driver request for topic {0} : {1}'.format(self.request_queue_config.topic.name, str(e)))
            # always commit, even with a failed request
            self.commit()

    def commit(self, request=None):
        """
        Commit the curent request by committing the Kafka offsets on the Kafka consumer's partition
        """
        if request is not None:
            logger.debug("Committing request {0}".format(request))
        self.requests_consumer.commit()

    def close(self):
        self.requests_consumer.close()

    def handle_failed_request(self, request):
        """
        Handle a failed request by adding it to a failed requests topic specific to the driver
        """
        logger.info("handle_failed_request topic {0} request {1}".format(self.request_queue_config.failed_topic.name, type(request.request_as_json.get())))
        if request.request_id is not None:
            self.postal_service.post(Envelope(self.request_queue_config.failed_topic.name, request.as_message()), key=request.request_id)
        else:
            self.postal_service.post(Envelope(self.request_queue_config.failed_topic.name, request.as_message()))

    def handle_request(self, request):
        pass


class KafkaLifecycleRequestQueueHandler(KafkaRequestQueueHandler):
    """
    Handler for lifecycle driver request queue requests
    """
    def __init__(self, messaging_service, postal_service, request_queue_config, kafka_consumer_factory, driver_files_manager, lifecycle_request_handler):
        super(KafkaLifecycleRequestQueueHandler, self).__init__(messaging_service, postal_service, request_queue_config, kafka_consumer_factory)
        self.driver_files_manager = driver_files_manager
        self.lifecycle_request_handler = lifecycle_request_handler

    def handle_request(self, request):
        try:
            partition = request.partition
            offset = request.offset
            request_as_dict = request.as_new_dict()
            request_id = request_as_dict.get('request_id', None)

            if 'lifecycle_name' not in request_as_dict or request_as_dict['lifecycle_name'] is None:
                msg = 'Lifecycle request for partition {0} offset {1} is missing lifecycle_name.'.format(partition, offset)
                logger.warning(msg)
                self.messaging_service.send_lifecycle_execution(LifecycleExecution(request_id, STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, msg), {}))
                return
            if 'driver_files' not in request_as_dict or request_as_dict['driver_files'] is None:
                msg = 'Lifecycle request for partition {0} offset {1} is missing driver_files.'.format(partition, offset)
                logger.warning(msg)
                self.messaging_service.send_lifecycle_execution(LifecycleExecution(request_id, STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, msg), {}))
                return
            if 'system_properties' not in request_as_dict or request_as_dict['system_properties'] is None:
                msg = 'Lifecycle request for partition {0} offset {1} is missing system_properties.'.format(partition, offset)
                logger.warning(msg)
                self.messaging_service.send_lifecycle_execution(LifecycleExecution(request_id, STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, msg), {}))
                return
            if 'resource_properties' not in request_as_dict or request_as_dict['resource_properties'] is None:
                msg = 'Lifecycle request for partition {0} offset {1} is missing resource_properties.'.format(partition, offset)
                logger.warning(msg)
                self.messaging_service.send_lifecycle_execution(LifecycleExecution(request_id, STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, msg), {}))
                return
            if 'request_properties' not in request_as_dict or request_as_dict['request_properties'] is None:
                msg = 'Lifecycle request for partition {0} offset {1} is missing request_properties.'.format(partition, offset)
                logger.warning(msg)
                self.messaging_service.send_lifecycle_execution(LifecycleExecution(request_id, STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, msg), {}))
                return
            if 'associated_topology' not in request_as_dict or request_as_dict['associated_topology'] is None:
                msg = 'Lifecycle request for partition {0} offset {1} is missing associated_topology.'.format(partition, offset)
                logger.warning(msg)
                self.messaging_service.send_lifecycle_execution(LifecycleExecution(request_id, STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, msg), {}))
                return
            if 'deployment_location' not in request_as_dict or request_as_dict['deployment_location'] is None:
                msg = 'Lifecycle request for partition {0} offset {1} is missing deployment_location.'.format(partition, offset)
                logger.warning(msg)
                self.messaging_service.send_lifecycle_execution(LifecycleExecution(request_id, STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, msg), {}))
                return

            file_name = '{0}'.format(str(uuid.uuid4()))
            request_as_dict['driver_files'] = self.driver_files_manager.build_tree(file_name, request_as_dict['driver_files'])
            request_as_dict['resource_properties'] = PropValueMap(request_as_dict['resource_properties'])
            request_as_dict['system_properties'] = PropValueMap(request_as_dict['system_properties'])
            request_as_dict['request_properties'] = PropValueMap(request_as_dict['request_properties'])
            request_as_dict['associated_topology'] = AssociatedTopology.from_dict(request_as_dict['associated_topology'])

            self.lifecycle_request_handler.handle_request(request_as_dict)
        except Exception as e:
            try:
                self.messaging_service.send_lifecycle_execution(LifecycleExecution(request.request_id, STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, str(e)), {}))
            except Exception as e:
                # just log this and carry on
                logger.exception('Caught exception sending lifecycle response for driver request {0} for topic {1} : {2}'.format(request.request_id, self.request_queue_config.topic.name, str(e)))


class RequestHandler():
    """
    Driver-specific handler for processing a single driver request
    """
    def __init__(self):
        pass

    def handle_request(self, request):
        """
        returns True if successful, False otherwise
        """
        pass



class KafkaConsumerFactory(Service):
    """
    A factory for creating Kafka request queue consumers
    """
    def __init__(self, request_queue_config, messaging_properties):
        if messaging_properties is None:
            raise ValueError('messaging_properties cannot be null')
        if messaging_properties.connection_address is None or messaging_properties.connection_address == '':
            raise ValueError('messaging_properties.connection_address cannot be null')
        self.messaging_config = messaging_properties.config
        self.bootstrap_servers = messaging_properties.connection_address
        if request_queue_config.topic.name is None or request_queue_config.topic.name == '':
            raise ValueError('request_queue_config.topic.name cannot be null')
        self.topic_name = request_queue_config.topic.name
        if request_queue_config.group_id is None or request_queue_config.group_id == '':
            raise ValueError('request_queue_config.group_id cannot be null')
        self.group_id = request_queue_config.group_id

    def create_consumer(self, max_poll_interval_ms=MAX_POLL_INTERVAL):
        logger.debug("Creating Kafka consumer for bootstrap server {0} topic {1} group {2} max_poll_interval_ms {3}".format(self.bootstrap_servers, self.topic_name, self.group_id, max_poll_interval_ms))
        # KafkaConsumer is picky about which keyword arguments are passed in, so build the parameters from KafkaProducer.DEFAULT_CONFIG
        config = {key:self.messaging_config.get(key, None) for key in KafkaConsumer.DEFAULT_CONFIG if self.messaging_config.get(key, None) is not None}
        config['bootstrap_servers'] = self.bootstrap_servers
        config['group_id'] = self.group_id
        config['enable_auto_commit'] = False
        config['max_poll_interval_ms'] = max_poll_interval_ms
        config['client_id'] = 'ignition'
        return KafkaConsumer(self.topic_name, **config)


class KafkaLifecycleConsumerFactory(KafkaConsumerFactory, LifecycleConsumerFactoryCapability):
    """
    A factory for creating Kafka lifecycle request queue consumers
    """
    def __init__(self, request_queue_config, **kwargs):
        if 'messaging_properties' not in kwargs:
            raise ValueError('messaging_properties argument not provided')
        super(KafkaLifecycleConsumerFactory, self).__init__(request_queue_config, kwargs.get('messaging_properties'))


class KafkaLifecycleRequestQueueService(Service, LifecycleRequestQueueCapability):

    def __init__(self, **kwargs):
        if 'lifecycle_messaging_service' not in kwargs:
            raise ValueError('lifecycle_messaging_service argument not provided')
        if 'messaging_properties' not in kwargs:
            raise ValueError('messaging_properties argument not provided')
        if 'resource_driver_config' not in kwargs:
            raise ValueError('resource_driver_config argument not provided')
        if 'postal_service' not in kwargs:
            raise ValueError('postal_service argument not provided')
        if 'driver_files_manager' not in kwargs:
            raise ValueError('driver_files_manager argument not provided')
        if 'lifecycle_consumer_factory' not in kwargs:
            raise ValueError('lifecycle_consumer_factory argument not provided')

        messaging_properties = kwargs.get('messaging_properties')
        resource_driver_config = kwargs.get('resource_driver_config')

        self.lifecycle_messaging_service = kwargs.get('lifecycle_messaging_service')
        self.driver_files_manager = kwargs.get('driver_files_manager')
        self.bootstrap_servers = messaging_properties.connection_address
        self.lifecycle_request_queue_config = resource_driver_config.lifecycle_request_queue
        self.postal_service = kwargs.get('postal_service')
        self.lifecycle_consumer_factory = kwargs.get('lifecycle_consumer_factory')

    def queue_lifecycle_request(self, request):
        logger.debug('queue_lifecycle_request {0} on topic {1}'.format(request, self.lifecycle_request_queue_config.topic))

        if request is None:
            raise ValueError('Request must not be null')
        if 'request_id' not in request or request['request_id'] is None:
            raise ValueError('Request must have a request_id')

        # note: key the messages by request_id to ensure correct partitioning
        self.postal_service.post(Envelope(self.lifecycle_request_queue_config.topic.name, Message(JsonContent(request).get())), key=request['request_id'])

    def get_lifecycle_request_queue(self, name, lifecycle_request_handler):
        return KafkaLifecycleRequestQueueHandler(self.lifecycle_messaging_service, self.postal_service, self.lifecycle_request_queue_config, self.lifecycle_consumer_factory, self.driver_files_manager, lifecycle_request_handler)

    def close(self):
        pass

