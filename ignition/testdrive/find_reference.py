import yaml
import logging
from .driver_client import DriverClient, DriverClientError

logger = logging.getLogger(__name__)

class FindReferenceRequest:

    def __init__(self, resource_state, instance_name, driver_type, driver_endpoint, quiet=False):
        if resource_state is None:
            raise ValueError('resource_state must be provided')
        self.resource_state = resource_state
        if instance_name is None:
            raise ValueError('instance_name must be provided')
        self.instance_name = instance_name
        if driver_type is None:
            raise ValueError('driver_type must be provided')
        self.driver_type = driver_type
        if driver_endpoint is None:
            raise ValueError('driver_endpoint must be provided')
        self.driver_endpoint = driver_endpoint
        self.quiet = quiet

    def _get_request_args(self):
        return {
            'instance_name': self.instance_name,
            'driver_files': self.resource_state.base64_driver_files(self.driver_type),
            'deployment_location': self.resource_state.deployment_location
        }

    def run(self):
        client = DriverClient(self.driver_endpoint)
        args = self._get_request_args()
        self._log_request(args)
        try:
            response = client.find_reference(**args)
        except DriverClientError as e:
            self._log_failed_request(e)
            raise
        self._log_sync_response(response)

    def _log_request(self, args):
        if not self.quiet:
            msg = '--- Request: find_reference ---'
            msg += '\n'
            msg += yaml.safe_dump(args)
            logger.info(msg)

    def _log_failed_request(self, error):
        if not self.quiet:
            msg = '--- Response: find_reference ---'
            msg += '\n'
            msg += f'Request failed: {str(error)}'
            logger.info(msg)

    def _log_sync_response(self, response):
        if not self.quiet:
            msg = '--- Response: find_reference ---'
            msg += '\n'
            msg += yaml.safe_dump(response)
            logger.info(msg)