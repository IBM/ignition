import unittest
from unittest.mock import MagicMock, patch
from ignition.boot.api import ApplicationBuilder
from ignition.boot.app import BootstrapApplication
from ignition.boot.config import ApplicationProperties, ApiProperties, DynamicApiConfigurator, DynamicServiceConfigurator
from ignition.service.config import YmlFileSource, EnvironmentVariableYmlFileSource, ConfigurationPropertiesGroup
from ignition.service.framework import Service


class TestPropertyGroup(ConfigurationPropertiesGroup):

    def __init__(self):
        super().__init__('test')


class TestApplicationBuilder(unittest.TestCase):

    def test_app_name(self):
        builder = ApplicationBuilder()
        self.assertIsNone(builder.app_name)
        builder = ApplicationBuilder('Test')
        self.assertEqual(builder.app_name, 'Test')

    def test_include_file_config_properties(self):
        builder = ApplicationBuilder()
        return_builder = builder.include_file_config_properties('test_props.yml')
        self.assertEqual(builder, return_builder)
        self.assertEqual(len(builder.property_sources), 1)
        self.assertIsInstance(builder.property_sources[0], YmlFileSource)
        self.assertEqual(builder.property_sources[0].file_path, 'test_props.yml')

    def test_include_environment_config_properties(self):
        builder = ApplicationBuilder()
        return_builder = builder.include_environment_config_properties('PROPS_VAR')
        self.assertEqual(builder, return_builder)
        self.assertEqual(len(builder.property_sources), 1)
        self.assertIsInstance(builder.property_sources[0], EnvironmentVariableYmlFileSource)
        self.assertEqual(builder.property_sources[0].environment_variable, 'PROPS_VAR')

    def test_default_property_groups(self):
        builder = ApplicationBuilder()
        all_property_groups = builder.property_groups.all_groups()
        self.assertEqual(len(all_property_groups), 2)
        found_api_props = False
        found_application_props = False
        for group in all_property_groups:
            if isinstance(group, ApplicationProperties):
                found_application_props = True
            elif isinstance(group, ApiProperties):
                found_api_props = True
        self.assertTrue(found_application_props)
        self.assertTrue(found_api_props)

    def test_add_property_group(self):
        builder = ApplicationBuilder()
        test_group = TestPropertyGroup()
        return_builder = builder.add_property_group(test_group)
        self.assertEqual(builder, return_builder)
        self.assertEqual(len(builder.property_groups.all_groups()), 3)
        self.assertIn(test_group, builder.property_groups.all_groups())

    def test_add_api_configurator(self):
        builder = ApplicationBuilder()
        mock_configurator = MagicMock()
        return_builder = builder.add_api_configurator(mock_configurator)
        self.assertEqual(builder, return_builder)
        self.assertEqual(len(builder.api_configurators), 1)
        self.assertEqual(builder.api_configurators[0], mock_configurator)

    def test_add_service_configurator(self):
        builder = ApplicationBuilder()
        mock_configurator = MagicMock()
        return_builder = builder.add_service_configurator(mock_configurator)
        self.assertEqual(builder, return_builder)
        self.assertEqual(len(builder.service_configurators), 1)
        self.assertEqual(builder.service_configurators[0], mock_configurator)

    def test_add_api(self):
        builder = ApplicationBuilder()
        mock_capability = MagicMock()
        return_builder = builder.add_api('mock_spec.yml', mock_capability)
        self.assertEqual(builder, return_builder)
        self.assertEqual(len(builder.api_configurators), 1)
        self.assertIsInstance(builder.api_configurators[0], DynamicApiConfigurator)
        self.assertEqual(builder.api_configurators[0].api_spec, 'mock_spec.yml')
        self.assertEqual(builder.api_configurators[0].api_capability, mock_capability)

    def test_add_service(self):
        builder = ApplicationBuilder()

        class MockService(Service):
            pass
        mock_capability = MagicMock()
        return_builder = builder.add_service(MockService, 'arg1', mock_capability=mock_capability)
        self.assertEqual(builder, return_builder)
        self.assertEqual(len(builder.service_configurators), 1)
        self.assertIsInstance(builder.service_configurators[0], DynamicServiceConfigurator)
        self.assertEqual(builder.service_configurators[0].service_class, MockService)
        self.assertEqual(builder.service_configurators[0].args, ('arg1',))
        self.assertEqual(builder.service_configurators[0].required_capabilities, {'mock_capability': mock_capability})

    def test_set_error_converter(self):
        builder = ApplicationBuilder()
        mock_error_converter = MagicMock()
        return_builder = builder.set_error_converter(mock_error_converter)
        self.assertEqual(builder, return_builder)
        self.assertEqual(builder.api_error_converter, mock_error_converter)

    @patch('ignition.boot.api.BootstrapApplicationConfiguration')
    def test_build(self, mock_config_init):
        builder = ApplicationBuilder('Test')
        configuration = builder.build()
        self.assertEqual(configuration, mock_config_init.return_value)
        mock_config_init.assert_called_once_with('Test', builder.property_sources, builder.property_groups, builder.service_configurators, builder.api_configurators, builder.api_error_converter)

    @patch('ignition.boot.api.BootstrapRunner')
    @patch('ignition.boot.api.BootstrapApplicationConfiguration')
    def test_configure(self, mock_config_init, mock_runner_init):
        builder = ApplicationBuilder('Test')
        app = builder.configure()
        mock_runner_init.assert_called_once_with(mock_config_init.return_value)
        self.assertEqual(app, mock_runner_init.return_value.init_app.return_value)

    @patch('ignition.boot.api.BootstrapRunner')
    @patch('ignition.boot.api.BootstrapApplicationConfiguration')
    def test_run(self, mock_config_init, mock_runner_init):
        builder = ApplicationBuilder('Test')
        app = builder.run()
        mock_runner_init.assert_called_once_with(mock_config_init.return_value)
        self.assertEqual(app, mock_runner_init.return_value.init_app.return_value)
        app.run.assert_called_once()
