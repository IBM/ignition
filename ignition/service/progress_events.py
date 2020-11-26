import logging
import yaml
from collections import OrderedDict
from ignition.service.framework import Service, Capability, interface
from ignition.service.logging import log_type
from ignition.model.progress_events import ResourceTransitionProgressEvent, BASE_EVENT_TYPE

# Allow OrderedDict to be dumped as YAML
yaml.add_representer(OrderedDict, lambda dumper, data: dumper.represent_mapping('tag:yaml.org,2002:map', data.items()))
yaml.add_representer(OrderedDict, lambda dumper, data: dumper.represent_mapping('tag:yaml.org,2002:map', data.items()), Dumper=yaml.SafeDumper)

logger = logging.getLogger(__name__)

class ProgressEventLogSerializerCapability(Capability):

    @interface
    def serialize(self, event):
        pass

class ProgressEventLogWriterCapability(Capability):

    @interface
    def add(self, event):
        pass

class YAMLProgressEventLogSerializer(Service, ProgressEventLogSerializerCapability):

    def serialize(self, event):
        data = event.to_dict()
        return yaml.safe_dump(data)

class ProgressEventLogWriterService(Service, ProgressEventLogWriterCapability):
    """
    Service to report ResourceTransitionProgressEvents
    """
    def __init__(self, serializer_service):
        self.serializer_service = serializer_service

    def add(self, event):
        if not isinstance(event, ResourceTransitionProgressEvent):
            raise ValueError('Cannot add event of type "{0}" because it must be a subtype of "{1}"'.format(event.__class__.__name__, ResourceTransitionProgressEvent.__name__))
        logger.info(self.to_loggable(event))
    
    def _make_yaml_str(self, data):
        return yaml.safe_dump(data)

    def to_loggable(self, event):
        data_str = self.serializer_service.serialize(event)
        if log_type.lower() == 'flat':
            # For flat logging we add start separator for clarity
            new_data_str = '---[{0}]---\n'.format(BASE_EVENT_TYPE)
            new_data_str += data_str
            return new_data_str
        else:
            return data_str