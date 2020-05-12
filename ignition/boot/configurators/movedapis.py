import ignition.openapi as openapi
import pathlib
import os
import logging
from ignition.boot.config import BootProperties

logger = logging.getLogger(__name__)

# Grabs the __init__.py from the openapi package then takes it's parent, the openapi directory itself
openapi_path = str(pathlib.Path(openapi.__file__).parent.resolve())

class EmptyResolver:
    pass

class MovedApisConfigurator:

    def __init__(self):
        pass

    def configure(self, configuration, service_register, service_instances, api_register):
        self.__configure_api_spec(configuration, service_register, service_instances, api_register)

    def __configure_api_spec(self, configuration, service_register, service_instances, api_register):
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        if auto_config.movedapis.infrastructure_enabled is True:
            logger.debug('Bootstrapping Moved Infrastructure API')
            api_register.register_api(os.path.join(openapi_path, 'moved-infrastructure.yaml'), resolver=EmptyResolver())
        else:
            logger.debug('Disabled: bootstrapped Moved Infrastructure API')
        if auto_config.movedapis.lifecycle_enabled is True:
            logger.debug('Bootstrapping Moved Lifecycle API')
            api_register.register_api(os.path.join(openapi_path, 'moved-lifecycle.yaml'), resolver=EmptyResolver())
        else:
            logger.debug('Disabled: bootstrapped Moved Lifecycle API')