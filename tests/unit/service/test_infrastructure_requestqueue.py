import unittest
import uuid
import collections
import json
import logging
from unittest.mock import patch, MagicMock
from ignition.model.failure import FailureDetails, FAILURE_CODE_INTERNAL_ERROR
from ignition.model.infrastructure import InfrastructureTask, STATUS_FAILED
from ignition.service.infrastructure import InfrastructureProperties, InfrastructureMessagingCapability
from ignition.service.requestqueue import KafkaInfrastructureRequestQueueService, RequestHandler, KafkaInfrastructureConsumerFactory, KafkaRequestQueueHandler
from ignition.service.messaging import Envelope, TopicsProperties, MessagingProperties, TopicConfigProperties
from kafka.structs import TopicPartition
from kafka import KafkaConsumer

MockRecord = collections.namedtuple('MockRecord', ['value', 'offset'])
logger = logging.getLogger(__name__)

class TestInfrastructureRequestQueueService(unittest.TestCase):

    def setUp(self):
        self.infrastructure_config = InfrastructureProperties()
        self.infrastructure_config.request_queue.topic.name = "infrastructure_request_queue"
        self.infrastructure_config.request_queue.failed_topic.name = "infrastructure_request_queue_failed"
        self.mock_infrastructure_messaging_service = MagicMock()
        self.mock_infrastructure_consumer_factory = MagicMock()
        self.mock_postal_service = MagicMock()
        self.mock_messaging_config = MagicMock(connection_address='test:9092')

    def test_init_without_infrastructure_messaging_service_throws_error(self):
        with self.assertRaises(ValueError) as context:
            KafkaInfrastructureRequestQueueService(infrastructure_config=self.infrastructure_config, postal_service=self.mock_postal_service, infrastructure_consumer_factory=self.mock_infrastructure_consumer_factory)
        self.assertEqual(str(context.exception), 'infrastructure_messaging_service argument not provided')

    def test_init_without_messaging_config_throws_error(self):
        with self.assertRaises(ValueError) as context:
            KafkaInfrastructureRequestQueueService(infrastructure_messaging_service=self.mock_infrastructure_messaging_service, infrastructure_config=self.infrastructure_config, postal_service=self.mock_postal_service, infrastructure_consumer_factory=self.mock_infrastructure_consumer_factory)
        self.assertEqual(str(context.exception), 'messaging_config argument not provided')

    def test_init_without_postal_service_throws_error(self):
        with self.assertRaises(ValueError) as context:
            KafkaInfrastructureRequestQueueService(infrastructure_messaging_service=self.mock_infrastructure_messaging_service, infrastructure_config=self.infrastructure_config, messaging_config=self.mock_messaging_config, infrastructure_consumer_factory=self.mock_infrastructure_consumer_factory)
        self.assertEqual(str(context.exception), 'postal_service argument not provided')

    def test_init_without_infrastructure_config_throws_error(self):
        with self.assertRaises(ValueError) as context:
            KafkaInfrastructureRequestQueueService(infrastructure_messaging_service=self.mock_infrastructure_messaging_service, postal_service=self.mock_postal_service, messaging_config=self.mock_messaging_config, infrastructure_consumer_factory=self.mock_infrastructure_consumer_factory)
        self.assertEqual(str(context.exception), 'infrastructure_config argument not provided')

    def test_init_KafkaInfrastructureConsumerFactory_fails_when_messaging_connection_address_not_set(self):
        messaging_conf = MessagingProperties()
        messaging_conf.connection_address = None
        infrastructure_config = InfrastructureProperties()
        with self.assertRaises(ValueError) as context:
            KafkaInfrastructureConsumerFactory(infrastructure_config, messaging_conf)

    def test_queue_infrastructure_request_posts_message(self):
        requestqueue_service = KafkaInfrastructureRequestQueueService(infrastructure_messaging_service=self.mock_infrastructure_messaging_service, postal_service=self.mock_postal_service, infrastructure_config=self.infrastructure_config, messaging_config=self.mock_messaging_config, infrastructure_consumer_factory=self.mock_infrastructure_consumer_factory)

        request = {
            "request_id": "112",
            "template": "template",
            "template_type": "test",
            "properties": {
                "prop1": "value1"
            },
            "system_properties": {
            },
            'deployment_location': {
                "name": "dl1",
                "type": "Openstack",
                "properties": {
                    "prop1": "value1"
                }
            }
        }

        requestqueue_service.queue_infrastructure_request(request)
        self.assert_request_posted(self.infrastructure_config.request_queue.topic.name, request)

    def test_queue_infrastructure_request_missing_request_id(self):
        requestqueue_service = KafkaInfrastructureRequestQueueService(infrastructure_messaging_service=self.mock_infrastructure_messaging_service, postal_service=self.mock_postal_service, infrastructure_config=self.infrastructure_config, messaging_config=self.mock_messaging_config, infrastructure_consumer_factory=self.mock_infrastructure_consumer_factory)

        request = {
            "template": "template",
            "template_type": "test",
            "properties": {
                "prop1": "value1"
            },
            "system_properties": {
                "prop1": "value1"
            },
            'deployment_location': {
                "name": "dl1",
                "type": "Openstack",
                "properties": {
                    "prop1": "value1"
                }
            }
        }

        with self.assertRaises(ValueError) as context:
            requestqueue_service.queue_infrastructure_request(request)
        self.assertEqual(str(context.exception), 'Request must have a request_id')
        self.mock_postal_service.post.assert_not_called()

    def test_queue_infrastructure_request_null_request_id(self):
        requestqueue_service = KafkaInfrastructureRequestQueueService(infrastructure_messaging_service=self.mock_infrastructure_messaging_service, postal_service=self.mock_postal_service, infrastructure_config=self.infrastructure_config, messaging_config=self.mock_messaging_config, infrastructure_consumer_factory=self.mock_infrastructure_consumer_factory)

        request = {
            "request_id": None,
            "template": "template",
            "template_type": "test",
            "properties": {
                "prop1": "value1"
            },
            "system_properties": {
                "prop1": "value1"
            },
            'deployment_location': {
                "name": "dl1",
                "type": "Openstack",
                "properties": {
                    "prop1": "value1"
                }
            }
        }

        with self.assertRaises(ValueError) as context:
            requestqueue_service.queue_infrastructure_request(request)
        self.assertEqual(str(context.exception), 'Request must have a request_id')
        self.mock_postal_service.post.assert_not_called()

    def test_queue_infrastructure_request_posts_message(self):
        requestqueue_service = KafkaInfrastructureRequestQueueService(infrastructure_messaging_service=self.mock_infrastructure_messaging_service, postal_service=self.mock_postal_service, infrastructure_config=self.infrastructure_config, messaging_config=self.mock_messaging_config, infrastructure_consumer_factory=self.mock_infrastructure_consumer_factory)

        request = {
            "request_id": "112",
            "template": "template",
            "template_type": "test",
            "properties": {
                "prop1": "value1"
            },
            "system_properties": {

            },
            'deployment_location': {
                "name": "dl1",
                "type": "Openstack",
                "properties": {
                    "prop1": "value1"
                }
            }
        }

        requestqueue_service.queue_infrastructure_request(request)
        self.mock_postal_service.post.assert_called_once()
        args, kwargs = self.mock_postal_service.post.call_args
        self.assertEqual(len(args), 1)
        envelope_arg = args[0]
        self.assertIsInstance(envelope_arg, Envelope)
        self.assertEqual(envelope_arg.address, self.infrastructure_config.request_queue.topic.name)
        self.assertEqual(envelope_arg.message.content, json.dumps(request).encode())

    def test_infrastructure_requestqueue_process_request(self):
        mock_postal_service = MagicMock()
        mock_request_queue_config = MagicMock()
        mock_request_queue_config.group_id = "1"
        mock_request_queue_config.failed_topic = TopicConfigProperties(auto_create=True, num_partitions=1, config={})
        mock_request_queue_config.failed_topic.name = "test_failed"
        mock_kafka_infrastructure_consumer = MagicMock()
        mock_kafka_infrastructure_consumer_factory = MagicMock()
        mock_kafka_infrastructure_consumer_factory.create_consumer.return_value = mock_kafka_infrastructure_consumer

        request_queue_service = KafkaInfrastructureRequestQueueService(infrastructure_messaging_service=self.mock_infrastructure_messaging_service, postal_service=self.mock_postal_service, infrastructure_config=self.infrastructure_config, messaging_config=self.mock_messaging_config, infrastructure_consumer_factory=mock_kafka_infrastructure_consumer_factory)

        mock_kafka_infrastructure_consumer.poll.return_value = {
            TopicPartition('infrastructure_request_queue', 0): [
                MockRecord(offset=0, value=json.JSONEncoder().encode({
                   "request_id": "a61dec25-fcdc-4281-b067-fa18681d65a7",
                   "template": "123",
                   "template_type": "test",
                   "system_properties": {
                      "resourceManagerId": {
                         "type": "string",
                         "value": "brent"
                      },
                      "resourceId": {
                         "type": "string",
                         "value": "ea21dd57-2664-4fb1-a8ac-c1fa77431ec7"
                      },
                      "infrastructureId": {
                         "type": "string",
                         "value": "91d11950-4787-44ed-a225-002d468e1135"
                      },
                      "metricKey": {
                         "type": "string",
                         "value": "7e6b7293-3a23-420c-9ff6-59323ca1e0b0"
                      },
                      "requestId": {
                         "type": "string",
                         "value": "af269525-0f10-4192-bb85-55516787bb74"
                      },
                      "resourceName": {
                         "type": "string",
                         "value": "apache20__hw-apache1"
                      },
                      "deploymentLocation": {
                         "type": "string",
                         "value": "core1"
                      },
                      "resourceType": {
                         "type": "string",
                         "value": "resource::hw-apache-vnfc-apache-demo::1.0"
                      }
                   },
                   "properties": {
                      "site_name": {
                         "type": "string",
                         "value": "hw"
                      },
                      "server1_internal_ip": {
                         "type": "string",
                         "value": "10.10.10.152"
                      },
                      "flavor": {
                         "type": "string",
                         "value": "m1.small"
                      },
                   },
                   "deployment_location": {
                      "resourceManager": "brent",
                      "name": "core1",
                      "type": "Openstack",
                      "properties": {
                      }
                   }
                }).encode())]
        }

        request_handler = TestRequestHandler()
        request_queue = request_queue_service.get_infrastructure_request_queue('test', request_handler)
        request_queue.process_request()

        self.assertEqual(len(request_handler.failed_requests), 0)
        self.assertEqual(len(request_handler.requests), 1)
        request = request_handler.requests[0]
        self.assertIsInstance(request, dict)
        self.assertEqual(request["request_id"], "a61dec25-fcdc-4281-b067-fa18681d65a7")
        mock_kafka_infrastructure_consumer.commit.assert_called_once()

    def test_infrastructure_requestqueue_process_missing_request_id(self):
        self.infrastructure_config.request_queue = MagicMock()
        self.infrastructure_config.request_queue.group_id = "1"
        self.infrastructure_config.request_queue.failed_topic = TopicConfigProperties(auto_create=True, num_partitions=1, config={})
        self.infrastructure_config.request_queue.failed_topic.name = "test_failed"

        mock_kafka_infrastructure_consumer = MagicMock()
        mock_kafka_infrastructure_consumer_factory = MagicMock()
        mock_kafka_infrastructure_consumer_factory.create_consumer.return_value = mock_kafka_infrastructure_consumer

        request_queue_service = KafkaInfrastructureRequestQueueService(infrastructure_messaging_service=self.mock_infrastructure_messaging_service, postal_service=self.mock_postal_service, infrastructure_config=self.infrastructure_config, messaging_config=self.mock_messaging_config, infrastructure_consumer_factory=mock_kafka_infrastructure_consumer_factory)

        request = {
           "template": "123",
           "template_type": "test",
           "system_properties": {
           },
           "properties": {
           },
           "deployment_location": {
           }
        }

        mock_kafka_infrastructure_consumer.poll.return_value = {
            TopicPartition('infrastructure_request_queue', 0): [
                MockRecord(offset=0, value=json.JSONEncoder().encode(request).encode())]
        }

        request_handler = TestRequestHandler()
        request_queue = request_queue_service.get_infrastructure_request_queue('test', request_handler)
        self.assertFalse(request_queue.process_request())
        mock_kafka_infrastructure_consumer.commit.assert_called_once()
        self.mock_postal_service.post.assert_called_once()
        args, kwargs = self.mock_postal_service.post.call_args
        self.assertEqual(len(args), 1)
        envelope_arg = args[0]
        self.assertIsInstance(envelope_arg, Envelope)
        self.assertEqual(envelope_arg.address, "test_failed")
        self.assertEqual(envelope_arg.message.content, json.dumps(request).encode())

class TestRequestHandler(RequestHandler):
    def __init__(self):
        self.requests = []
        self.failed_requests = []
        self.is_failed = False

    def set_failed_request(self, is_failed):
        self.is_failed = is_failed

    def handle_request(self, request):
        self.requests.append(request)
        return not self.is_failed