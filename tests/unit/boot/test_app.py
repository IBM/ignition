import unittest
import os
from unittest.mock import patch, MagicMock
from ignition.boot.api import ApplicationBuilder
from ignition.boot.config import BootstrapApplicationConfiguration, ApplicationProperties, ApiProperties
from ignition.service.config import DictSource
from ignition.service.messaging import MessagingProperties, TopicsProperties
from ignition.service.framework import Service, Capability, ServiceRegistration
from ignition.boot.app import BootstrapRunner
from ignition.boot.connexionutils import RequestBodyValidator
import ignition.openapi as openapi
import pathlib

# Grabs the __init__.py from the openapi package then takes it's parent, the openapi directory itself
openapi_path = str(pathlib.Path(openapi.__file__).parent.resolve())


class TestBootstrapRunner(unittest.TestCase):

    def __minimal_working_configuration(self, app_name=None):
        app_builder = self.__minimal_working_configuration_builder(app_name)
        return app_builder.build()

    def __minimal_working_configuration_builder(self, app_name=None):
        app_builder = ApplicationBuilder(app_name)
        app_builder.property_groups.get_property_group(ApplicationProperties).port = 7777
        return app_builder

    @patch('ignition.boot.app.connexion.App')
    def test_init_app_default_name(self, mock_connexion_app):
        configuration = self.__minimal_working_configuration()
        bootstrap_runner = BootstrapRunner(configuration)
        app = bootstrap_runner.init_app()
        mock_connexion_app.assert_called_once_with('BootstrapApplication', **{'specification_dir': '{0}/BootstrapApplication_boot/api_specs'.format(os.getcwd())})

    @patch('ignition.boot.app.ServiceRegister')
    @patch('ignition.boot.app.connexion.App')
    def test_init_app_registers_property_groups_as_services(self, mock_connexion_app, mock_service_register_init):
        mock_service_register = MagicMock()
        mock_service_register_init.return_value = mock_service_register
        configuration = self.__minimal_working_configuration()
        bootstrap_runner = BootstrapRunner(configuration)
        app = bootstrap_runner.init_app()
        service_register_add_service_calls = mock_service_register.add_service.call_args_list
        self.assertEqual(len(service_register_add_service_calls), 2)
        expected_service_classes = [ApplicationProperties, ApiProperties]
        for idx, call in enumerate(service_register_add_service_calls):
            call_args, call_kwargs = call
            service_registration_arg = call_args[0]
            self.assertEqual(service_registration_arg.service_class, expected_service_classes[idx])

    @patch('ignition.boot.app.connexion.App')
    def test_init_app_calls_service_configurators(self, mock_connexion_app):
        mock_configurator = MagicMock()
        app_builder = self.__minimal_working_configuration_builder()
        app_builder.add_service_configurator(mock_configurator)
        configuration = app_builder.build()
        bootstrap_runner = BootstrapRunner(configuration)
        app = bootstrap_runner.init_app()
        mock_configurator.configure.assert_called_once_with(configuration, bootstrap_runner.service_register)

    @patch('ignition.boot.app.connexion.App')
    def test_init_app_calls_api_configurators(self, mock_connexion_app):
        mock_configurator = MagicMock()
        app_builder = self.__minimal_working_configuration_builder()
        app_builder.add_api_configurator(mock_configurator)
        configuration = app_builder.build()
        bootstrap_runner = BootstrapRunner(configuration)
        app = bootstrap_runner.init_app()
        mock_configurator.configure.assert_called_once_with(configuration, bootstrap_runner.service_register, bootstrap_runner.service_instances, bootstrap_runner.api_register)

    @patch('ignition.boot.app.ServiceInitialiser')
    @patch('ignition.boot.app.connexion.App')
    def test_init_app_builds_service_instances(self, mock_connexion_app, mock_service_initialiser_init):
        mock_service_initialiser = MagicMock()
        mock_service_initialiser_init.return_value = mock_service_initialiser
        configuration = self.__minimal_working_configuration()
        bootstrap_runner = BootstrapRunner(configuration)
        app = bootstrap_runner.init_app()
        mock_service_initialiser_init.assert_called_once()
        mock_service_initialiser.build_instances.assert_called_once()

    @patch('ignition.boot.app.connexion.App')
    def test_init_app_creates_connexion_app_with_apis(self, mock_connexion_app):
        mock_connexion_App_inst = mock_connexion_app.return_value
        mock_api_configurator = MagicMock()
        mock_resolver = MagicMock()

        def mock_api_configure(configuration, service_register, service_instances, api_register):
            api_register.register_api(os.path.join(openapi_path, 'resource-driver.yaml'), resolver=mock_resolver)
        mock_api_configurator.configure.side_effect = mock_api_configure
        app_builder = self.__minimal_working_configuration_builder('MyTest')
        app_builder.add_api_configurator(mock_api_configurator)
        bootstrap_runner = BootstrapRunner(app_builder.build())
        app = bootstrap_runner.init_app()
        mock_connexion_app.assert_called_once_with('MyTest', **{'specification_dir': '{0}/MyTest_boot/api_specs'.format(os.getcwd())})
        mock_connexion_App_inst.add_api.assert_called_once_with('resource-driver.yaml', **{'resolver': mock_resolver, 'validator_map': {'body': RequestBodyValidator}})
        self.assertEqual(app.connexion_app, mock_connexion_App_inst)

    @patch('ignition.boot.app.connexion.App')
    def test_init_app_creates_connexion_app_with_init_args(self, mock_connexion_app):
        mock_connexion_App_inst = mock_connexion_app.return_value
        app_builder = self.__minimal_working_configuration_builder('MyTest')
        app_builder.property_groups.get_property_group(ApplicationProperties).connexion_init_props['test'] = True
        bootstrap_runner = BootstrapRunner(app_builder.build())
        app = bootstrap_runner.init_app()
        mock_connexion_app.assert_called_once_with('MyTest', **{'test': True, 'specification_dir': '{0}/MyTest_boot/api_specs'.format(os.getcwd())})

    @patch('ignition.boot.app.connexion.App')
    def test_init_app_creates_connexion_app_with_runtime_args(self, mock_connexion_app):
        mock_connexion_App_inst = mock_connexion_app.return_value
        app_builder = self.__minimal_working_configuration_builder('MyTest')
        app_config = app_builder.property_groups.get_property_group(ApplicationProperties)
        app_builder.property_groups.get_property_group(ApplicationProperties).connexion_runtime_props['runtimeTest'] = True
        bootstrap_runner = BootstrapRunner(app_builder.build())
        app = bootstrap_runner.init_app()
        app.run()
        mock_connexion_App_inst.run.assert_called_once_with(**{'port': 7777, 'runtimeTest': True})

    @patch('ignition.boot.app.connexion.App')
    def test_init_app_creates_connexion_app_with_error_handler(self, mock_connexion_app):
        mock_connexion_App_inst = mock_connexion_app.return_value
        app_builder = self.__minimal_working_configuration_builder('MyTest')
        mock_error_converter = MagicMock()
        app_builder.set_error_converter(mock_error_converter)
        bootstrap_runner = BootstrapRunner(app_builder.build())
        app = bootstrap_runner.init_app()
        mock_connexion_App_inst.add_error_handler.assert_called_once_with(Exception, mock_error_converter.handle)
