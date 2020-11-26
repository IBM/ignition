import logging
import re
from ignition.service.framework import ServiceRegistration
from ignition.boot.config import BootProperties
from ignition.boot.configurators.utils import validate_no_service_with_capability_exists
from ignition.service.progress_events import (ProgressEventLogWriterCapability, ProgressEventLogWriterService, 
                                                YAMLProgressEventLogSerializer, ProgressEventLogSerializerCapability)

logger = logging.getLogger(__name__)

class ProgressEventLogConfigurator:

    def __init__(self):
        pass

    def configure(self, configuration, service_register):
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        if auto_config.progress_event_log.service_enabled is True:
            logger.debug('Bootstrapping Progress Event Log Writer Service')
            validate_no_service_with_capability_exists(service_register, ProgressEventLogWriterCapability, 'ProgressEventLogWriter', 'bootstrap.progress_event_log.service_enabled')
            service_register.add_service(ServiceRegistration(ProgressEventLogWriterService, serializer_service=ProgressEventLogSerializerCapability))
        else:
            logger.debug('Disabled: bootstrapped Progress Event Log Writer Service')

        if auto_config.progress_event_log.serializer_service_enabled is True:
            logger.debug('Bootstrapping Progress Event Log Serializer Service')
            validate_no_service_with_capability_exists(service_register, ProgressEventLogSerializerCapability, 'ProgressEventLogSerializer', 'bootstrap.progress_event_log.serializer_service_enabled')
            service_register.add_service(ServiceRegistration(YAMLProgressEventLogSerializer))
        else:
            logger.debug('Disabled: bootstrapped Progress Event Log Serializer Service')
        