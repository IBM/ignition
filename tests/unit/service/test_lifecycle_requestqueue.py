import unittest
import uuid
import collections
import json
import logging
from unittest.mock import patch, MagicMock
from ignition.model.failure import FailureDetails, FAILURE_CODE_INTERNAL_ERROR
from ignition.model.lifecycle import LifecycleExecution, STATUS_FAILED
from ignition.service.resourcedriver import ResourceDriverProperties, LifecycleMessagingCapability
from ignition.service.requestqueue import Request, KafkaLifecycleRequestQueueService, RequestHandler, KafkaLifecycleConsumerFactory, KafkaRequestQueueHandler
from ignition.service.messaging import Envelope, Message, TopicsProperties, MessagingProperties, TopicConfigProperties
from kafka.structs import TopicPartition
from kafka import KafkaConsumer

MockRecord = collections.namedtuple('MockRecord', ['value', 'offset'])
logger = logging.getLogger(__name__)

# assert_not_called_with.from https://stackoverflow.com/a/54838760
def assert_not_called_with(self, *args, **kwargs):
    try:
        self.assert_called_with(*args, **kwargs)
    except AssertionError as e:
        return
    raise AssertionError('Expected %s to not have been called.' % self._format_mock_call_signature(args, kwargs))

MagicMock.assert_not_called_with = assert_not_called_with

class TestLifecycleRequestQueueService(unittest.TestCase):

    def setUp(self):
        self.resource_driver_config = ResourceDriverProperties()
        self.resource_driver_config.lifecycle_request_queue.topic.name = "lifecycle_request_queue"
        self.resource_driver_config.lifecycle_request_queue.failed_topic.name = "lifecycle_request_queue_failed"
        self.mock_postal_service = MagicMock()
        self.mock_lifecycle_messaging_service = MagicMock()
        self.mock_driver_files_manager = MagicMock()
        self.mock_messaging_config = MagicMock(connection_address='test:9092')

    def assert_request_posted(self, topic, request):
        self.mock_postal_service.post.assert_called_once()
        args, kwargs = self.mock_postal_service.post.call_args
        self.assertEqual(len(args), 1)
        envelope_arg = args[0]
        self.assertIsInstance(envelope_arg, Envelope)
        self.assertEqual(envelope_arg.address, topic)
        self.assertEqual(envelope_arg.message.content, json.dumps(request).encode())

    def assert_request_failed_not_posted(self, request_as_dict):
        request = Request.from_str_message(json.dumps(request_as_dict), self.resource_driver_config.lifecycle_request_queue.failed_topic.name, 0, 0)
        self.mock_postal_service.post.assert_not_called_with(Envelope(self.resource_driver_config.lifecycle_request_queue.failed_topic.name, request.as_message()), key=request_as_dict["request_id"])

    def assert_lifecycle_execution_equal(self, lifecycle_execution, expected_lifecycle_execution):
        self.assertEqual(lifecycle_execution.request_id, expected_lifecycle_execution.request_id)
        self.assertEqual(lifecycle_execution.status, expected_lifecycle_execution.status)
        self.assertEqual(lifecycle_execution.outputs, expected_lifecycle_execution.outputs)
        if expected_lifecycle_execution.failure_details is not None:
            self.assertEqual(lifecycle_execution.failure_details.failure_code, expected_lifecycle_execution.failure_details.failure_code)
            self.assertEqual(lifecycle_execution.failure_details.description, expected_lifecycle_execution.failure_details.description)

    def assert_lifecycle_execution_response_posted(self, expected_lifecycle_execution):
        self.mock_lifecycle_messaging_service.send_lifecycle_execution.assert_called_once()
        args, kwargs = self.mock_lifecycle_messaging_service.send_lifecycle_execution.call_args
        self.assertEqual(len(args), 1)
        lifecycle_execution = args[0]
        self.assertIsInstance(lifecycle_execution, LifecycleExecution)
        self.assert_lifecycle_execution_equal(lifecycle_execution, expected_lifecycle_execution)

    def test_init_without_lifecycle_messaging_service_throws_error(self):
        with self.assertRaises(ValueError) as context:
            KafkaLifecycleRequestQueueService(driver_files_manager=self.mock_driver_files_manager, postal_service=self.mock_postal_service, resource_driver_config=ResourceDriverProperties(), messaging_config=self.mock_messaging_config)
        self.assertEqual(str(context.exception), 'lifecycle_messaging_service argument not provided')

    def test_init_without_driver_files_manager_throws_error(self):
        with self.assertRaises(ValueError) as context:
            KafkaLifecycleRequestQueueService(lifecycle_messaging_service=self.mock_lifecycle_messaging_service, postal_service=self.mock_postal_service, resource_driver_config=ResourceDriverProperties(), messaging_config=self.mock_messaging_config)
        self.assertEqual(str(context.exception), 'driver_files_manager argument not provided')

    def test_init_without_messaging_config_throws_error(self):
        with self.assertRaises(ValueError) as context:
            KafkaLifecycleRequestQueueService(lifecycle_messaging_service=self.mock_lifecycle_messaging_service, driver_files_manager=self.mock_driver_files_manager, postal_service=self.mock_postal_service, resource_driver_config=ResourceDriverProperties())
        self.assertEqual(str(context.exception), 'messaging_config argument not provided')

    def test_init_without_resource_driver_config_throws_error(self):
        with self.assertRaises(ValueError) as context:
            KafkaLifecycleRequestQueueService(lifecycle_messaging_service=self.mock_lifecycle_messaging_service, driver_files_manager=self.mock_driver_files_manager, postal_service=self.mock_postal_service, messaging_config=self.mock_messaging_config)
        self.assertEqual(str(context.exception), 'resource_driver_config argument not provided')

    def test_init_without_postal_service_throws_error(self):
        with self.assertRaises(ValueError) as context:
            KafkaLifecycleRequestQueueService(lifecycle_messaging_service=self.mock_lifecycle_messaging_service, driver_files_manager=self.mock_driver_files_manager, resource_driver_config=ResourceDriverProperties(), messaging_config=self.mock_messaging_config)
        self.assertEqual(str(context.exception), 'postal_service argument not provided')

    def test_init_KafkaLifecycleConsumerFactory_fails_when_messaging_connection_address_not_set(self):
        messaging_conf = MessagingProperties()
        messaging_conf.connection_address = None
        resource_driver_config = ResourceDriverProperties()
        with self.assertRaises(ValueError) as context:
            KafkaLifecycleConsumerFactory(resource_driver_config, messaging_conf)

    def test_queue_lifecycle_request_missing_request_id(self):
        requestqueue_service = KafkaLifecycleRequestQueueService(lifecycle_messaging_service=self.mock_lifecycle_messaging_service, postal_service=self.mock_postal_service, driver_files_manager=self.mock_driver_files_manager, resource_driver_config=self.resource_driver_config, messaging_config=self.mock_messaging_config, lifecycle_consumer_factory=MagicMock())

        request = {
            "template": "template",
            "template_type": "test",
            "properties": {
                "prop1": "value1"
            },
            "system_properties": {
            },
            "request_properties": {
            },
            "associated_topology": [],
            'deployment_location': {
                "name": "dl1",
                "type": "Openstack",
                "properties": {
                    "prop1": "value1"
                }
            }
        }

        with self.assertRaises(ValueError) as context:
            requestqueue_service.queue_lifecycle_request(request)
        self.assertEqual(str(context.exception), 'Request must have a request_id')
        self.mock_postal_service.post.assert_not_called()

    def test_queue_lifecycle_request_null_request_id(self):
        requestqueue_service = KafkaLifecycleRequestQueueService(lifecycle_messaging_service=self.mock_lifecycle_messaging_service, postal_service=self.mock_postal_service, driver_files_manager=self.mock_driver_files_manager, resource_driver_config=self.resource_driver_config, messaging_config=self.mock_messaging_config, lifecycle_consumer_factory=MagicMock())

        request = {
            "request_id": None,
            "template": "template",
            "template_type": "test",
            "resource_properties": {
                "prop1": "value1"
            },
            "system_properties": {
            },
            "request_properties": {
            },
            "associated_topology": [],
            'deployment_location': {
                "name": "dl1",
                "type": "Openstack",
                "properties": {
                    "prop1": "value1"
                }
            }
        }

        with self.assertRaises(ValueError) as context:
            requestqueue_service.queue_lifecycle_request(request)
        self.assertEqual(str(context.exception), 'Request must have a request_id')
        self.mock_postal_service.post.assert_not_called()

    def test_lifecycle_requestqueue_process_request(self):
        mock_kafka_lifecycle_consumer = MagicMock()
        mock_kafka_lifecycle_consumer_factory = MagicMock()
        mock_kafka_lifecycle_consumer_factory.create_consumer.return_value = mock_kafka_lifecycle_consumer

        request_queue_service = KafkaLifecycleRequestQueueService(lifecycle_messaging_service=self.mock_lifecycle_messaging_service, postal_service=self.mock_postal_service, driver_files_manager=self.mock_driver_files_manager, resource_driver_config=self.resource_driver_config, messaging_config=self.mock_messaging_config, lifecycle_consumer_factory=mock_kafka_lifecycle_consumer_factory)

        mock_kafka_lifecycle_consumer.poll.return_value = {
            TopicPartition('lifecycle_request_queue', 0): [
                MockRecord(offset=0, value=json.JSONEncoder().encode({
                   "request_id": "a61dec25-fcdc-4281-b067-fa18681d65a7",
                   "lifecycle_name": "Configure",
                   "driver_files": "UEsDBBQACAgIAMd0alAAAAAAAAAAAAAAAAAJAAAALkRTX1N0b3Jl7ZlZbNxEGMe/b3ONnZRMQkqypdssTQNpm7RJyFmSsrlo06akIvfRbLxrN7Fw7O3au5s2DQqqOIVAHBLiEqjw1kpISEhQ8chRBEKqiLgkeIAXXpAQCCSeYLwzG6U5KvWpFfVf8v49883YnpmfZzReAMDOhFoHUAYABLjTfNhQRBzr5BOeyw5k9QF0mFHtqBGxLGPja3ny5MmTJ0+ebrCQG9lk3ffkydMtLHd+CAoPCV/ijiLuE569qg4VHhQeEr7EHUU5n/Bs4UQ4FR4UHhK+xF1MWig2HyjujGKHglR4UHjouprsydMtpdz0EQULTDi5ev/uvmd5YLNQnGXHwAE7krJjEcOKsMjnkZih205t7bfoy8rOyc0jRCbyFvnEwKyVGnAUJ2F3KvEJN3VccWYj4nyQXXjlXIkM61oqTEu6LNNRdFOLpyvrqsaKTI7opmqlOq2EqdoTqwKESEQK07KFhfqW1upgU9NidXChrraxsTrY3NC0uCiR0sq69t7pudNnFs4uPvIKb2Zm2oDCNe1/dX0zr9EDhp3s4j3geznTA99lekCS8/29R+S+MC1Osob1xxzdMu1hLW4zD9NCmzWiN2qZx+OaGx+JWkZizrTDtCiqGNGEoThah2EM6Gc0e9TR5h33bNy24k5XumCY0oStPaSxcnpS62al7VGdXc4tRlG6ULA1sPPuvbWNB+7vXt5yWyGVi+WSkaRu6xFDG0rpqjM7pthRzVR1c2ac9aXp6Cd1LS4V4W/SoKnMact3lJZR/zb/9s1qEVpBRhMR/VRCd07ze5T775Lo+2RSZY9zzFLdK6rpiL/cX0nIhJvfFdfYL8+Wq/x7JKqQQZs9Nc+pkfdL1JYGH2YDzqvWyw2EqtKQoUQ0g2c1y62EHpVGkrw3eWabfJAUYbU0GrXm5lh7bJ7d4e8i9DKZcu/dp9hOf0wz2e3TrSv3HyJkzI10qKqmkopQFecg3QNSRahWcEHAD/vY2nMYJkFjg38OnoFn4Tl4Dd6Bi/AefASfwWX4Ar6EK/AD/Ay/wh/wJ/wFf8O/SFDCfCxAP+7ECtyFtdiKB7AN27ETj2IfPoj9OIgncAqnUcEZjOEptNHBs/gYPo5P4dP4Ir6Ob+Cb+Ba+ix/gh3gJP8ZP8Cv8Gpf54/kyPB+7Gmf8cUNoxWvrm9oI2kDPA/LhGwPt9wXuiBUV316ydUdFVU19c1vHymCuGb/VKKXp4XiksclgkR7Eq1lko+7fdqccGGLFtPm1RGdIp3kuRyRdujwYCFAXIJ7cVcmSPsY4T+7eE5BpFiNYSif37ZcDNIfByqP3NsgyzWY082hLK4vmMm55tP0gi4L7vvGwVBmQ2Wx23QyehwtwCT5l9F2Bb+An+AV+h38YdzlYiKWMuu0YwB14D+7GvViNNdiELYy/+xiBPXgIe/EIo3AQh3EUx3Aco6gxBmdRxzhjMIkpnMdH8Rwj8Ql8Ep/HFxiNLzEaz+Pba9jrXcPexfXsJQfipmGZM7Cy2/R00yiLW5m7/+/Z/Pu/J0+e/sfC7O6B7k7YfIp299pBdkxnKsC1PwTgqj8Mb7oPAd76763/nuA/UEsHCOjISzueBAAABCAAAFBLAwQUAAgICADHdGpQAAAAAAAAAAAAAAAAIQAAAGNvbmZpZy9ob3N0X3ZhcnMvYXBhY2hlMS1pbnN0LnltbHXPsQqDMBAG4N2nCC5OqXQVnAql4Fg6BxMPcxiTkEssIr574+JSXO/7/+OOc170llAaENpRbNi2MR+chxAR6EYQFgh34ZM0qAR6tu9nIWVtWJLJxnQOJSg3g/A90Z9RGtyFkBa5Nzsr+jBmLzlenHJEJ1jznqjzNYw7Vn0ydtZ97Sv/QE800NYDLLVNxlRH4h0DqnhoB+tDg5rQjq11ZfEDUEsHCH4DIFWhAAAAAgEAAFBLAwQUAAgICADHdGpQAAAAAAAAAAAAAAAAIQAAAGNvbmZpZy9ob3N0X3ZhcnMvYXBhY2hlMi1pbnN0LnltbHXPsQqDMBAG4N2nCC5OqdBRcCqUgmPpHEw8zGFMQi6xiPjujYtLcb3v/487znnRW0JpQGhHsWHbxnxwHkJEoBtBWCDchU/SoBLo2b6fhZS1YUkmG9M5lKDcDML3RH9GaXAXQlrk3uys6MOYveR4ccoRnWDNe6LO1zDuWPXJ2Fn3ta/8Az3RQFsPsNQ2GVMdiXcMqOKhHawPDWpCO7bWlcUPUEsHCEC7XUKhAAAAAgEAAFBLAwQUAAgICADHdGpQAAAAAAAAAAAAAAAAEAAAAGNvbmZpZy9pbnZlbnRvcnmLTixITM5INYzlgjJ0M/OKS7i4oiFcI5i4EVgcAFBLBwiyd4xxHQAAAC4AAABQSwMEFAAICAgAx3RqUAAAAAAAAAAAAAAAABEAAABzY3JpcHRzLy5EU19TdG9yZe2YTU7DMBBGvwmpZImNlyx9hd7ArcIJegGUhJ9KKY6Udp8LcQjOwGnYALX8tYASkNi0FZ0nWS/KxI698XgMQOabegpYAAbJEh9GMGwDMnoSO8cxmvvpogqrdnyckyTOPUeFgEfcjcx/H1uFoiibUG7fmZe3p9fu/Xn2PV7/Gm8fRsbusMQat3VXNWUIjRxw4YqiKMrZwnRjLo87DUVRTpC4Pzja032yMJ7R+Zc+lna0p/tk4XcZndOGtrSjPd0nc9MSFh/CP++KF7G0o/2flqwoZ8NFko35//rn+l9RlH+M5MWimGNfEAyIudZt282uA5jNMTwEZOmy8AqfcUd7uk/Wg4CiHIsPUEsHCFjAJvEHAQAABBgAAFBLAwQUAAgICADHdGpQAAAAAAAAAAAAAAAAFgAAAHNjcmlwdHMvQ29uZmlndXJlLnlhbWyNkk1uwjAQhfc5xezY1DhFQpWyq/pzgF4ADfaEWE3syB5IEeLutZNASaGoq9jxm/e+8VgIkQmw2FABL86WZrP1lAFULnAoAFtUFT0+DN9FPFiTckm8pxB3G+SK/KpEldTvWIdUzBg+QxEXACfvVxNwXRNoKnFbMwTD1AsAol+DVsewhTYhHUCe52JUzlWkGpUlmpr0qqvIFnHTh01SPqhxu2kIqL6rk0M0KMY1QGDkWIXrQJbPf9vYUwGSWMmxbZmMgsBdzE9dyCu+CcWLp+gLlrqBQBtPip3f34P4LTpz7NDLruvk4QCtdy15NhTmyXiV4uB47CumBK7dD9kVN/XoyNS0dcr6ifaq6GXSWE1f8wsxxEsM/K/4W8WN0xFjlj8tl7NrvGetb8zmD76kkVUnUsHlYzgT3hvUzbr7cG+2f6in6V0/UrLDzV5aZ9k3UEsHCI6TIgVOAQAASQMAAFBLAwQUAAgICADHdGpQAAAAAAAAAAAAAAAAFAAAAHNjcmlwdHMvSW5zdGFsbC55YW1sdVI9T8MwEN35FU8RUqlECO3AYEYkJLZOLFVVufE1serYkX1JFX49TupCioSX+/Ddu3vPzmFlQwIfNrA05g6oXeAgIFtZ1rR6vNh1vDhQ6cbSgUKMKsk1+f1RlmP1uzSBYpZlOAURnTzhbmQXCEfnsRm4djZeAV6eBc61NoQt8i9k9w8RupFWIe/RToXLDLtXKIdgiFqsRt/SHNlTT5bTomvIjl0eSXjWtoKz0BdKy2lkqMkYAWORBxSK+sJ2xqAgLoswBKZGJVskwKdAvtflfGQSCb+aRC7EXlOU4OV5ihUZOQispkC2LCYH6Folmfbl2HnVcDwX5FvESsdF/DW71z9vE2Es68hjkb25zihYx6iIYVx5yqZI2z9t2yywIu+z3WJG5ZO8Pg5IHG/mJznEvwvGEo5cBCa1SaUkWXkwpObkmvgdxox131BLBwifDPH+SAEAAGgCAABQSwMEFAAICAgAx3RqUAAAAAAAAAAAAAAAABYAAABzY3JpcHRzL0ludGVncml0eS55YW1sZY5PSwMxFMTv+ymGXqqHXeg10IMIguBJvJeYvvyh6UvJe8H225tdXVS8TWYm83vjOA4j2J7J4JmVQk16w0vy5G4uE96qZUmaCg9ALKJiUElKq466E6xGqgdv3Rw82Syz+06uzINaGw39rVZOYrpYSY+R3AnJ40GUapKuBbUxJw69BkiknA02F4Ft183iVQpprhvY718HUatNhl/Lr3QpVfEVoPwQlglvUzaLAs4SzB8+F11vmJbORyT+B5tEj6Xp5BMf77ZruL3Hfo9x9wlQSwcI64IusM4AAABPAQAAUEsDBBQACAgIAMd0alAAAAAAAAAAAAAAAAASAAAAc2NyaXB0cy9TdGFydC55YW1sRYzLEcIwDETvqUIF4EM4ugAKCAVkFmfBMyGfsXRJ98jjALpIu/u0IYQuyIqFUe6GYp1I3tQ0CnakzP7S9tWDB9NWwYPq6gXLLOMTqdI3vJXuGnTW6IfIt3eg1mb5F9XRQ43LFE/phsGcLo3m9Atay/n9AVBLBwj87zwhcwAAALEAAABQSwMEFAAICAgAx3RqUAAAAAAAAAAAAAAAABEAAABzY3JpcHRzL1N0b3AueWFtbE2MwQ2EMAwE/1ThAsgDnimABijgZIIh0sElYv2hexwRwflj73p2nXONox/v4mnUlBuimKDwxJlDlK69d2+PSUIq3CkwtbJGOT4Lh0IPvEHMVcYX3g6i/1p6W8rghMo++yrNUFZDYWiW+bHvgpq9AFBLBwgLFqLCbwAAAKsAAABQSwMEFAAICAgAx3RqUAAAAAAAAAAAAAAAABkAAABzY3JpcHRzL2NvbmYvaHctc2l0ZS5jb25mbc8xC4MwEAXg3V+RoVMHsxcRRKUtCC0WukoaDwmYnFxOHST/vVU6FOyN731vuORpiEfVX9CzOJ6WZSAcgNiAj71haAYkDiGNxOceQBNQ1lrjxF6qNW/AKtOHsPkC9WjBcY3IQk6K5DzPcr90ysJ3UhIhVdiJw5Lds/xSNtXt3BTXOkhYq7jHboP56Bntf6m0Bu9XKjTal3HQRon8+TR9A1BLBwglaiIJoAAAAPcAAABQSwMEFAAICAgAx3RqUAAAAAAAAAAAAAAAABYAAABzY3JpcHRzL3NpdGUvLkRTX1N0b3Jl7Zg7DsIwEERnjQtLNC4p3XAAbmBFyQm4AAVXoPfRIdoRshRSUCWCeZL1Vop/aRxPANjwuF+ADCDBjTM+ktgWhK42ziGEEEKIfWOudNx2G0KIHTKfD4WudHMbnwc6dmMyXehKN7exX6AjnehMF7rSzc1Dyxg+jCsbE4oxhVih61evLMTfcHDl+fs/YTX/CyF+GIvjdRzwDgTLDq926+qG9UtA8J+Fp25soSvd3LoICLEVT1BLBwhqAIhtsgAAAAQYAABQSwMEFAAICAgAx3RqUAAAAAAAAAAAAAAAABcAAABzY3JpcHRzL3NpdGUvaW5kZXguaHRtbJXOQQqDMBQE0H1OEffS4P6TtfseoLRxMIFows+vIOLdjaQX6KxnHkNelmgVebwnq3QNSZAIOyLG1Ovj0JlTBktAecwMSFjnF8MhbGB9nmTaQJFpCH3StP8sP/wD1XabZfv8OodSOjL5lhtZG/fbC1BLBwiFIcA2bwAAALQAAABQSwECFAAUAAgICADHdGpQ6MhLO54EAAAEIAAACQAAAAAAAAAAAAAAAAAAAAAALkRTX1N0b3JlUEsBAhQAFAAICAgAx3RqUH4DIFWhAAAAAgEAACEAAAAAAAAAAAAAAAAA1QQAAGNvbmZpZy9ob3N0X3ZhcnMvYXBhY2hlMS1pbnN0LnltbFBLAQIUABQACAgIAMd0alBAu11CoQAAAAIBAAAhAAAAAAAAAAAAAAAAAMUFAABjb25maWcvaG9zdF92YXJzL2FwYWNoZTItaW5zdC55bWxQSwECFAAUAAgICADHdGpQsneMcR0AAAAuAAAAEAAAAAAAAAAAAAAAAAC1BgAAY29uZmlnL2ludmVudG9yeVBLAQIUABQACAgIAMd0alBYwCbxBwEAAAQYAAARAAAAAAAAAAAAAAAAABAHAABzY3JpcHRzLy5EU19TdG9yZVBLAQIUABQACAgIAMd0alCOkyIFTgEAAEkDAAAWAAAAAAAAAAAAAAAAAFYIAABzY3JpcHRzL0NvbmZpZ3VyZS55YW1sUEsBAhQAFAAICAgAx3RqUJ8M8f5IAQAAaAIAABQAAAAAAAAAAAAAAAAA6AkAAHNjcmlwdHMvSW5zdGFsbC55YW1sUEsBAhQAFAAICAgAx3RqUOuCLrDOAAAATwEAABYAAAAAAAAAAAAAAAAAcgsAAHNjcmlwdHMvSW50ZWdyaXR5LnlhbWxQSwECFAAUAAgICADHdGpQ/O88IXMAAACxAAAAEgAAAAAAAAAAAAAAAACEDAAAc2NyaXB0cy9TdGFydC55YW1sUEsBAhQAFAAICAgAx3RqUAsWosJvAAAAqwAAABEAAAAAAAAAAAAAAAAANw0AAHNjcmlwdHMvU3RvcC55YW1sUEsBAhQAFAAICAgAx3RqUCVqIgmgAAAA9wAAABkAAAAAAAAAAAAAAAAA5Q0AAHNjcmlwdHMvY29uZi9ody1zaXRlLmNvbmZQSwECFAAUAAgICADHdGpQagCIbbIAAAAEGAAAFgAAAAAAAAAAAAAAAADMDgAAc2NyaXB0cy9zaXRlLy5EU19TdG9yZVBLAQIUABQACAgIAMd0alCFIcA2bwAAALQAAAAXAAAAAAAAAAAAAAAAAMIPAABzY3JpcHRzL3NpdGUvaW5kZXguaHRtbFBLBQYAAAAADQANAGsDAAB2EAAAAAA=",
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
                   "resource_properties": {
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
                   "request_properties": {
                       "request_type": {
                           "type": "string",
                           "value": "testing"
                       }
                   },
                   "associated_topology": {},
                   "deployment_location": {
                      "resourceManager": "brent",
                      "name": "core1",
                      "type": "Openstack",
                      "properties": {
                      }
                   }
                }).encode())]
        }

        request_handler = MagicMock(RequestHandler)
        request_queue = request_queue_service.get_lifecycle_request_queue('test', request_handler)
        request_queue.process_request()

        request_handler.handle_request.assert_called_once()
        args, kwargs = request_handler.handle_request.call_args
        self.assertEqual(len(args), 1)
        request = args[0]
        self.assertIsInstance(request, dict)
        self.assertEqual(request["request_id"], "a61dec25-fcdc-4281-b067-fa18681d65a7")
        mock_kafka_lifecycle_consumer.commit.assert_called_once()

    def test_lifecycle_requestqueue_process_missing_request_id(self):
        mock_kafka_lifecycle_consumer = MagicMock()
        mock_kafka_lifecycle_consumer_factory = MagicMock()
        mock_kafka_lifecycle_consumer_factory.create_consumer.return_value = mock_kafka_lifecycle_consumer

        request_queue_service = KafkaLifecycleRequestQueueService(lifecycle_messaging_service=self.mock_lifecycle_messaging_service, postal_service=self.mock_postal_service, driver_files_manager=self.mock_driver_files_manager, resource_driver_config=self.resource_driver_config, messaging_config=self.mock_messaging_config, lifecycle_consumer_factory=mock_kafka_lifecycle_consumer_factory)

        request = {
           "lifecycle_name": "Configure",
           "driver_files": "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",
           "system_properties": {
           },
           "resource_properties": {
           },
           "request_properties": {
           },
           "associated_topology": [],
           "deployment_location": {
           }
        }

        mock_kafka_lifecycle_consumer.poll.return_value = {
            TopicPartition('lifecycle_request_queue', 0): [
                MockRecord(offset=0, value=json.JSONEncoder().encode(request).encode())]
        }

        request_handler = MagicMock(RequestHandler)
        request_queue = request_queue_service.get_lifecycle_request_queue('test', request_handler)
        request_queue.process_request()

        request_handler.handle_request.assert_not_called()
        mock_kafka_lifecycle_consumer.commit.assert_called_once()
        self.assert_request_posted(self.resource_driver_config.lifecycle_request_queue.failed_topic.name, request)

    def test_lifecycle_requestqueue_process_missing_lifecycle_name(self):
        mock_kafka_lifecycle_consumer = MagicMock()
        mock_kafka_lifecycle_consumer_factory = MagicMock()
        mock_kafka_lifecycle_consumer_factory.create_consumer.return_value = mock_kafka_lifecycle_consumer

        request_queue_service = KafkaLifecycleRequestQueueService(lifecycle_messaging_service=self.mock_lifecycle_messaging_service, postal_service=self.mock_postal_service, driver_files_manager=self.mock_driver_files_manager, resource_driver_config=self.resource_driver_config, messaging_config=self.mock_messaging_config, lifecycle_consumer_factory=mock_kafka_lifecycle_consumer_factory)

        request = {
           "request_id": "123",
           "driver_files": "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",
           "system_properties": {
           },
           "resource_properties": {
           },
           "request_properties": {
           },
           "associated_topology": [],
           "deployment_location": {
           }
        }

        mock_kafka_lifecycle_consumer.poll.return_value = {
            TopicPartition('lifecycle_request_queue', 0): [
                MockRecord(offset=0, value=json.JSONEncoder().encode(request).encode())]
        }

        request_handler = MagicMock(RequestHandler)
        request_queue = request_queue_service.get_lifecycle_request_queue('test', request_handler)
        request_queue.process_request()

        request_handler.handle_request.assert_not_called()
        mock_kafka_lifecycle_consumer.commit.assert_called_once()
        self.assert_lifecycle_execution_response_posted(LifecycleExecution('123', STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR,
            'Lifecycle request for partition 0 offset 0 is missing lifecycle_name.'), {}))
        self.assert_request_failed_not_posted(request)

    def test_lifecycle_requestqueue_process_missing_driver_files(self):
        mock_kafka_lifecycle_consumer = MagicMock()
        mock_kafka_lifecycle_consumer_factory = MagicMock()
        mock_kafka_lifecycle_consumer_factory.create_consumer.return_value = mock_kafka_lifecycle_consumer

        request_queue_service = KafkaLifecycleRequestQueueService(lifecycle_messaging_service=self.mock_lifecycle_messaging_service, postal_service=self.mock_postal_service, driver_files_manager=self.mock_driver_files_manager, resource_driver_config=self.resource_driver_config, messaging_config=self.mock_messaging_config, lifecycle_consumer_factory=mock_kafka_lifecycle_consumer_factory)

        request = {
           "request_id": "123",
           "lifecycle_name": "Configure",
           "system_properties": {
           },
           "resource_properties": {
           },
           "request_properties": {
           },
           "associated_topology": [],
           "deployment_location": {
           }
        }

        mock_kafka_lifecycle_consumer.poll.return_value = {
            TopicPartition('lifecycle_request_queue', 0): [
                MockRecord(offset=0, value=json.JSONEncoder().encode(request).encode())]
        }

        request_handler = MagicMock(RequestHandler)
        request_queue = request_queue_service.get_lifecycle_request_queue('test', request_handler)
        request_queue.process_request()

        request_handler.handle_request.assert_not_called()
        mock_kafka_lifecycle_consumer.commit.assert_called_once()

        self.assert_lifecycle_execution_response_posted(LifecycleExecution('123', STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR,
            'Lifecycle request for partition 0 offset 0 is missing driver_files.'), {}))
        self.assert_request_failed_not_posted(request)

    def test_lifecycle_requestqueue_process_missing_deployment_location(self):
        mock_kafka_lifecycle_consumer = MagicMock()
        mock_kafka_lifecycle_consumer_factory = MagicMock()
        mock_kafka_lifecycle_consumer_factory.create_consumer.return_value = mock_kafka_lifecycle_consumer

        request_queue_service = KafkaLifecycleRequestQueueService(lifecycle_messaging_service=self.mock_lifecycle_messaging_service, postal_service=self.mock_postal_service, driver_files_manager=self.mock_driver_files_manager, resource_driver_config=self.resource_driver_config, messaging_config=self.mock_messaging_config, lifecycle_consumer_factory=mock_kafka_lifecycle_consumer_factory)

        request = {
           "request_id": "123",
           "lifecycle_name": "Configure",
           "driver_files": "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",
           "system_properties": {
           },
           "resource_properties": {
           },
           "associated_topology": [],
           "request_properties": {
           }
        }
        mock_kafka_lifecycle_consumer.poll.return_value = {
            TopicPartition('lifecycle_request_queue', 0): [
                MockRecord(offset=0, value=json.JSONEncoder().encode(request).encode())]
        }

        request_handler = MagicMock(RequestHandler)
        request_queue = request_queue_service.get_lifecycle_request_queue('test', request_handler)
        request_queue.process_request()

        request_handler.handle_request.assert_not_called()
        mock_kafka_lifecycle_consumer.commit.assert_called_once()

        self.assert_lifecycle_execution_response_posted(LifecycleExecution('123', STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR,
            'Lifecycle request for partition 0 offset 0 is missing deployment_location.'), {}))
        self.assert_request_failed_not_posted(request)

    def test_lifecycle_requestqueue_process_missing_request_properties(self):
        mock_kafka_lifecycle_consumer = MagicMock()
        mock_kafka_lifecycle_consumer_factory = MagicMock()
        mock_kafka_lifecycle_consumer_factory.create_consumer.return_value = mock_kafka_lifecycle_consumer

        request_queue_service = KafkaLifecycleRequestQueueService(lifecycle_messaging_service=self.mock_lifecycle_messaging_service, postal_service=self.mock_postal_service, driver_files_manager=self.mock_driver_files_manager, resource_driver_config=self.resource_driver_config, messaging_config=self.mock_messaging_config, lifecycle_consumer_factory=mock_kafka_lifecycle_consumer_factory)

        request = {
           "request_id": "123",
           "lifecycle_name": "Start",
           "driver_files": "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",
           "system_properties": {
           },
           "resource_properties": {
           },
           "associated_topology": [],
           "deployment_location": {
           }
        }

        mock_kafka_lifecycle_consumer.poll.return_value = {
            TopicPartition('lifecycle_request_queue', 0): [
                MockRecord(offset=0, value=json.JSONEncoder().encode(request).encode())]
        }

        request_handler = MagicMock(RequestHandler)
        request_queue = request_queue_service.get_lifecycle_request_queue('test', request_handler)
        request_queue.process_request()

        request_handler.handle_request.assert_not_called()
        mock_kafka_lifecycle_consumer.commit.assert_called_once()
        self.assert_lifecycle_execution_response_posted(LifecycleExecution('123', STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR,
            'Lifecycle request for partition 0 offset 0 is missing request_properties.'), {}))
        self.assert_request_failed_not_posted(request)

    def test_lifecycle_requestqueue_process_missing_resource_properties(self):
        mock_kafka_lifecycle_consumer = MagicMock()
        mock_kafka_lifecycle_consumer_factory = MagicMock()
        mock_kafka_lifecycle_consumer_factory.create_consumer.return_value = mock_kafka_lifecycle_consumer

        request_queue_service = KafkaLifecycleRequestQueueService(lifecycle_messaging_service=self.mock_lifecycle_messaging_service, postal_service=self.mock_postal_service, driver_files_manager=self.mock_driver_files_manager, resource_driver_config=self.resource_driver_config, messaging_config=self.mock_messaging_config, lifecycle_consumer_factory=mock_kafka_lifecycle_consumer_factory)

        request = {
           "request_id": "123",
           "lifecycle_name": "Start",
           "driver_files": "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",
           "system_properties": {
           },
           "request_properties": {
           },
           "associated_topology": [],
           "deployment_location": {
           }
        }

        mock_kafka_lifecycle_consumer.poll.return_value = {
            TopicPartition('lifecycle_request_queue', 0): [
                MockRecord(offset=0, value=json.JSONEncoder().encode(request).encode())]
        }

        request_handler = MagicMock(RequestHandler)
        request_queue = request_queue_service.get_lifecycle_request_queue('test', request_handler)
        request_queue.process_request()

        request_handler.handle_request.assert_not_called()
        mock_kafka_lifecycle_consumer.commit.assert_called_once()
        self.assert_lifecycle_execution_response_posted(LifecycleExecution('123', STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR,
            'Lifecycle request for partition 0 offset 0 is missing resource_properties.'), {}))
        self.assert_request_failed_not_posted(request)
    
    def test_lifecycle_requestqueue_process_missing_system_properties(self):
        mock_kafka_lifecycle_consumer = MagicMock()
        mock_kafka_lifecycle_consumer_factory = MagicMock()
        mock_kafka_lifecycle_consumer_factory.create_consumer.return_value = mock_kafka_lifecycle_consumer

        request_queue_service = KafkaLifecycleRequestQueueService(lifecycle_messaging_service=self.mock_lifecycle_messaging_service, postal_service=self.mock_postal_service, driver_files_manager=self.mock_driver_files_manager, resource_driver_config=self.resource_driver_config, messaging_config=self.mock_messaging_config, lifecycle_consumer_factory=mock_kafka_lifecycle_consumer_factory)

        request = {
           "request_id": "123",
           "lifecycle_name": "Start",
           "driver_files": "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",
           "resource_properties": {
           },
           "request_properties": {
           },
           "associated_topology": [],
           "deployment_location": {
           }
        }

        mock_kafka_lifecycle_consumer.poll.return_value = {
            TopicPartition('lifecycle_request_queue', 0): [
                MockRecord(offset=0, value=json.JSONEncoder().encode(request).encode())]
        }

        request_handler = MagicMock(RequestHandler)
        request_queue = request_queue_service.get_lifecycle_request_queue('test', request_handler)
        request_queue.process_request()

        request_handler.handle_request.assert_not_called()
        mock_kafka_lifecycle_consumer.commit.assert_called_once()
        self.assert_lifecycle_execution_response_posted(LifecycleExecution('123', STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR,
            'Lifecycle request for partition 0 offset 0 is missing system_properties.'), {}))
        self.assert_request_failed_not_posted(request)

    def test_lifecycle_requestqueue_process_missing_associated_topology(self):
        mock_kafka_lifecycle_consumer = MagicMock()
        mock_kafka_lifecycle_consumer_factory = MagicMock()
        mock_kafka_lifecycle_consumer_factory.create_consumer.return_value = mock_kafka_lifecycle_consumer

        request_queue_service = KafkaLifecycleRequestQueueService(lifecycle_messaging_service=self.mock_lifecycle_messaging_service, postal_service=self.mock_postal_service, driver_files_manager=self.mock_driver_files_manager, resource_driver_config=self.resource_driver_config, messaging_config=self.mock_messaging_config, lifecycle_consumer_factory=mock_kafka_lifecycle_consumer_factory)

        request = {
           "request_id": "123",
           "lifecycle_name": "Start",
           "driver_files": "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",
           "resource_properties": {
           },
           "request_properties": {
           },
           "system_properties": {
           },
           "deployment_location": {
           }
        }

        mock_kafka_lifecycle_consumer.poll.return_value = {
            TopicPartition('lifecycle_request_queue', 0): [
                MockRecord(offset=0, value=json.JSONEncoder().encode(request).encode())]
        }

        request_handler = MagicMock(RequestHandler)
        request_queue = request_queue_service.get_lifecycle_request_queue('test', request_handler)
        request_queue.process_request()

        request_handler.handle_request.assert_not_called()
        mock_kafka_lifecycle_consumer.commit.assert_called_once()
        self.assert_lifecycle_execution_response_posted(LifecycleExecution('123', STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR,
            'Lifecycle request for partition 0 offset 0 is missing associated_topology.'), {}))
        self.assert_request_failed_not_posted(request)