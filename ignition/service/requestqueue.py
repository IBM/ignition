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


class KafkaInfrastructureRequestQueueHandler():
    def __init__(self, name, bootstrap_servers, request_queue_config):
        self.bootstrap_servers = bootstrap_servers
        self.request_queue_config = request_queue_config
        self.group_id = request_queue_config.group_id
        self.requests_consumer = KafkaConsumer(self.request_queue_config.topic.name, bootstrap_servers=self.bootstrap_servers, group_id=self.group_id, enable_auto_commit=False)

    def process_infrastructure_request(self, infrastructure_request_handler):
        try:
            for topic_partition, messages in self.requests_consumer.poll(timeout_ms=200, max_records=1).items():
                if topic_partition.topic == self.request_queue_config.topic.name:
                    for message in messages:
                        # message value and key are raw bytes -- decode if necessary!
                        logger.debug('KafkaInfrastructureRequestQueueHandler ({0}) has received a new infrastucture request message: {1}'.format(self.request_queue_config.topic.name, message.value))
                        request = JsonContent.read(message.value.decode('utf-8')).dict_val
                        logger.debug('KafkaInfrastructureRequestQueueHandler ({0}) infrastucture request message: {1}'.format(self.request_queue_config.topic.name, request))

                        # if 'infrastructure_id' not in request or request['infrastructure_id'] is None:
                        #     logger.warning('Infrastructure request {0} is missing infrastructure_id. This request has been discarded'.format(request))
                        #     return False
                        if 'request_id' not in request or request['request_id'] is None:
                            logger.warning('Infrastructure request {0} is missing request_id. This request has been discarded'.format(request))
                            return False
                        if 'template' not in request or request['template'] is None:
                            logger.warning('Infrastructure request {0} is missing template. This request has been discarded'.format(request))
                            return False
                        if 'template_type' not in request or request['template_type'] is None:
                            logger.warning('Infrastructure request {0} is missing template_type. This request has been discarded'.format(request))
                            return False
                        if 'inputs' not in request or request['inputs'] is None:
                            logger.warning('Infrastructure request {0} is missing inputs. This request has been discarded'.format(request))
                            return False
                        if 'deployment_location' not in request or request['deployment_location'] is None:
                            logger.warning('Infrastructure request {0} is missing deployment_location. This request has been discarded'.format(request))
                            return False

                        request['inputs'] = PropValueMap(request['inputs'])

                        infrastructure_request_handler(request)

                        # If request handler returns without error we are ok to move on
                        logger.info("Committing infrastructure requests queue topic")
                        self.requests_consumer.commit()
        except Exception as e:
            logger.exception('Infrastructure request queue for topic {0} is closing due to error {1}'.format(self.request_queue_config.topic.name, str(e)))
            # re-raise after logging, should kill the app so it can be restarted
            raise e


class KafkaLifecycleRequestQueueHandler():
    def __init__(self, name, bootstrap_servers, request_queue_config, script_file_manager):
        self.bootstrap_servers = bootstrap_servers
        self.request_queue_config = request_queue_config
        self.group_id = request_queue_config.group_id
        self.script_file_manager = script_file_manager
        self.requests_consumer = KafkaConsumer(self.request_queue_config.topic.name, bootstrap_servers=self.bootstrap_servers, group_id=self.group_id, enable_auto_commit=False)
        logger.info("Created KafkaLifecycleRequestQueueHandler with group_id {0}".format(self.group_id))

    def process_lifecycle_request(self, lifecycle_request_handler):
        try:
            for topic_partition, messages in self.requests_consumer.poll(timeout_ms=200, max_records=1).items():
                if topic_partition.topic == self.request_queue_config.topic.name:
                    for message in messages:
                        # logger.debug('KafkaLifecycleRequestQueueHandler ({0}) has received a new lifecycle request message: {1}'.format(self.request_queue_config.topic.name, message.value))
                        request = JsonContent.read(message.value.decode('utf-8')).dict_val
                        logger.debug('KafkaLifecycleRequestQueueHandler ({0}) lifecycle request message: {1}'.format(self.request_queue_config.topic.name, request['request_id']))

                        # if 'infrastructure_id' not in request or request['infrastructure_id'] is None:
                        #     logger.warning('Infrastructure request {0} is missing infrastructure_id. This request has been discarded'.format(request))
                        #     return False
                        if 'request_id' not in request or request['request_id'] is None:
                            logger.warning('Lifecycle request {0} is missing request_id. This request has been discarded'.format(request))
                            return False
                        if 'lifecycle_name' not in request or request['lifecycle_name'] is None:
                            logger.warning('Lifecycle request {0} is missing lifecycle_name. This request has been discarded'.format(request))
                            return False
                        if 'lifecycle_scripts' not in request or request['lifecycle_scripts'] is None:
                            logger.warning('Lifecycle request {0} is missing lifecycle_scripts. This request has been discarded'.format(request))
                            return False
                        if 'system_properties' not in request or request['system_properties'] is None:
                            logger.warning('Lifecycle request {0} is missing system_properties. This request has been discarded'.format(request))
                            return False
                        if 'properties' not in request or request['properties'] is None:
                            logger.warning('Lifecycle request {0} is missing properties. This request has been discarded'.format(request))
                            return False
                        if 'deployment_location' not in request or request['deployment_location'] is None:
                            logger.warning('Lifecycle request {0} is missing deployment_location. This request has been discarded'.format(request))
                            return False

                        file_name = '{0}'.format(str(uuid.uuid4()))
                        request['lifecycle_path'] = self.script_file_manager.build_tree(file_name, request['lifecycle_scripts'])
                        request['properties'] = PropValueMap(request['properties'])
                        request['system_properties'] = PropValueMap(request['system_properties'])

                        lifecycle_request_handler(request)

                        # If request handler returns without error we are ok to move on
                        logger.info("Committing lifecycle requests queue topic")
                        self.requests_consumer.commit()
        except Exception as e:
            logger.exception('Lifecycle request queue for topic {0} is closing due to error {1}'.format(self.request_queue_config.topic.name, str(e)))
            # re-raise after logging, should kill the app so it can be restarted
            raise e

    def close(self):
        self.requests_consumer.close()



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

        messaging_config = kwargs.get('messaging_config')
        infrastructure_config = kwargs.get('infrastructure_config')
        lifecycle_config = kwargs.get('lifecycle_config')

        self.script_file_manager = kwargs.get('script_file_manager')
        self.bootstrap_servers = messaging_config.connection_address
        self.infrastructure_request_queue_config = infrastructure_config.request_queue
        self.lifecycle_request_queue_config = lifecycle_config.request_queue
        self.postal_service = kwargs.get('postal_service')

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

    def get_infrastructure_request_queue(self, name):
        return KafkaInfrastructureRequestQueueHandler(name, self.bootstrap_servers, self.infrastructure_request_queue_config)

    def get_lifecycle_request_queue(self, name):
        return KafkaLifecycleRequestQueueHandler(name, self.bootstrap_servers, self.lifecycle_request_queue_config, self.script_file_manager)

    def close(self):
        pass


