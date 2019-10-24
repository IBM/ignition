from ignition.service.framework import Capability, Service, interface
from ignition.service.config import ConfigurationPropertiesGroup
from ignition.service.api import BaseController
from ignition.model.infrastructure import InfrastructureTask, infrastructure_task_dict, infrastructure_find_response_dict, STATUS_COMPLETE, STATUS_FAILED
from ignition.service.messaging import Message, Envelope, JsonContent, TopicCreator
from ignition.api.exceptions import ApiException
from ignition.service.logging import logging_context
import logging
import pathlib
import os
import ignition.openapi as openapi

logger = logging.getLogger(__name__)

# Grabs the __init__.py from the openapi package then takes it's parent, the openapi directory itself
openapi_path = str(pathlib.Path(openapi.__file__).parent.resolve())


class InfrastructureNotFoundError(ApiException):
    status_code = 400


class InvalidInfrastructureTemplateError(ApiException):
    status_code = 400


class InfrastructureProperties(ConfigurationPropertiesGroup, Service, Capability):
    def __init__(self):
        super().__init__('infrastructure')
        self.api_spec = os.path.join(openapi_path, 'vim_infrastructure.yaml')
        self.async_messaging_enabled = True


class InfrastructureDriverCapability(Capability):
    """
    The InfrastructureDriver is the expected integration point for VIM Drivers to implement communication with the VIM on an Infrastructure request
    """
    @interface
    def create_infrastructure(self, template, template_type, inputs, deployment_location):
        """
        Initiates a request to create infrastructure based on a TOSCA template.
        This method should return immediate response of the request being accepted,
        it is expected that the InfrastructureService will poll get_infrastructure_task on this driver to determine when the request has complete.

        :param str template: template of infrastructure to be created
        :param str template_type: type of template used i.e. TOSCA or Heat
        :param str inputs: values for the inputs defined on the tosca template
        :param dict deployment_location: the deployment location to deploy to
        :return: an ignition.model.infrastructure.CreateInfrastructureResponse
        """
        pass

    @interface
    def get_infrastructure_task(self, infrastructure_id, request_id, deployment_location):
        """
        Get information about the infrastructure (created or deleted)

        :param str infrastructure_id: identifier of the infrastructure to check
        :param str request_id: identifier of the request to check
        :param dict deployment_location: the location the infrastructure was deployed to
        :return: an ignition.model.infrastructure.InfrastructureTask instance describing the status
        """
        pass

    @interface
    def delete_infrastructure(self, infrastructure_id, deployment_location):
        """
        Initiates a request to delete infrastructure previously created with the given infrastructure_id.
        This method should return immediate response of the request being accepted,
        it is expected that the InfrastructureService will poll get_infrastructure_task on this driver to determine when the request has complete.

        :param str infrastructure_id: identifier of the infrastructure to be removed
        :param dict deployment_location: the location the infrastructure was deployed to
        :return: an ignition.model.infrastructure.DeleteInfrastructureResponse
        """
        pass

    @interface
    def find_infrastructure(self, template, template_type, instance_name, deployment_location):
        """
        Finds infrastructure instances that meet the requirements set out in the given TOSCA template, returning the desired output values from those instances

        :param str template: tosca template of infrastructure to be found
        :param str template_type: type of template used i.e. TOSCA or Heat
        :param str instance_name: name given as search criteria
        :param dict deployment_location: the deployment location to deploy to
        :return: an ignition.model.infrastructure.FindInfrastructureResponse
        """
        pass


class InfrastructureApiCapability(Capability):

    @interface
    def create(self, **kwarg):
        pass

    @interface
    def delete(self, **kwarg):
        pass

    @interface
    def query(self, **kwarg):
        pass

    @interface
    def find(self, **kwarg):
        pass


class InfrastructureServiceCapability(Capability):

    @interface
    def create_infrastructure(self, template, template_type, inputs, deployment_location):
        pass

    @interface
    def get_infrastructure_task(self, infrastructure_id, request_id, deployment_location):
        pass

    @interface
    def delete_infrastructure(self, infrastructure_id, deployment_location):
        pass

    @interface
    def find_infrastructure(self, template, template_type, instance_name, deployment_location):
        pass


class InfrastructureTaskMonitoringCapability(Capability):

    @interface
    def monitor_task(self, infrastructure_id, request_id, deployment_location):
        pass


class InfrastructureMessagingCapability(Capability):

    @interface
    def send_infrastructure_task(self, infrastructure_task):
        pass


class InfrastructureApiService(Service, InfrastructureApiCapability, BaseController):
    """
    Out-of-the-box controller for the Infrastructure API
    """

    def __init__(self, **kwargs):
        if 'service' not in kwargs:
            raise ValueError('No service instance provided')
        self.service = kwargs.get('service')

    def create(self, **kwarg):
        try:
            logging_context.set_from_headers()

            body = self.get_body(kwarg)
            logger.debug('Create infrastructure with body %s', body)
            template = self.get_body_required_field(body, 'template')
            template_type = self.get_body_required_field(body, 'templateType')
            deployment_location = self.get_body_required_field(body, 'deploymentLocation')
            inputs = self.get_body_field(body, 'inputs', {})
            create_response = self.service.create_infrastructure(template, template_type, inputs, deployment_location)
            response = {'infrastructureId': create_response.infrastructure_id, 'requestId': create_response.request_id}
            return (response, 202)
        finally:
            logging_context.clear()

    def delete(self, **kwarg):
        try:
            logging_context.set_from_headers()

            body = self.get_body(kwarg)
            logger.debug('Delete infrastructure with body %s', body)
            deployment_location = self.get_body_required_field(body, 'deploymentLocation')
            infrastructure_id = self.get_body_required_field(body, 'infrastructureId')
            delete_response = self.service.delete_infrastructure(infrastructure_id, deployment_location)
            response = {'infrastructureId': delete_response.infrastructure_id, 'requestId': delete_response.request_id}
            return (response, 202)
        finally:
            logging_context.clear()

    def query(self, **kwarg):
        try:
            logging_context.set_from_headers()

            body = self.get_body(kwarg)
            logger.debug('Query infrastructure with body %s', body)
            deployment_location = self.get_body_required_field(body, 'deploymentLocation')
            infrastructure_id = self.get_body_required_field(body, 'infrastructureId')
            request_id = self.get_body_required_field(body, 'requestId')
            infrastructure_task = self.service.get_infrastructure_task(infrastructure_id, request_id, deployment_location)
            response = infrastructure_task_dict(infrastructure_task)
            return (response, 200)
        finally:
            logging_context.clear()

    def find(self, **kwarg):
        try:
            logging_context.set_from_headers()

            body = self.get_body(kwarg)
            logger.debug('Find infrastructure with body %s', body)
            template = self.get_body_required_field(body, 'template')
            template_type = self.get_body_required_field(body, 'templateType')
            deployment_location = self.get_body_required_field(body, 'deploymentLocation')
            instance_name = self.get_body_required_field(body, 'instanceName')
            service_find_response = self.service.find_infrastructure(template, template_type, instance_name, deployment_location)
            response = infrastructure_find_response_dict(service_find_response)
            return (response, 200)
        finally:
            logging_context.clear()

class InfrastructureService(Service, InfrastructureServiceCapability):
    """
    Out-of-the-box service for the Infrastructure API
    """

    def __init__(self, **kwargs):
        if 'driver' not in kwargs:
            raise ValueError('driver argument not provided')
        if 'infrastructure_config' not in kwargs:
            raise ValueError('infrastructure_config argument not provided')
        self.driver = kwargs.get('driver')
        infrastructure_config = kwargs.get('infrastructure_config')
        self.async_enabled = infrastructure_config.async_messaging_enabled
        if self.async_enabled is True:
            if 'inf_monitor_service' not in kwargs:
                raise ValueError('inf_monitor_service argument not provided (required when async_messaging_enabled is True)')
            self.inf_monitor_service = kwargs.get('inf_monitor_service')

    def create_infrastructure(self, template, template_type, inputs, deployment_location):
        create_response = self.driver.create_infrastructure(template, template_type, inputs, deployment_location)
        if self.async_enabled is True:
            self.__async_infrastructure_task_completion(create_response.infrastructure_id, create_response.request_id, deployment_location)
        return create_response

    def get_infrastructure_task(self, infrastructure_id, request_id, deployment_location):
        return self.driver.get_infrastructure_task(infrastructure_id, request_id, deployment_location)

    def delete_infrastructure(self, infrastructure_id, deployment_location):
        delete_response = self.driver.delete_infrastructure(infrastructure_id, deployment_location)
        if self.async_enabled is True:
            self.__async_infrastructure_task_completion(delete_response.infrastructure_id, delete_response.request_id, deployment_location)
        return delete_response

    def find_infrastructure(self, template, template_type, instance_name, deployment_location):
        find_response = self.driver.find_infrastructure(template, template_type, instance_name, deployment_location)
        return find_response

    def __async_infrastructure_task_completion(self, infrastructure_id, request_id, deployment_location):
        self.inf_monitor_service.monitor_task(infrastructure_id, request_id, deployment_location)


INFRASTRUCTURE_TASK_MONITOR_JOB_TYPE = 'InfrastructureTaskMonitoring'


class InfrastructureTaskMonitoringService(Service, InfrastructureTaskMonitoringCapability):

    def __init__(self, **kwargs):
        if 'job_queue_service' not in kwargs:
            raise ValueError('job_queue_service argument not provided')
        if 'inf_messaging_service' not in kwargs:
            raise ValueError('inf_messaging_service argument not provided')
        if 'driver' not in kwargs:
            raise ValueError('driver argument not provided')
        self.job_queue_service = kwargs.get('job_queue_service')
        self.inf_messaging_service = kwargs.get('inf_messaging_service')
        self.driver = kwargs.get('driver')
        self.job_queue_service.register_job_handler(INFRASTRUCTURE_TASK_MONITOR_JOB_TYPE, self.job_handler)

    def job_handler(self, job_definition):
        if 'infrastructure_id' not in job_definition or job_definition['infrastructure_id'] is None:
            logger.warning('Job with {0} job type is missing infrastructure_id. This job has been discarded'.format(INFRASTRUCTURE_TASK_MONITOR_JOB_TYPE))
            return True
        if 'request_id' not in job_definition or job_definition['request_id'] is None:
            logger.warning('Job with {0} job type is missing request_id. This job has been discarded'.format(INFRASTRUCTURE_TASK_MONITOR_JOB_TYPE))
            return True
        if 'deployment_location' not in job_definition or job_definition['deployment_location'] is None:
            logger.warning('Job with {0} job type is missing deployment_location. This job has been discarded'.format(INFRASTRUCTURE_TASK_MONITOR_JOB_TYPE))
            return True
        infrastructure_id = job_definition['infrastructure_id']
        request_id = job_definition['request_id']
        deployment_location = job_definition['deployment_location']
        infrastructure_task = self.driver.get_infrastructure_task(infrastructure_id, request_id, deployment_location)
        status = infrastructure_task.status
        if status in [STATUS_COMPLETE, STATUS_FAILED]:
            self.inf_messaging_service.send_infrastructure_task(infrastructure_task)
            return True
        return False

    def __create_job_definition(self, infrastructure_id, request_id, deployment_location):
        return {
            'job_type': INFRASTRUCTURE_TASK_MONITOR_JOB_TYPE,
            'infrastructure_id': infrastructure_id,
            'request_id': request_id,
            'deployment_location': deployment_location
        }

    def monitor_task(self, infrastructure_id, request_id, deployment_location):
        if infrastructure_id is None:
            raise ValueError('Cannot monitor task when infrastructure_id is not given')
        if request_id is None:
            raise ValueError('Cannot monitor task when request_id is not given')
        if deployment_location is None:
            raise ValueError('Cannot monitor task when deployment_location is not given')
        self.job_queue_service.queue_job(self.__create_job_definition(infrastructure_id, request_id, deployment_location))


class InfrastructureMessagingService(Service, InfrastructureMessagingCapability):

    def __init__(self, **kwargs):
        if 'postal_service' not in kwargs:
            raise ValueError('postal_service argument not provided')
        if 'topics_configuration' not in kwargs:
            raise ValueError('topics_configuration argument not provided')
        self.postal_service = kwargs.get('postal_service')
        topics_configuration = kwargs.get('topics_configuration')
        if topics_configuration.infrastructure_task_events is None:
            raise ValueError('infrastructure_task_events topic must be set')
        self.infrastructure_task_events_topic = topics_configuration.infrastructure_task_events.name
        if self.infrastructure_task_events_topic is None:
            raise ValueError('infrastructure_task_events topic name must be set')

    def send_infrastructure_task(self, infrastructure_task):
        if infrastructure_task is None:
            raise ValueError('infrastructure_task must be set to send an infrastructure task event')
        infrastructure_task_message_content = infrastructure_task_dict(infrastructure_task)
        message_str = JsonContent(infrastructure_task_message_content).get()
        self.postal_service.post(Envelope(self.infrastructure_task_events_topic, Message(message_str)))
