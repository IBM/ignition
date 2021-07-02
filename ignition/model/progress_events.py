from collections import OrderedDict

BASE_EVENT_TYPE = 'ResourceTransitionProgressEvent'

class ResourceTransitionProgressEvent:
    """
    Base class for all events to be submitted during the execution of a Resource lifecycle transition/operation
    """

    def __init__(self, progress_event_type = None):
        if progress_event_type is None:
            if not hasattr(self, 'progress_event_type'):
                raise ValueError('Must pass "progress_event_type" to constructor or have an existing attribute with this name on "{0}"'.format(self.__class__.__name__))
        else:
            self.progress_event_type = progress_event_type

    def _details(self):
        return {}

    def to_dict(self):
        return OrderedDict({
            'eventType': BASE_EVENT_TYPE,
            'progressEventType': self.progress_event_type,
            'details': self._details()
        })
