import logging
import jinja2 as jinja
import random
import os
import ignition
import re

DRIVER_TYPE_VIM = 'VIM'
DRIVER_TYPE_LIFECYCLE = 'LIFECYCLE'

JINJA_VARIABLE_START = '{('
JINJA_VARIABLE_END = ')}'

logger = logging.getLogger(__name__)

class DriverGenRequest:

    def __init__(self, driver_types, app_name, version="1.0.0", port=None, module_name=None, description=None, docker_name=None, helm_name=None, helm_node_port=None):
        self.driver_types = []
        if len(driver_types) == 0:
            raise ValueError('driver_types cannot be empty')
        for driver_type in driver_types:
            target_driver_type = driver_type.upper()
            if target_driver_type == DRIVER_TYPE_VIM or target_driver_type == DRIVER_TYPE_LIFECYCLE:
                if driver_type not in self.driver_types:
                    self.driver_types.append(target_driver_type)
            else:
                raise ValueError('Each driver_type must be one of: {0}'.format([DRIVER_TYPE_VIM, DRIVER_TYPE_LIFECYCLE]))
        self.app_name = app_name
        self.version = version
        if port == None:
            port = self.generate_port()
        self.port = port
        if module_name == None:
            module_name = self.generate_module_name(self.app_name)
        self.__validate_module_name(module_name)
        self.module_name = module_name
        self.description = description
        if docker_name == None:
            docker_name = self.generate_docker_name(self.app_name)
        self.__validate_docker_name(docker_name)
        self.docker_name = docker_name
        if helm_name == None:
            helm_name = self.generate_helm_name(self.app_name)
        self.__validate_helm_name(helm_name)
        self.helm_name = helm_name
        if helm_node_port == None:
            helm_node_port = self.generate_node_port()
        self.helm_node_port = helm_node_port

    def __validate_module_name(self, module_name):
        if not re.match('^[a-zA-Z0-9]*$', module_name):
            raise ValueError('module_name must be a string with characters from a-z, A-Z, 0-9 but was: {0}'.format(module_name))

    def __validate_helm_name(self, helm_name):
        if not re.match('^[a-zA-Z0-9-_]*$', helm_name):
            raise ValueError('helm_name must be a string with characters from a-z, A-Z, 0-9, dash (-) or underscore (_) but was: {0}'.format(helm_name))

    def __validate_docker_name(self, docker_name):
        if not re.match('^[a-zA-Z0-9-_]*$', docker_name):
            raise ValueError('docker_name must be a string with characters from a-z, A-Z, 0-9, dash (-) or underscore (_) but was: {0}'.format(docker_name))
    
    def generate_helm_name(self, app_name):
        filtered_helm_name = re.sub('[^A-Za-z0-9-_ ]+', '', app_name)
        filtered_helm_name = " ".join(filtered_helm_name.split())
        return filtered_helm_name.lower().replace(" ", "-")

    def generate_docker_name(self, app_name):
        filtered_docker_name = re.sub('[^A-Za-z0-9-_ ]+', '', app_name)
        filtered_docker_name = " ".join(filtered_docker_name.split())
        return filtered_docker_name.lower().replace(" ", "-")

    def generate_module_name(self, app_name):
        filtered_module_name = re.sub('[^A-Za-z0-9 ]+', '', app_name)
        filtered_module_name = " ".join(filtered_module_name.split())
        return filtered_module_name.lower().replace(" ", "")

    def generate_port(self):
        return random.randint(7000, 7999)

    def generate_node_port(self):
        return random.randint(30000, 30999)

class ProducerError(Exception):
    pass

class DriverProducer:

    def __init__(self, request, target_location):
        self.request = request
        self.target_location = target_location

    def __determine_templates(self):
        templates_dir = os.path.dirname(__file__)
        template_paths = [os.path.join(templates_dir, 'driver_template')]
        if DRIVER_TYPE_VIM in self.request.driver_types:
            template_paths.append(os.path.join(templates_dir, 'vim_additions'))
        if DRIVER_TYPE_LIFECYCLE in self.request.driver_types:
            template_paths.append(os.path.join(templates_dir, 'lifecycle_additions'))
        return template_paths

    def __create_render_props(self):
        render_props = {}
        render_props['ignition'] = {}
        render_props['ignition']['version'] = ignition.__version__
        render_props['app'] = {}
        render_props['app']['is_vim'] = (DRIVER_TYPE_VIM in self.request.driver_types)
        render_props['app']['is_lifecycle'] = (DRIVER_TYPE_LIFECYCLE in self.request.driver_types)
        render_props['app']['name'] = self.request.app_name
        render_props['app']['description'] = self.request.description
        render_props['app']['module_name'] = self.request.module_name
        render_props['app']['port'] = self.request.port
        render_props['app']['version'] = self.request.version
        render_props['helm'] = {}
        render_props['helm']['name'] = self.request.helm_name
        render_props['helm']['node_port'] = self.request.helm_node_port
        render_props['docker'] = {}
        render_props['docker']['name'] = self.request.docker_name
        return render_props

    def __render_template(self, template_path, render_props):
        template_loader = jinja.FileSystemLoader(searchpath=template_path)
        template_env = jinja.Environment(variable_start_string=JINJA_VARIABLE_START, variable_end_string=JINJA_VARIABLE_END, loader=template_loader)
        file_name_env = jinja.Environment(variable_start_string=JINJA_VARIABLE_START, variable_end_string=JINJA_VARIABLE_END, loader=jinja.BaseLoader)
        for item in os.listdir(template_path):
            full_item_path = os.path.join(template_path, item)
            if os.path.isdir(full_item_path):
                self.__render_directory(template_path, template_env, file_name_env, full_item_path, self.target_location, render_props)
            else:
                self.__render_file(template_path, template_env, file_name_env, full_item_path, self.target_location, render_props)

    def __render_directory(self, template_base_path, template_env, file_name_env, template_dir_path, target_parent_path, render_props):
        if os.path.basename(template_dir_path) == '__pycache__':
            return
        logger.debug('Rendering directory {0}'.format(template_dir_path))
        template_dir_name = os.path.basename(template_dir_path)
        new_dir_name = file_name_env.from_string(template_dir_name).render(render_props)
        new_dir_path = os.path.join(target_parent_path, new_dir_name)
        if os.path.exists(new_dir_path):
            if not os.path.isdir(new_dir_path):
                raise ProducerError('Template item \'{0}\' already exists but is not a directory'.format(new_dir_path))
        else:
            os.mkdir(new_dir_path)
        for item in os.listdir(template_dir_path):
            full_item_path = os.path.join(template_dir_path, item)
            if os.path.isdir(full_item_path):
                self.__render_directory(template_base_path, template_env, file_name_env, full_item_path, new_dir_path, render_props)
            else:
                self.__render_file(template_base_path, template_env, file_name_env, full_item_path, new_dir_path, render_props)

    def __render_file(self, template_base_path, template_env, file_name_env, template_file_path, target_parent_path, render_props):
        template_filename, template_ext = os.path.splitext(template_file_path)
        if template_ext == '.pyc':
            return
        logger.debug('Rendering file {0}'.format(template_file_path))
        template_rel_path = os.path.relpath(template_file_path, template_base_path)
        template = template_env.get_template(template_rel_path)
        output = template.render(render_props)
        template_file_name = os.path.basename(template_file_path)
        new_file_name = file_name_env.from_string(template_file_name).render(render_props)
        new_file_path = os.path.join(target_parent_path, new_file_name)
        with open(new_file_path, 'w') as f:
            f.write(output)

    def __create_target_location(self):
        if os.path.exists(self.target_location):
            if not os.path.isdir(self.target_location):
                raise ProducerError('Target location \'{0}\' already exists but is not a directory'.format(self.target_location))
        else:
            os.mkdir(self.target_location)
        
    def produce(self):
        templates = self.__determine_templates()
        self.__create_target_location()
        render_props = self.__create_render_props()
        for template in templates:
            self.__render_template(template, render_props)

