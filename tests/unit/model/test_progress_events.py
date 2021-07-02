import unittest
from ignition.model.progress_events import ResourceTransitionProgressEvent
from collections import OrderedDict

class TestSubEvent(ResourceTransitionProgressEvent):
    progress_event_type = 'TestSubEvent'

    def __init__(self, extra_details=None):
        super().__init__()
        self.extra_details = extra_details or {}

    def _details(self):
        return self.extra_details

class TestResourceTransitionProgressEvent(unittest.TestCase):

    def test_init(self):
        event = ResourceTransitionProgressEvent(progress_event_type='TestEvent')
        self.assertEqual(event.progress_event_type, 'TestEvent')

    def test_init_with_class_attr_for_progress_event_type(self):
        event = TestSubEvent()
        self.assertEqual(event.progress_event_type, 'TestSubEvent')

    def test_init_without_progress_event_type_raises_error(self):
        with self.assertRaises(ValueError) as context:
            ResourceTransitionProgressEvent()
        self.assertEqual(str(context.exception), 'Must pass "progress_event_type" to constructor or have an existing attribute with this name on "ResourceTransitionProgressEvent"')

    def test_to_dict(self):
        event = ResourceTransitionProgressEvent(progress_event_type='TestEvent')
        to_dict_result = event.to_dict()
        self.assertIsInstance(to_dict_result, OrderedDict)
        self.assertEqual(to_dict_result['eventType'], 'ResourceTransitionProgressEvent')
        self.assertEqual(to_dict_result['progressEventType'], 'TestEvent')
        self.assertEqual(to_dict_result['details'], {})

    def test_to_dict_order(self):
        event = ResourceTransitionProgressEvent(progress_event_type='TestEvent')
        to_dict_result = event.to_dict()
        self.assertIsInstance(to_dict_result, OrderedDict)
        self.assertEqual(list(to_dict_result.keys()), ['eventType', 'progressEventType', 'details'])

    def test_to_dict_with_details(self):
        event = TestSubEvent(extra_details={'a': 'A', 'b': 'B'})
        to_dict_result = event.to_dict()
        self.assertIsInstance(to_dict_result, OrderedDict)
        self.assertEqual(to_dict_result['eventType'], 'ResourceTransitionProgressEvent')
        self.assertEqual(to_dict_result['progressEventType'], 'TestSubEvent')
        self.assertEqual(to_dict_result['details'], {
            'a': 'A',
            'b': 'B'
        })
