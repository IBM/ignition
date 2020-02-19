from ignition.service.framework import Service, Capability, interface
from ignition.service.config import ConfigurationPropertiesGroup
from ignition.service.api import BaseController
from ignition.service.health import HealthStatus
from ignition.service.logging import LoggerUpdateRequest
import ignition.openapi as openapi
import pathlib
import os
import logging

# Deliberately uppercase so we don't get mixed up with all the other references to "logger" in this module
LOGGER = logging.getLogger(__name__)

# Grabs the __init__.py from the openapi package then takes it's parent, the openapi directory itself
openapi_path = str(pathlib.Path(openapi.__file__).parent.resolve())

class ManagementApi(Capability):
    
    @interface
    def health(self):
        pass

    @interface
    def get_logger(self):
        pass

class Management(Capability):
    
    @interface
    def check_health(self):
        pass

    @interface
    def get_logger_details(self, logger_name):
        pass

class ManagementProperties(ConfigurationPropertiesGroup, Service, Capability):
    def __init__(self):
        super().__init__('management')
        self.api_spec = os.path.join(openapi_path, 'management.yaml')

class ManagementApiService(Service, ManagementApi, BaseController):
    """
    Out-of-the-box controller for management APIs
    """

    def __init__(self, service):
        if service is None:
            raise ValueError('No management service instance provided')
        self.service = service

    def health(self):
        LOGGER.debug('Checking application health')
        health_report = self.service.check_health()
        status = 200
        if health_report.diagnosis_is_unhealthy:
            status = 503
        response = health_report.dict_copy()
        return (response, status)

    def get_logger(self, **kwarg):
        logger_name = self.get_required_param(kwarg, 'logger')
        LOGGER.debug('Retrieving logger with name %s', logger_name)
        logger_details = self.service.get_logger_details(logger_name)
        response = logger_details.dict_copy()
        return response, 200

    def update_logger(self, **kwarg):
        logger_name = self.get_required_param(kwarg, 'logger')
        body = self.get_body(kwarg)
        LOGGER.debug('Updating logger with name %s: %s', logger_name, body)
        self.service.update_logger_details(logger_name, body)
        return None, 200

class ManagementService(Service, Management):
    """
    Out-of-the-box service for management functionality
    """

    def __init__(self, health_checker, log_manager):
        if health_checker is None:
            raise ValueError('No health_checker instance provided')
        self.health_checker = health_checker
        if log_manager is None:
            raise ValueError('No log_manager instance provided')
        self.log_manager = log_manager

    def check_health(self):
        return self.health_checker.perform_checkup()

    def get_logger_details(self, logger_name):
        return self.log_manager.get_logger_details(logger_name)

    def update_logger_details(self, logger_name, raw_update_request):
        update_request = LoggerUpdateRequest(level=raw_update_request.get('level', None))
        self.log_manager.update_logger_details(logger_name, update_request)