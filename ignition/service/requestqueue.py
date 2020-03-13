from ignition.service.config import ConfigurationPropertiesGroup
from ignition.service.framework import Capability, Service, interface
from ignition.service.messaging import TopicConfigProperties, Envelope, Message, JsonContent
from ignition.utils.propvaluemap import PropValueMap
from kafka import KafkaConsumer
import logging
import uuid

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


class KafkaRequestQueueHandler():
    def __init__(self, kafka_consumer_factory):
        self.requests_consumer = kafka_consumer_factory.create_consumer()

    def process_request(self):
        try:
            for topic_partition, messages in self.requests_consumer.poll(timeout_ms=200, max_records=1).items():
                if len(messages) > 0:
                    request = JsonContent.read(messages[0].value.decode('utf-8')).dict_val
                    request["partition"] = topic_partition.partition
                    request["offset"] = messages[0].offset
                    if self.handle_request(request):
                        # If request handler returns with 'true' and without raising an error we are ok
                        # to commit topic offset and move on
                        self.requests_consumer.commit()
        except Exception as e:
            logger.exception('Lifecycle request queue for topic {0} is closing due to error {1}'.format(self.request_queue_config.topic.name, str(e)))
            # re-raise after logging, should kill the app so it can be restarted
            raise e

    def close(self):
        self.requests_consumer.close()

    def handle_request(self, request):
        pass


class KafkaInfrastructureRequestQueueHandler(KafkaRequestQueueHandler):
    def __init__(self, kafka_consumer_factory, infrastructure_request_handler):
        super(KafkaInfrastructureRequestQueueHandler, self).__init__(kafka_consumer_factory)
        self.infrastructure_request_handler = infrastructure_request_handler

    def handle_request(self, request):
        try:
            partition = request.get("partition", None)
            offset = request.get("offset", None)

            if 'request_id' not in request or request['request_id'] is None:
                logger.warning('Infrastructure request for partition {0} offset {1} is missing request_id. This request has been discarded'.format(partition, offset))
                return False
            if 'template' not in request or request['template'] is None:
                logger.warning('Infrastructure request for partition {0} offset {1} is missing template. This request has been discarded'.format(partition, offset))
                return False
            if 'template_type' not in request or request['template_type'] is None:
                logger.warning('Infrastructure request for partition {0} offset {1} is missing template_type. This request has been discarded'.format(partition, offset))
                return False
            if 'properties' not in request or request['properties'] is None:
                logger.warning('Infrastructure request for partition {0} offset {1} is missing properties. This request has been discarded'.format(partition, offset))
                return False
            if 'system_properties' not in request or request['system_properties'] is None:
                logger.warning('Infrastructure request for partition {0} offset {1} is missing system_properties. This request has been discarded'.format(partition, offset))
                return False
            if 'deployment_location' not in request or request['deployment_location'] is None:
                logger.warning('Infrastructure request for partition {0} offset {1} is missing deployment_location. This request has been discarded'.format(partition, offset))
                return False

            request['properties'] = PropValueMap(request['properties'])
            request['system_properties'] = PropValueMap(request['system_properties'])

            return self.infrastructure_request_handler.handle(request)
        except Exception as e:
            logger.exception('Infrastructure request queue for topic {0} is closing due to error {1}'.format(self.request_queue_config.topic.name, str(e)))
            # re-raise after logging, should kill the app so it can be restarted
            raise e


class KafkaLifecycleRequestQueueHandler(KafkaRequestQueueHandler):
    def __init__(self, kafka_consumer_factory, script_file_manager, lifecycle_request_handler):
        super(KafkaLifecycleRequestQueueHandler, self).__init__(kafka_consumer_factory)
        self.script_file_manager = script_file_manager
        self.lifecycle_request_handler = lifecycle_request_handler

    def handle_request(self, request):
        try:
            partition = request.get("partition", None)
            offset = request.get("offset", None)

            if 'request_id' not in request or request['request_id'] is None:
                logger.warning('Lifecycle request for partition {0} offset {1} is missing request_id. This request has been discarded'.format(partition, offset))
                return False
            if 'lifecycle_name' not in request or request['lifecycle_name'] is None:
                logger.warning('Lifecycle request for partition {0} offset {1} is missing lifecycle_name. This request has been discarded'.format(partition, offset))
                return False
            if 'lifecycle_scripts' not in request or request['lifecycle_scripts'] is None:
                logger.warning('Lifecycle request for partition {0} offset {1} is missing lifecycle_scripts. This request has been discarded'.format(partition, offset))
                return False
            if 'system_properties' not in request or request['system_properties'] is None:
                logger.warning('Lifecycle request for partition {0} offset {1} is missing system_properties. This request has been discarded'.format(partition, offset))
                return False
            if 'properties' not in request or request['properties'] is None:
                logger.warning('Lifecycle request for partition {0} offset {1} is missing properties. This request has been discarded'.format(partition, offset))
                return False
            if 'deployment_location' not in request or request['deployment_location'] is None:
                logger.warning('Lifecycle request for partition {0} offset {1} is missing deployment_location. This request has been discarded'.format(partition, offset))
                return False

            file_name = '{0}'.format(str(uuid.uuid4()))
            request['lifecycle_path'] = self.script_file_manager.build_tree(file_name, request['lifecycle_scripts'])
            request['properties'] = PropValueMap(request['properties'])
            request['system_properties'] = PropValueMap(request['system_properties'])

            return self.lifecycle_request_handler.handle(request)
        except Exception as e:
            logger.exception('Lifecycle request queue for topic {0} is closing due to error {1}'.format(self.request_queue_config.topic.name, str(e)))
            # re-raise after logging, should kill the app so it can be restarted
            raise e


class RequestHandler():
    def __init__(self):
        pass

    """
    returns True if successful, False otherwise
    """
    def handle(self, request):
        pass


class KafkaInfrastructureConsumerFactory(InfrastructureConsumerFactoryCapability):
    def __init__(self, messaging_config, infrastructure_config):
        if messaging_config.connection_address is None or messaging_config.connection_address == '':
            raise ValueError('messaging_config.connection_address cannot be null')
        self.bootstrap_servers = messaging_config.connection_address
        if infrastructure_config.request_queue.topic.name is None or infrastructure_config.request_queue.topic.name == '':
            raise ValueError('infrastructure_config.request_queue.topic.name cannot be null')
        self.topic_name = infrastructure_config.request_queue.topic.name
        if infrastructure_config.request_queue.group_id is None or infrastructure_config.request_queue.group_id == '':
            raise ValueError('infrastructure_config.request_queue.group_id cannot be null')
        self.group_id = infrastructure_config.request_queue.group_id

    def create_consumer(self):
        return KafkaConsumer(self.topic_name, bootstrap_servers=self.bootstrap_servers, group_id=self.group_id, enable_auto_commit=False, max_poll_interval_ms=300000)


class KafkaLifecycleConsumerFactory(LifecycleConsumerFactoryCapability):
    def __init__(self, messaging_config, lifecycle_config):
        if messaging_config.connection_address is None or messaging_config.connection_address == '':
            raise ValueError('messaging_config.connection_address cannot be null')
        self.bootstrap_servers = messaging_config.connection_address
        if lifecycle_config.request_queue.topic.name is None or lifecycle_config.request_queue.topic.name == '':
            raise ValueError('lifecycle_config.request_queue.topic.name cannot be null')
        self.topic_name = lifecycle_config.request_queue.topic.name
        if lifecycle_config.request_queue.group_id is None or lifecycle_config.request_queue.group_id == '':
            raise ValueError('lifecycle_config.request_queue.group_id cannot be null')
        self.group_id = lifecycle_config.request_queue.group_id

    def create_consumer(self):
        return KafkaConsumer(self.topic_name, bootstrap_servers=self.bootstrap_servers, group_id=self.group_id, enable_auto_commit=False, max_poll_interval_ms=300000)


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
        if request['request_id'] is None:
            raise ValueError('Infrastructure request must have a request_id')

        # note: key the messages by request_id to ensure correct partitioning
        self.postal_service.post(Envelope(self.infrastructure_request_queue_config.topic.name, Message(JsonContent(request).get())), key=request['request_id'])

    def queue_lifecycle_request(self, request):
        logger.debug('queue_lifecycle_request {0} on topic {1}'.format(str(request), self.lifecycle_request_queue_config.topic))

        if request is None:
            raise ValueError('Request must not be null')
        if request['request_id'] is None:
            raise ValueError('Infrastructure request must have a request_id')

        # note: key the messages by request_id to ensure correct partitioning
        self.postal_service.post(Envelope(self.lifecycle_request_queue_config.topic.name, Message(JsonContent(request).get())), key=request['request_id'])

    def get_infrastructure_request_queue(self, name, infrastructure_request_handler):
        return KafkaInfrastructureRequestQueueHandler(self.infrastructure_consumer_factory, infrastructure_request_handler)

    def get_lifecycle_request_queue(self, name, lifecycle_request_handler):
        return KafkaLifecycleRequestQueueHandler(self.lifecycle_consumer_factory, self.script_file_manager, lifecycle_request_handler)

    def close(self):
        pass


