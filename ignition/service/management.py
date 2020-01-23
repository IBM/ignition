from ignition.service.framework import Service, Capability, interface
from ignition.service.config import ConfigurationPropertiesGroup
from ignition.service.api import BaseController
from ignition.service.health import HealthStatus
import ignition.openapi as openapi
import pathlib
import os
import logging

logger = logging.getLogger(__name__)

# Grabs the __init__.py from the openapi package then takes it's parent, the openapi directory itself
openapi_path = str(pathlib.Path(openapi.__file__).parent.resolve())

class ManagementApi(Capability):
    
    @interface
    def health(self):
        pass

class Management(Capability):
    
    @interface
    def check_health(self):
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
        logger.debug('Checking application health')
        health_report = self.service.check_health()
        status = 200
        if health_report.diagnosis_is_unhealthy:
            status = 503
        response = health_report.dict_copy()
        return (response, status)
   

class ManagementService(Service, Management):
    """
    Out-of-the-box service for management functionality
    """

    def __init__(self, health_checker):
        if health_checker is None:
            raise ValueError('No health_checker instance provided')
        self.health_checker = health_checker

    def check_health(self):
        return self.health_checker.perform_checkup()