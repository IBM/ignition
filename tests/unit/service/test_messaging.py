import unittest
import time
from unittest.mock import patch, MagicMock, call
from ignition.service.messaging import PostalService, KafkaDeliveryService, KafkaInboxService, Envelope, Message


class TestPostalService(unittest.TestCase):

    def setUp(self):
        self.mock_delivery_service = MagicMock()

    def test_init_without_delivery_service_throws_error(self):
        with self.assertRaises(ValueError) as context:
            PostalService()
        self.assertEqual(str(context.exception), 'delivery_service argument not provided')

    def test_post_sends_envelope_to_delivery_service(self):
        postal_service = PostalService(delivery_service=self.mock_delivery_service)
        test_envelope = Envelope('test', Message('test message'))
        postal_service.post(test_envelope)
        self.mock_delivery_service.deliver.assert_called_once_with(test_envelope)

    def test_post_throws_error_when_envelope_is_none(self):
        postal_service = PostalService(delivery_service=self.mock_delivery_service)
        with self.assertRaises(ValueError) as context:
            postal_service.post(None)
        self.assertEqual(str(context.exception), 'An envelope must be passed to post a message')


class TestKafkaDeliveryService(unittest.TestCase):

    def setUp(self):
        self.mock_messaging_config = MagicMock(connection_address='test:9092', api_version_auto_timeout_ms=5000)

    def test_init_without_messaging_config_throws_error(self):
        with self.assertRaises(ValueError) as context:
            KafkaDeliveryService()
        self.assertEqual(str(context.exception), 'messaging_config argument not provided')

    def test_init_without_bootstrap_servers_throws_error(self):
        mock_messaging_config = MagicMock(connection_address=None)
        with self.assertRaises(ValueError) as context:
            KafkaDeliveryService(messaging_config=mock_messaging_config)
        self.assertEqual(str(context.exception), 'connection_address not set on messaging_config')

    @patch('ignition.service.messaging.KafkaProducer')
    def test_deliver(self, mock_kafka_producer_init):
        delivery_service = KafkaDeliveryService(messaging_config=self.mock_messaging_config)
        test_envelope = Envelope('test_topic', Message('test message'))
        delivery_service.deliver(test_envelope)
        mock_kafka_producer_init.assert_called_once_with(bootstrap_servers='test:9092', api_version_auto_timeout_ms=5000)
        self.assertEqual(delivery_service.producer, mock_kafka_producer_init.return_value)
        mock_kafka_producer = mock_kafka_producer_init.return_value
        mock_kafka_producer.send.assert_called_once_with('test_topic', b'test message')
        mock_kafka_producer.flush.assert_called_once()

    @patch('ignition.service.messaging.KafkaProducer')
    def test_deliver_throws_error_when_envelope_is_none(self, mock_kafka_producer_init):
        delivery_service = KafkaDeliveryService(messaging_config=self.mock_messaging_config)
        with self.assertRaises(ValueError) as context:
            delivery_service.deliver(None)
        self.assertEqual(str(context.exception), 'An envelope must be passed to deliver a message')


class TestKafkaInboxService(unittest.TestCase):

    def setUp(self):
        self.mock_messaging_config = MagicMock(connection_address='test:9092', api_version_auto_timeout_ms=5000)

    def test_init_without_messaging_config_throws_error(self):
        with self.assertRaises(ValueError) as context:
            KafkaInboxService()
        self.assertEqual(str(context.exception), 'messaging_config argument not provided')

    def test_init_without_bootstrap_servers_throws_error(self):
        mock_messaging_config = MagicMock(connection_address=None)
        with self.assertRaises(ValueError) as context:
            KafkaInboxService(messaging_config=mock_messaging_config)
        self.assertEqual(str(context.exception), 'connection_address not set on messaging_config')

    @patch('ignition.service.messaging.KafkaInboxThread')
    def test_watch_inbox_starts_thread(self, mock_kafka_inbox_thread_init):
        inbox_service = KafkaInboxService(messaging_config=self.mock_messaging_config)
        mock_read_inbox_func = MagicMock()
        inbox_service.watch_inbox('test_group', 'test_topic', mock_read_inbox_func)
        mock_kafka_inbox_thread_init.assert_called_once_with('test:9092', 5000, 'test_group', 'test_topic', mock_read_inbox_func, inbox_service._KafkaInboxService__thread_exit_func)
        mock_kafka_inbox_thread_init.return_value.start.assert_called_once()

    @patch('ignition.service.messaging.KafkaConsumer')
    def test_watch_inbox_thread_inits_consumer(self, mock_kafka_consumer_init):
        inbox_service = KafkaInboxService(messaging_config=self.mock_messaging_config)
        mock_read_inbox_func = MagicMock()
        inbox_service.watch_inbox('test_group', 'test_topic', mock_read_inbox_func)
        mock_kafka_consumer_init.assert_called_once_with('test_topic', bootstrap_servers='test:9092', group_id='test_group', enable_auto_commit=False)

    @patch('ignition.service.messaging.KafkaConsumer')
    def test_watch_inbox_thread_inits_consumer(self, mock_kafka_consumer_init):
        mock_kafka_consumer = mock_kafka_consumer_init.return_value
        mock_record_1 = MagicMock()
        mock_record_2 = MagicMock()
        infinite_iter_stop = False
        infinite_iter_has_stopped = False
        ready_for_second_message = False
        second_message_sent = False

        def build_iter():
            def iter():
                yield mock_record_1
                while not infinite_iter_stop:
                    if ready_for_second_message:
                        yield mock_record_2
                        break
                while not infinite_iter_stop:
                    time.sleep(0.001)
                infinite_iter_has_stopped = True
            return iter
        mock_kafka_consumer.__iter__.side_effect = build_iter()
        inbox_service = KafkaInboxService(messaging_config=self.mock_messaging_config)
        mock_read_inbox_func = MagicMock()
        inbox_service.watch_inbox('test_group', 'test_topic', mock_read_inbox_func)
        time.sleep(0.01)
        try:
            self.assertEqual(len(inbox_service.active_threads), 1)
            mock_kafka_consumer_init.assert_called_once_with('test_topic', bootstrap_servers='test:9092', api_version_auto_timeout_ms=5000, group_id='test_group', enable_auto_commit=False)
            mock_kafka_consumer.__iter__.assert_called_once()
            mock_record_1.value.decode.assert_called_once_with('utf-8')
            mock_record_2.value.decode.assert_not_called()
            mock_read_inbox_func.assert_called_once_with(mock_record_1.value.decode.return_value)
            mock_kafka_consumer.commit.assert_called_once()
            ready_for_second_message = True
            time.sleep(0.01)
            mock_record_2.value.decode.assert_called_once_with('utf-8')
            mock_read_inbox_func.assert_called_with(mock_record_2.value.decode.return_value)
            mock_kafka_consumer.commit.assert_has_calls([call(), call()])
        finally:
            infinite_iter_stop = True
        time.sleep(1)
        mock_kafka_consumer.close.assert_called_once()
        self.assertEqual(len(inbox_service.active_threads), 0)

    @patch('ignition.service.messaging._thread')
    @patch('ignition.service.messaging.KafkaConsumer')
    def test_watch_inbox_thread_calls_exit_func_on_error(self, mock_kafka_consumer_init, mock_thread):
        mock_kafka_consumer = mock_kafka_consumer_init.return_value
        mock_record_1 = MagicMock()
        infinite_iter_stop = False
        ready_for_message = True
        def build_iter():
            def iter():
                while not infinite_iter_stop:
                    if ready_for_message:
                        yield mock_record_1
                        break
            return iter
        mock_kafka_consumer.__iter__.side_effect = build_iter()
        inbox_service = KafkaInboxService(test_mode=True, messaging_config=self.mock_messaging_config)
        mock_read_inbox_func = MagicMock()
        mock_read_inbox_func.side_effect = ValueError('Test error')
        self.assertFalse(inbox_service.exited)
        inbox_service.watch_inbox('test_group', 'test_topic', mock_read_inbox_func)
        ready_for_message = True
        time.sleep(0.03)
        ## Indicates the exit func on inbox_service was called when in "test_mode"
        self.assertTrue(inbox_service.exited)
        mock_kafka_consumer.commit.assert_not_called()