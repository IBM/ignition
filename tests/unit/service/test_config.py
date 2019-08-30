import unittest
import os
from unittest.mock import MagicMock
from ignition.service.config import ConfigurationProperties, ConfigurationPropertiesGroup, ConfigParserService, DictSource, YmlFileSource, EnvironmentVariableYmlFileSource, EnvironmentSourceError


class SimpleConfigProps(ConfigurationProperties):

    def __init__(self):
        self.propA = False
        self.propB = 10
        self.propC = 'hello'


class ComplexConfigProps(ConfigurationProperties):

    def __init__(self):
        self.propA = 'propA'
        self.propB = SimpleConfigProps()


class TestConfigurationProperties(unittest.TestCase):

    def test_read_from_dict_simple(self):
        config_props = SimpleConfigProps()
        raw_dict = {
            'propB': 12,
            'propC': 'world'
        }
        config_props.read_from_dict(raw_dict)
        self.assertEqual(config_props.propA, False)
        self.assertEqual(config_props.propB, 12)
        self.assertEqual(config_props.propC, 'world')

    def test_read_from_dict_nested(self):
        config_props = ComplexConfigProps()
        raw_dict = {
            'propA': 'propA_updated',
            'propB': {
                'propA': True,
                'propB': 42
            }
        }
        config_props.read_from_dict(raw_dict)
        self.assertEqual(config_props.propA, 'propA_updated')
        self.assertEqual(config_props.propB.propA, True)
        self.assertEqual(config_props.propB.propB, 42)
        self.assertEqual(config_props.propB.propC, 'hello')

    def test_read_from_dict_unknown_attr(self):
        config_props = SimpleConfigProps()
        raw_dict = {
            'propZ': 'hello'
        }
        config_props.read_from_dict(raw_dict)
        self.assertEqual(config_props.propA, False)
        self.assertEqual(config_props.propB, 10)
        self.assertEqual(config_props.propC, 'hello')


class SimpleConfigPropsGroup(ConfigurationPropertiesGroup):

    def __init__(self):
        super().__init__('simple')
        self.propA = False
        self.propB = 10
        self.propC = 'hello'


class AltSimpleConfigPropsGroup(ConfigurationPropertiesGroup):

    def __init__(self):
        super().__init__('simple')
        self.propA = False


class DatabasePropsGroup(ConfigurationPropertiesGroup):

    def __init__(self):
        super().__init__('app.database')
        self.host = None
        self.port = None


class TestConfigParserService(unittest.TestCase):

    def __mock_simple_source(self):
        return DictSource({
            'simple': {
                'propA': True,
                'propB': 12,
                'propC': 'world'
            }
        })

    def __mock_nested_source(self):
        return DictSource({
            'app': {
                'database': {
                    'host': 'test',
                    'port': 8080
                }
            }
        })

    def test_parse_simple_group(self):
        parser_service = ConfigParserService()
        instance = SimpleConfigPropsGroup()
        parser_service.parse([self.__mock_simple_source()], [instance])
        self.assertEqual(instance.propA, True)
        self.assertEqual(instance.propB, 12)
        self.assertEqual(instance.propC, 'world')

    def test_parse_unknown_group(self):
        parser_service = ConfigParserService()
        instance = SimpleConfigPropsGroup()
        parser_service.parse([DictSource({'unknown_group': {'propA': 'test'}})], [instance])
        self.assertEqual(instance.propA, False)
        self.assertEqual(instance.propB, 10)
        self.assertEqual(instance.propC, 'hello')

    def test_parse_two_groups_with_same_namespace(self):
        parser_service = ConfigParserService()
        instance = SimpleConfigPropsGroup()
        alt_instance = AltSimpleConfigPropsGroup()
        parser_service.parse([self.__mock_simple_source()], [instance, alt_instance])
        self.assertEqual(instance.propA, True)
        self.assertEqual(instance.propB, 12)
        self.assertEqual(instance.propC, 'world')
        self.assertEqual(alt_instance.propA, True)

    def test_parse_group_does_not_extend_class(self):
        parser_service = ConfigParserService()
        instance = 'not_a_config_group'
        with self.assertRaises(ValueError) as context:
            parser_service.parse([self.__mock_simple_source()], [instance])
        self.assertEqual(str(context.exception), 'Property group instance provided must be a subclass of ConfigurationPropertiesGroup: not_a_config_group')

    def test_parse_nested(self):
        parser_service = ConfigParserService()
        instance = DatabasePropsGroup()
        parser_service.parse([self.__mock_nested_source()], [instance])
        self.assertEqual(instance.host, 'test')
        self.assertEqual(instance.port, 8080)


class TestDictSource(unittest.TestCase):

    def test_get(self):
        data_dict = {'hello': 'world'}
        source = DictSource(data_dict)
        self.assertEqual(source.get(), data_dict)


class TestYmlFileSource(unittest.TestCase):

    def test_get(self):
        test_file_path = os.path.join(os.path.dirname(__file__), 'test_config_files', 'yml_source.yml')
        source = YmlFileSource(test_file_path)
        yml_tpl = source.get()
        self.assertIsNotNone(yml_tpl)
        self.assertEqual(yml_tpl, {
            'application': {
                'database': {
                    'host': 'myhost',
                    'port': 7777
                }
            }})

    def test_get_required_fails_when_not_found(self):
        source = YmlFileSource('not_a_file.yml', required=True)
        with self.assertRaises(FileNotFoundError) as context:
            source.get()
        self.assertEqual(str(context.exception), 'File not found: not_a_file.yml')

    def test_get_non_required_returns_none(self):
        source = YmlFileSource('not_a_file.yml')
        self.assertIsNone(source.get())


class TestEnvironmentVariableYmlFileSource(unittest.TestCase):

    def setUp(self):
        os.environ['TEST_ENV_VAR'] = str(os.path.join(os.path.dirname(__file__), 'test_config_files', 'yml_source.yml'))
        os.environ['TEST_ENV_VAR_NOT_FOUND'] = 'not_a_file.yml'

    def test_get(self):
        source = EnvironmentVariableYmlFileSource('TEST_ENV_VAR')
        yml_tpl = source.get()
        self.assertIsNotNone(yml_tpl)
        self.assertEqual(yml_tpl, {
            'application': {
                'database': {
                    'host': 'myhost',
                    'port': 7777
                }
            }})

    def test_get_required_fails_when_not_found(self):
        source = EnvironmentVariableYmlFileSource('NOT_A_ENV_VAR', required=True)
        with self.assertRaises(EnvironmentSourceError) as context:
            source.get()
        self.assertEqual(str(context.exception), 'Required environment variable \'NOT_A_ENV_VAR\' not set')

    def test_get_required_fails_when_set_to_file_not_found(self):
        source = EnvironmentVariableYmlFileSource('TEST_ENV_VAR_NOT_FOUND', required=True)
        with self.assertRaises(FileNotFoundError) as context:
            source.get()
        self.assertEqual(str(context.exception), 'File not found: not_a_file.yml')

    def test_get_non_required_returns_none(self):
        source = EnvironmentVariableYmlFileSource('NOT_A_ENV_VAR')
        self.assertIsNone(source.get())
