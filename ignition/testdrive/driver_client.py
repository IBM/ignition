import requests
import os
import tempfile
from .base_client import BaseClient 

class DriverClientError(Exception):
    pass

class DriverClient(BaseClient):

    def __init__(self, driver_endpoint):
        if driver_endpoint is None:
            raise ValueError('driver_endpoint must be provided to create Driver Client')
        self.driver_endpoint = driver_endpoint.rstrip('/')

    def execute_lifecycle(self, lifecycle_name, driver_files, system_properties, resource_properties, request_properties, associated_topology, deployment_location, headers=None):
        url = '{0}/api/driver/lifecycle/execute'.format(self.driver_endpoint)
        headers = headers or {}
        body = {
            'lifecycleName': lifecycle_name,
            'driverFiles': driver_files,
            'systemProperties': system_properties,
            'resourceProperties': resource_properties,
            'requestProperties': request_properties,
            'associatedTopology': associated_topology,
            'deploymentLocation': deployment_location
        }
        response = requests.post(url, headers=headers, json=body, verify=False)
        if response.status_code == 202:
            return response.json()
        else:
            self._raise_unexpected_status_exception(response)

    def find_reference(self, instance_name, driver_files, deployment_location):
        url = '{0}/api/driver/references/find'.format(self.driver_endpoint)
        headers = {}
        body = {
            'instanceName': instance_name,
            'driverFiles': driver_files,
            'deploymentLocation': deployment_location
        }
        response = requests.post(url, headers=headers, json=body, verify=False)
        if response.status_code == 200:
            return response.json()
        else:
            self._raise_unexpected_status_exception(response)

    def _raise_unexpected_status_exception(self, response, error_prefx=None):
        message = None
        try:
            json_body = response.json()
            if 'localizedMessage' in json_body:
                message = json_body['localizedMessage']
            elif 'message' in json_body:
                message = json_body['message']
        except ValueError as e:
            pass
        error_msg = ''
        if error_prefx is not None:
            error_msg += '{0}: '.format(error_prefx)
        error_msg += 'Request returned unexpected error: status_code={0}'.format(response.status_code)
        if message:
            error_msg += ', message={0}'.format(message)
        raise DriverClientError(error_msg)