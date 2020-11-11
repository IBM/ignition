import unittest
from unittest.mock import patch
from ignition.service.progress_events import ProgressEventLogWriterService, YAMLProgressEventLogSerializer
from ignition.model.progress_events import ResourceTransitionProgressEvent, BASE_EVENT_TYPE

class TestEvent(ResourceTransitionProgressEvent):
    progress_event_type = 'TestEvent'

    def __init__(self, extra_details=None):
        super().__init__()
        self.extra_details = extra_details or {}

    def _details(self):
        return self.extra_details

class TestProgressEventLogWriterService(unittest.TestCase):
    
    def setUp(self):
        self.service = ProgressEventLogWriterService(serializer_service=YAMLProgressEventLogSerializer())

    @patch('ignition.service.progress_events.logger')
    def test_add_logs_flat_format(self, mock_logger):
        event = TestEvent(extra_details={'A': 123})
        self.service.add(event)
        expected_str = '---[{0}]---'.format(BASE_EVENT_TYPE)
        expected_str += '\neventType: {0}'.format(BASE_EVENT_TYPE)
        expected_str += '\nprogressEventType: TestEvent'
        expected_str += '\ndetails:'
        expected_str += '\n  A: 123\n'
        mock_logger.info.assert_called_once_with(expected_str)

    @patch('ignition.service.progress_events.logger')
    @patch('ignition.service.progress_events.log_type')
    def test_add_logs_logstash_format(self, mock_log_type, mock_logger):
        mock_log_type.lower.return_value = 'logstash'
        event = TestEvent(extra_details={'A': 123})
        self.service.add(event)
        expected_str = 'eventType: {0}'.format(BASE_EVENT_TYPE)
        expected_str += '\nprogressEventType: TestEvent'
        expected_str += '\ndetails:'
        expected_str += '\n  A: 123\n'
        mock_logger.info.assert_called_once_with(expected_str)

    def test_add_invalid_event(self):
        with self.assertRaises(ValueError) as context:
            self.service.add({'Invalid': 'Because it does not subclass ResourceTransitionProgressEvent'})
        self.assertEqual(str(context.exception), 'Cannot add event of type "dict" because it must be a subtype of "ResourceTransitionProgressEvent"')
