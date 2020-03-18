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


class RequestQueueCapability(Capability):
    @interface
    def queue_infrastructure_request(self, request):
        pass

    @interface
    def queue_lifecycle_request(self, request):
        pass

    @interface
    def get_infrastructure_request_queue(self, name):
        pass

    @interface
    def get_lifecycle_request_queue(self, name):
        pass


class InfrastructureConsumerFactoryCapability(Capability):
    @interface
    def create_consumer():
        pass


class LifecycleConsumerFactoryCapability(Capability):
    @interface
    def create_consumer():
        pass


class Request():
    def __init__(self, message, topic, partition):
        self.message = message
        self.request_as_json = JsonContent.read(message.value.decode('utf-8'))
        self.request_as_dict = self.request_as_json.dict_val
        self.request_id = self.request_as_dict.get("request_id", None)
        self.topic = topic
        self.partition = partition
        self.offset = message.offset
        self.exception_as_str = None

    def as_new_dict(self):
        return JsonContent.read(self.message.value.decode('utf-8')).dict_val

    def as_message(self):
        return Message(self.request_as_json.get())

    def set_failed(self, exc_info):
        self.exception_as_str = ''.join(traceback.format_exception(*exc_info)) if exc_info else ''
        self.request_as_dict['exception'] = self.exception_as_str

    def __str__(self):
        return 'request_id: {0.request_id} topic: {0.topic} partition: {0.partition} offset: {0.offset}'.format(self)


"""
Abstract handler for driver request queue requests
"""
class KafkaRequestQueueHandler():
    def __init__(self, postal_service, request_queue_config, kafka_consumer_factory):
        self.postal_service = postal_service
        self.request_queue_config = request_queue_config
        self.requests_consumer = kafka_consumer_factory.create_consumer()

    """
    Process a single request from the request queue. If processed successfully, the Kafka topic offsets
    are committed for the partition and True is retirned. Otherwise the Kafka offsets are not committed
    and False is returned.
    """
    def process_request(self):
        try:
            success = True
            for topic_partition, messages in self.requests_consumer.poll(timeout_ms=200, max_records=1).items():
                if len(messages) > 0:
                    message = messages[0]
                    request = Request(message, topic_partition.topic, topic_partition.partition)
                    try:
                        logger.debug("Read request {0}".format(request))
                        if request.request_id is None:
                            logger.warning('Request {0} is missing request_id. This request has been discarded.'.format(request))
                            self.handle_failed_request(request)
                            success = False
                        else:
                            if not self.handle_request(request):
                                logger.warning("Adding failed request with id {0} to failed topic".format(request.request_id))
                                self.handle_failed_request(request)
                                success = False
                    except Exception as e:
                        logger.warning('Caught exception handling driver request {0} : {1}'.format(request, str(e)))
                        request.set_failed(sys.exc_info())
                        self.handle_failed_request(request)
                        self.send_failed_response(request.request_id, request.exception_as_str)
                        success = False

                    # always commit, even with a failed request
                    self.commit(request)

            return success
        except Exception as e:
            # just log this because we don't know enough about the failed request to call handle_failed_request
            logger.exception('Caught exception handling driver request for topic {0} : {1}'.format(self.request_queue_config.topic.name, str(e)))
            # always commit, even with a failed request
            self.commit()
            return False

    def commit(self, request=None):
        if request is not None:
            logger.debug("Committing request {0}".format(request))
        self.requests_consumer.commit()

    def close(self):
        self.requests_consumer.close()

    def handle_failed_request(self, request):
        if request.request_id is not None:
            self.postal_service.post(Envelope(self.request_queue_config.failed_topic.name, request.as_message()), key=request.request_id)
        else:
            self.postal_service.post(Envelope(self.request_queue_config.failed_topic.name, request.as_message()))

    def handle_request(self, request):
        pass

    def send_failed_response(self, request_id, msg):
        pass

"""
Handler for infrastructure driver request queue requests
"""
class KafkaInfrastructureRequestQueueHandler(KafkaRequestQueueHandler):
    def __init__(self, postal_service, request_queue_config, kafka_consumer_factory, infrastructure_request_handler):
        super(KafkaInfrastructureRequestQueueHandler, self).__init__(postal_service, request_queue_config, kafka_consumer_factory)
        self.infrastructure_request_handler = infrastructure_request_handler

    def handle_request(self, request):
        partition = request.partition
        offset = request.offset
        request_as_dict = request.as_new_dict()

        if 'request_id' not in request_as_dict or request_as_dict['request_id'] is None:
            logger.warning('Infrastructure request for partition {0} offset {1} is missing request_id. This request has been discarded'.format(partition, offset))
            return False
        if 'template' not in request_as_dict or request_as_dict['template'] is None:
            logger.warning('Infrastructure request for partition {0} offset {1} is missing template. This request has been discarded'.format(partition, offset))
            return False
        if 'template_type' not in request_as_dict or request_as_dict['template_type'] is None:
            logger.warning('Infrastructure request for partition {0} offset {1} is missing template_type. This request has been discarded'.format(partition, offset))
            return False
        if 'properties' not in request_as_dict or request_as_dict['properties'] is None:
            logger.warning('Infrastructure request for partition {0} offset {1} is missing properties. This request has been discarded'.format(partition, offset))
            return False
        if 'system_properties' not in request_as_dict or request_as_dict['system_properties'] is None:
            logger.warning('Infrastructure request for partition {0} offset {1} is missing system_properties. This request has been discarded'.format(partition, offset))
            return False
        if 'deployment_location' not in request_as_dict or request_as_dict['deployment_location'] is None:
            logger.warning('Infrastructure request for partition {0} offset {1} is missing deployment_location. This request has been discarded'.format(partition, offset))
            return False

        request_as_dict['properties'] = PropValueMap(request_as_dict['properties'])
        request_as_dict['system_properties'] = PropValueMap(request_as_dict['system_properties'])

        return self.infrastructure_request_handler.handle_request(request_as_dict)

    def send_failed_response(self, request_id, msg):
        self.messaging_service.send_infrastructure_task(InfrastructureTask(None, request_id, STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, msg), {}))

"""
Handler for lifecycle driver request queue requests
"""
class KafkaLifecycleRequestQueueHandler(KafkaRequestQueueHandler):
    def __init__(self, postal_service, request_queue_config, kafka_consumer_factory, script_file_manager, lifecycle_request_handler):
        super(KafkaLifecycleRequestQueueHandler, self).__init__(postal_service, request_queue_config, kafka_consumer_factory)
        self.script_file_manager = script_file_manager
        self.lifecycle_request_handler = lifecycle_request_handler

    def handle_request(self, request):
        partition = request.partition
        offset = request.offset
        request_as_dict = request.as_new_dict()

        if 'request_id' not in request_as_dict or request_as_dict['request_id'] is None:
            logger.warning('Lifecycle request for partition {0} offset {1} is missing request_id. This request has been discarded'.format(partition, offset))
            return False
        if 'lifecycle_name' not in request_as_dict or request_as_dict['lifecycle_name'] is None:
            logger.warning('Lifecycle request for partition {0} offset {1} is missing lifecycle_name. This request has been discarded'.format(partition, offset))
            return False
        if 'lifecycle_scripts' not in request_as_dict or request_as_dict['lifecycle_scripts'] is None:
            logger.warning('Lifecycle request for partition {0} offset {1} is missing lifecycle_scripts. This request has been discarded'.format(partition, offset))
            return False
        if 'system_properties' not in request_as_dict or request_as_dict['system_properties'] is None:
            logger.warning('Lifecycle request for partition {0} offset {1} is missing system_properties. This request has been discarded'.format(partition, offset))
            return False
        if 'properties' not in request_as_dict or request_as_dict['properties'] is None:
            logger.warning('Lifecycle request for partition {0} offset {1} is missing properties. This request has been discarded'.format(partition, offset))
            return False
        if 'deployment_location' not in request_as_dict or request_as_dict['deployment_location'] is None:
            logger.warning('Lifecycle request for partition {0} offset {1} is missing deployment_location. This request has been discarded'.format(partition, offset))
            return False

        file_name = '{0}'.format(str(uuid.uuid4()))
        request_as_dict['lifecycle_path'] = self.script_file_manager.build_tree(file_name, request_as_dict['lifecycle_scripts'])
        request_as_dict['properties'] = PropValueMap(request_as_dict['properties'])
        request_as_dict['system_properties'] = PropValueMap(request_as_dict['system_properties'])

        return self.lifecycle_request_handler.handle_request(request_as_dict)

    def send_failed_response(self, request_id, msg):
        self.messaging_service.send_lifecycle_execution(LifecycleExecution(request_id, STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, msg), {}))

"""
Driver-specific handler for processing a single driver request
"""
class RequestHandler():
    def __init__(self):
        pass

    """
    returns True if successful, False otherwise
    """
    def handle_request(self, request):
        pass


"""
A factory for creating Kafka request queue consumers
"""
class KafkaConsumerFactory(Service):
    def __init__(self, request_queue_config, messaging_config):
        if messaging_config.connection_address is None or messaging_config.connection_address == '':
            raise ValueError('messaging_config.connection_address cannot be null')
        self.bootstrap_servers = messaging_config.connection_address
        if request_queue_config.topic.name is None or request_queue_config.topic.name == '':
            raise ValueError('request_queue_config.topic.name cannot be null')
        self.topic_name = request_queue_config.topic.name
        if request_queue_config.group_id is None or request_queue_config.group_id == '':
            raise ValueError('request_queue_config.group_id cannot be null')
        self.group_id = request_queue_config.group_id

    def create_consumer(self, max_poll_interval_ms=300000):
        logger.debug("Creating Kafka consumer for bootstrap server {0} topic {1} group {2} max_poll_interval_ms {3}".format(self.bootstrap_servers, self.topic_name, self.group_id, max_poll_interval_ms))
        return KafkaConsumer(self.topic_name, bootstrap_servers=self.bootstrap_servers, group_id=self.group_id, enable_auto_commit=False, max_poll_interval_ms=max_poll_interval_ms)

"""
A factory for creating Kafka infrastructure request queue consumers
"""
class KafkaInfrastructureConsumerFactory(KafkaConsumerFactory, InfrastructureConsumerFactoryCapability):
    def __init__(self, request_queue_config, messaging_config):
        super(KafkaInfrastructureConsumerFactory, self).__init__(request_queue_config, messaging_config)

"""
A factory for creating Kafka lifecycle request queue consumers
"""
class KafkaLifecycleConsumerFactory(KafkaConsumerFactory, LifecycleConsumerFactoryCapability):
    def __init__(self, request_queue_config, messaging_config):
        super(KafkaLifecycleConsumerFactory, self).__init__(request_queue_config, messaging_config)


"""
A service for handling driver request queues for infrastructure and lifecycle drivers
"""
class KafkaRequestQueueService(Service, RequestQueueCapability):

    def __init__(self, **kwargs):
        if 'messaging_config' not in kwargs:
            raise ValueError('messaging_config argument not provided')
        if 'infrastructure_config' not in kwargs:
            raise ValueError('infrastructure_config argument not provided')
        if 'lifecycle_config' not in kwargs:
            raise ValueError('lifecycle_config argument not provided')
        if 'postal_service' not in kwargs:
            raise ValueError('postal_service argument not provided')
        if 'script_file_manager' not in kwargs:
            raise ValueError('script_file_manager argument not provided')
        if 'infrastructure_consumer_factory' not in kwargs:
            raise ValueError('infrastructure_consumer_factory argument not provided')
        if 'lifecycle_consumer_factory' not in kwargs:
            raise ValueError('lifecycle_consumer_factory argument not provided')

        messaging_config = kwargs.get('messaging_config')
        infrastructure_config = kwargs.get('infrastructure_config')
        lifecycle_config = kwargs.get('lifecycle_config')

        self.script_file_manager = kwargs.get('script_file_manager')
        self.bootstrap_servers = messaging_config.connection_address
        self.infrastructure_request_queue_config = infrastructure_config.request_queue
        self.lifecycle_request_queue_config = lifecycle_config.request_queue
        self.postal_service = kwargs.get('postal_service')
        self.infrastructure_consumer_factory = kwargs.get('infrastructure_consumer_factory')
        self.lifecycle_consumer_factory = kwargs.get('lifecycle_consumer_factory')

    def queue_infrastructure_request(self, request):
        logger.debug('queue_infrastructure_request {0} on topic {1}'.format(str(request), self.infrastructure_request_queue_config.topic.name))

        if request is None:
            raise ValueError('Request must not be null')
        if 'request_id' not in request or request['request_id'] is None:
            raise ValueError('Request must have a request_id')

        # note: key the messages by request_id to ensure correct partitioning
        self.postal_service.post(Envelope(self.infrastructure_request_queue_config.topic.name, Message(JsonContent(request).get())), key=request['request_id'])

    def queue_lifecycle_request(self, request):
        logger.debug('queue_lifecycle_request {0} on topic {1}'.format(request, self.lifecycle_request_queue_config.topic))

        if request is None:
            raise ValueError('Request must not be null')
        if 'request_id' not in request or request['request_id'] is None:
            raise ValueError('Request must have a request_id')

        # note: key the messages by request_id to ensure correct partitioning
        self.postal_service.post(Envelope(self.lifecycle_request_queue_config.topic.name, Message(JsonContent(request).get())), key=request['request_id'])

    def get_infrastructure_request_queue(self, name, infrastructure_request_handler):
        return KafkaInfrastructureRequestQueueHandler(self.postal_service, self.infrastructure_request_queue_config, self.infrastructure_consumer_factory, infrastructure_request_handler)

    def get_lifecycle_request_queue(self, name, lifecycle_request_handler):
        logger.info("get_lifecycle_request_queue {0} {1}".format(name, lifecycle_request_handler))
        return KafkaLifecycleRequestQueueHandler(self.postal_service, self.lifecycle_request_queue_config, self.lifecycle_consumer_factory, self.script_file_manager, lifecycle_request_handler)

    def close(self):
        pass


