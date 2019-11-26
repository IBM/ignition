import connexion
import logging
import os
import shutil
from ignition.boot.config import ApplicationProperties, ApiProperties
from ignition.boot.connexionutils import RequestBodyValidator
from ignition.service.config import ConfigParserService, ConfigurationProperties
from ignition.service.framework import ServiceRegister, ServiceInstances, ServiceInitialiser, ServiceRegistration, Service
from ignition.utils.file import safe_filename

logger = logging.getLogger(__name__)

class ApiRegister():

    def __init__(self):
        self.connexion_apis = []

    def register_api(self, api_spec, **kwargs):
        logger.debug('Registering API with spec {0}'.format(api_spec))
        self.connexion_apis.append({'api_spec': api_spec, 'kwargs': kwargs})


class BootstrapRunner():
    """
    Takes BootstrapRunnerConfiguration and produces a BootstrapApplication
    """

    def __init__(self, configuration):
        self.configuration = configuration
        if self.configuration.app_name is None:
            self.configuration.app_name = 'BootstrapApplication'
        self.property_sources = self.configuration.property_sources
        self.property_groups = self.configuration.property_groups
        self.service_configurators = self.configuration.service_configurators
        self.api_configurators = self.configuration.api_configurators
        self.api_register = ApiRegister()
        self.service_register = ServiceRegister()
        self.service_instances = ServiceInstances()

    def __process_properties(self):
        parser = ConfigParserService()
        parser.parse(self.property_sources, self.property_groups.all_groups())

    def __get_api_spec(self):
        spec_dir = None
        api_properties = self.property_groups.get_property_group(ApiProperties)
        spec_dir = api_properties.specification_dir
        if spec_dir is None:
            app_name_as_file_name = safe_filename(self.configuration.app_name)
            app_name_as_file_name = '{0}_boot'.format(app_name_as_file_name)
            spec_dir = os.path.join(os.getcwd(), app_name_as_file_name, 'api_specs')
        return spec_dir

    def __get_server_port(self):
        application_properties = self.property_groups.get_property_group(ApplicationProperties)
        if application_properties.port is None:
            raise ValueError('application.port must be set')
        if not isinstance(application_properties.port, int):
            raise ValueError('application.port must be an integer')
        return application_properties.port

    def __add_error_handler(self, connexion_app):
        error_converter = self.configuration.api_error_converter
        if error_converter is not None:
            connexion_app.add_error_handler(Exception, error_converter.handle)

    def __connexion_runtime_args(self):
        application_properties = self.property_groups.get_property_group(ApplicationProperties)
        connexion_runtime_props = application_properties.connexion_runtime_props
        if connexion_runtime_props is None:
            connexion_runtime_props = {}
        connexion_runtime_props['port'] = self.__get_server_port()
        return connexion_runtime_props

    def __configure_connexion_api_specs(self):
        spec_dir = self.__get_api_spec()
        if not os.path.exists(spec_dir):
            os.makedirs(spec_dir)
        for connexion_api in self.api_register.connexion_apis:
            orig_path_to_spec = connexion_api['api_spec']
            if not os.path.exists(orig_path_to_spec):
                raise ValueError('api_spec not found at path: {0}'.format(orig_path_to_spec))
            file_name = os.path.basename(orig_path_to_spec)
            new_path_to_spec = os.path.join(spec_dir, file_name)
            logger.debug('Copying api_spec {0} to {1}'.format(orig_path_to_spec, new_path_to_spec))
            shutil.copy2(orig_path_to_spec, new_path_to_spec)
            connexion_api['api_spec'] = file_name

    def __connexion_init_args(self):
        application_properties = self.property_groups.get_property_group(ApplicationProperties)
        connexion_init_props = application_properties.connexion_init_props
        if connexion_init_props is None:
            connexion_init_props = {}
        connexion_init_props['specification_dir'] = self.__get_api_spec()
        return connexion_init_props

    def __create_properties_group_service_registration(self, configuration_class):
        registration = ServiceRegistration(configuration_class)
        registration.provided = True
        return registration

    def __register_property_group_services(self, config):
        if isinstance(config, ConfigurationProperties):
            if isinstance(config, Service):
                self.service_register.add_service(self.__create_properties_group_service_registration(config.__class__))
            for attr, value in config.__dict__.items():
                if value is not None:
                    self.__register_property_group_services(value)

    def __register_property_group_instances(self, config):
        if isinstance(config, ConfigurationProperties):
            if isinstance(config, Service):
                self.service_instances.add_instance_of(config, config.__class__)
            for attr, value in config.__dict__.items():
                if value is not None:
                    self.__register_property_group_instances(value)

    def init_app(self):
        app_name = self.configuration.app_name
        logger.info('Bootstrapping Application: {0}'.format(app_name))

        # Read all the Property Sources
        self.__process_properties()

        # Allow ConfigurationProperties classes to be registered as Services
        for property_group in self.property_groups.all_groups():
            self.__register_property_group_services(property_group)

        # Run Service Configurators
        for service_configurator in self.service_configurators:
            service_configurator.configure(self.configuration, self.service_register)

        # Build instances of Services
        for property_group in self.property_groups.all_groups():
            self.__register_property_group_instances(property_group)
        initialiser = ServiceInitialiser(self.service_instances, self.service_register)
        initialiser.build_instances()

        # Run API Configurators
        for api_configurator in self.api_configurators:
            api_configurator.configure(self.configuration, self.service_register, self.service_instances, self.api_register)

        # Build connexion app
        connexion_app = connexion.App(app_name, **self.__connexion_init_args())
        self.__configure_connexion_api_specs()
        self.__add_error_handler(connexion_app)
        for connexion_api in self.api_register.connexion_apis:
            connexion_api['kwargs']['validator_map'] = {'body': RequestBodyValidator}
            connexion_app.add_api(connexion_api['api_spec'], **connexion_api['kwargs'])

        # Build final BootstrapApplication
        inst = BootstrapApplication(app_name, connexion_app, self.__connexion_runtime_args())
        return inst


class BootstrapApplication():

    def __init__(self, name, connexion_app, connexion_runtime_args):
        self.name = name
        self.connexion_app = connexion_app
        self.connexion_runtime_args = connexion_runtime_args

    def run(self):
        self.connexion_app.run(**self.connexion_runtime_args)
