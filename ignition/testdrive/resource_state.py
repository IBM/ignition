import os
import tempfile
import shutil
import base64
import logging
import uuid
import yaml
import random
from ignition.utils.propvaluemap import PropValueMap
from ignition.model.associated_topology import AssociatedTopology

logger = logging.getLogger(__name__)

class ResourceState:

    def __init__(self, driver_files=None, driver_files_dir=None, deployment_location=None, system_properties=None, resource_properties=None, associated_topology=None, 
    driver_files_encoded=False, disable_auto_system_properties=False):
        if driver_files is not None and driver_files_dir is not None:
            raise ValueError('Cannot set both driver_files and driver_files_dir')
        self.driver_files = driver_files
        self.driver_files_encoded = driver_files_encoded
        self.driver_files_dir = driver_files_dir
        self.deployment_location = deployment_location if deployment_location is not None else {}
        self.system_properties = system_properties if system_properties is not None else {}
        self.resource_properties = resource_properties if resource_properties is not None else {}
        self.associated_topology = associated_topology if associated_topology is not None else {}
        self.disable_auto_system_properties = disable_auto_system_properties
        if not self.disable_auto_system_properties:
            self.__auto_system_properties()

    def __auto_system_properties(self):
        resource_name_and_type = None
        if self.system_properties is None:
            self.system_properties = {}
        if 'resourceId' not in self.system_properties:
            self.system_properties['resourceId'] = {'type': 'string', 'value': str(uuid.uuid4())}
        if 'resourceName' not in self.system_properties:
            resource_name_and_type = generate_resource_name_and_type()
            self.system_properties['resourceName'] = {'type': 'string', 'value': resource_name_and_type[0]}
        if 'resourceMananger' not in self.system_properties:
            self.system_properties['resourceMananger'] = {'type': 'string', 'value': str(uuid.uuid4())}
        if 'deploymentLocation' not in self.system_properties:
            if self.deployment_location is not None:
                self.system_properties['deploymentLocation'] = {'type': 'string', 'value': self.deployment_location.get('name')}
        if 'resourceType' not in self.system_properties:
            if resource_name_and_type is None:
                resource_name_and_type = generate_resource_name_and_type()
            self.system_properties['resourceType'] = {'type': 'string', 'value': resource_name_and_type[1]}

    def base64_driver_files(self, driver_type):
        if self.driver_files is not None:
            if self.driver_files_encoded:
                logger.info('driver_files_encoded is True - using raw value of driver_files')
                return self.driver_files
            else:
                logger.info('driver_files is set - encoding value')
                return self._get_driver_files_base64(self.driver_files)
        elif self.driver_files_dir is not None and driver_type is not None:
            logger.info(f'driver_files_dir is set - encoding directory for driver type {driver_type}')
            driver_files_path = os.path.join(self.driver_files_dir, driver_type)
            return self._get_driver_files_base64(driver_files_path) 
        else:
            return None

    def _get_driver_files_base64(self, driver_files):
        tmp_dir = None
        try:
            file_to_encode = None
            if os.path.exists(driver_files):
                if os.path.isdir(driver_files):
                    tmp_dir = tempfile.mkdtemp()
                    zip_name = os.path.join(tmp_dir, 'driver_files')
                    file_to_encode = shutil.make_archive(zip_name, 'zip', driver_files)
                else:
                    file_to_encode = self.driver_files
            else:
                raise ValueError(f'Could not find driver_files at path {driver_files}')
            with open(file_to_encode, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        finally:
            if tmp_dir is not None and os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir)

    @staticmethod
    def from_dict(data):
        return ResourceState(
            driver_files=data.get('driverFiles'),
            driver_files_dir=data.get('driverFilesDir'),
            system_properties=data.get('systemProperties'),
            resource_properties=data.get('resourceProperties'),
            associated_topology=data.get('associatedTopology'),
            deployment_location=data.get('deploymentLocation'),
            driver_files_encoded=data.get('driverFilesEncoded', False)
        )

    @staticmethod
    def from_file(data_file):
        if os.path.exists(data_file):
            with open(data_file, 'r') as f:
                data = yaml.safe_load(f.read())
            return ResourceState.from_dict(data)
        else:
            raise ValueError(f'Cannot load Resource State from file {data_file} as it does not exist')

service_names = ['LondonA', 'LondonB', 'NewYork' 'Base', 'HqA', 'HqB']
root_composite_names = ['video', 'voice', 'conference']
middle_composite_names = ['core', 'edge', 'site', 'internal', 'external']
resource_names = ['voip-server', 'firewall', 'gateway', 'jumphost', 'router', 'dns-server', 'load-gen']
resource_type_versions = ['1.0', '1.1', '1.2', '2.0', '2.1']

def generate_resource_name_and_type():
    name = random.choice(service_names)
    name += '__' + random.choice(root_composite_names)
    include_middle = random.choice([True, False])
    if include_middle:
        name += '__' + random.choice(middle_composite_names)
    resource_name = random.choice(resource_names)
    name += '__' + random.choice(resource_names)
    resource_type = 'resource::'+resource_name+'::'+random.choice(resource_type_versions)
    return name, resource_type
