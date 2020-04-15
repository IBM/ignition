import logging
import re
from ignition.service.framework import ServiceRegistration
from ignition.boot.config import BootProperties
from ignition.boot.configurators.utils import validate_no_service_with_capability_exists
from ignition.service.templating import TemplatingCapability, Jinja2TemplatingService, ResourceTemplateContextCapability, ResourceTemplateContextService

logger = logging.getLogger(__name__)

class TemplatingConfigurator:

    def __init__(self):
        pass

    def configure(self, configuration, service_register):
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        if auto_config.templating.service_enabled is True:
            logger.debug('Bootstrapping Templating Service')
            validate_no_service_with_capability_exists(service_register, TemplatingCapability, 'Templating', 'bootstrap.templating.service_enabled')
            service_register.add_service(ServiceRegistration(Jinja2TemplatingService))
        else:
            logger.debug('Disabled: bootstrapped Templating Service')
        if auto_config.templating.resource_context_service_enabled is True:
            logger.debug('Bootstrapping Resource Template Context Service')
            validate_no_service_with_capability_exists(service_register, ResourceTemplateContextCapability, 'Resource Template Context', 'bootstrap.templating.resource_context_service_enabled')
            service_register.add_service(ServiceRegistration(ResourceTemplateContextService))
        else:
            logger.debug('Disabled: bootstrapped Resource Template Context Service')