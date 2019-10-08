from unittest.mock import patch, MagicMock
from .utils import ConfiguratorTestCase
from ignition.boot.config import BootstrapApplicationConfiguration, BootProperties
from ignition.boot.configurators.lifecycleapi import LifecycleApiConfigurator, LifecycleServicesConfigurator
from ignition.service.lifecycle import LifecycleProperties, LifecycleApiCapability, LifecycleServiceCapability, LifecycleScriptFileManagerCapability, LifecycleDriverCapability, LifecycleExecutionMonitoringCapability, LifecycleMessagingCapability, LifecycleApiService, LifecycleService, LifecycleScriptFileManagerService, LifecycleExecutionMonitoringService, LifecycleMessagingService
from ignition.service.messaging import TopicsProperties, PostalCapability, MessagingProperties
from ignition.service.queue import JobQueueCapability
from ignition.service.framework import Service, ServiceRegistration


class TestLifecycleApiConfigurator(ConfiguratorTestCase):

    def __bootstrap_config(self):
        configuration = BootstrapApplicationConfiguration()
        boot_config = BootProperties()
        configuration.property_groups.add_property_group(boot_config)
        lifecycle_config = LifecycleProperties()
        configuration.property_groups.add_property_group(lifecycle_config)
        messaging_config = MessagingProperties()
        messaging_config.connection_address = 'test'
        configuration.property_groups.add_property_group(messaging_config)
        return configuration

    def test_configure_nothing_when_api_enabled_is_false(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).lifecycle.api_enabled = False
        LifecycleApiConfigurator().configure(configuration, self.mock_service_register, self.mock_service_instances, self.mock_api_register)
        self.mock_service_register.add_service.assert_not_called()
        self.mock_api_register.register_api.assert_not_called()

    def test_configure_fails_when_api_spec_is_not_defined(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).lifecycle.api_enabled = True
        configuration.property_groups.get_property_group(LifecycleProperties).api_spec = None
        with self.assertRaises(ValueError) as context:
            LifecycleApiConfigurator().configure(configuration, self.mock_service_register, self.mock_service_instances, self.mock_api_register)
        self.assertEqual(str(context.exception), 'lifecycle.api_spec must be set when bootstrap.lifecycle.api_enabled is True')

    def test_configure_fails_when_api_service_not_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).lifecycle.api_enabled = True
        configuration.property_groups.get_property_group(LifecycleProperties).api_spec = 'vnfc_lifecycle.yml'
        self.mock_service_register.get_service_offering_capability.return_value = None
        with self.assertRaises(ValueError) as context:
            LifecycleApiConfigurator().configure(configuration, self.mock_service_register, self.mock_service_instances, self.mock_api_register)
        self.assertEqual(str(context.exception), 'No service has been registered with the LifecycleApiCapability, did you forget to register one? Or try enabling bootstrap.lifecycle.api_service_enabled')

    def test_configure_fails_when_api_service_instance_not_available(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).lifecycle.api_enabled = True
        configuration.property_groups.get_property_group(LifecycleProperties).api_spec = 'vnfc_lifecycle.yml'
        self.mock_service_register.get_service_offering_capability.return_value = LifecycleApiService
        self.mock_service_instances.get_instance.return_value = None
        with self.assertRaises(ValueError) as context:
            LifecycleApiConfigurator().configure(configuration, self.mock_service_register, self.mock_service_instances, self.mock_api_register)
        self.assertEqual(str(context.exception), 'No instance of the Lifecycle API service has been built')

    @patch('ignition.boot.configurators.lifecycleapi.build_resolver_to_instance')
    def test_configure_api(self, mock_build_resolver_to_instance):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).lifecycle.api_enabled = True
        configuration.property_groups.get_property_group(LifecycleProperties).api_spec = 'vnfc_lifecycle.yml'
        self.mock_service_register.get_service_offering_capability.return_value = LifecycleApiService
        mock_resolver = MagicMock()
        mock_build_resolver_to_instance.return_value = mock_resolver
        LifecycleApiConfigurator().configure(configuration, self.mock_service_register, self.mock_service_instances, self.mock_api_register)
        self.mock_service_register.get_service_offering_capability.assert_called_once_with(LifecycleApiCapability)
        self.mock_service_instances.get_instance.assert_called_once_with(LifecycleApiService)
        mock_build_resolver_to_instance.assert_called_once_with(self.mock_service_instances.get_instance.return_value)
        self.mock_api_register.register_api.assert_called_once_with('vnfc_lifecycle.yml', resolver=mock_resolver)


class TestLifecycleServicesConfigurator(ConfiguratorTestCase):

    def __bootstrap_config(self):
        configuration = BootstrapApplicationConfiguration()
        boot_config = BootProperties()
        configuration.property_groups.add_property_group(boot_config)
        lifecycle_config = LifecycleProperties()
        configuration.property_groups.add_property_group(lifecycle_config)
        messaging_config = MessagingProperties()
        messaging_config.connection_address = 'test'
        configuration.property_groups.add_property_group(messaging_config)
        return configuration

    def test_configure_nothing_when_disabled(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).lifecycle.api_service_enabled = False
        configuration.property_groups.get_property_group(BootProperties).lifecycle.service_enabled = False
        configuration.property_groups.get_property_group(BootProperties).lifecycle.service_enabled = False
        configuration.property_groups.get_property_group(BootProperties).lifecycle.monitoring_service_enabled = False
        configuration.property_groups.get_property_group(BootProperties).lifecycle.messaging_service_enabled = False
        self.mock_service_register.add_service.assert_not_called()

    def test_configure_api_service(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).lifecycle.api_service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = None
        LifecycleServicesConfigurator().configure(configuration, self.mock_service_register)
        registered_service = self.assert_single_service_registered()
        self.assert_service_registration_equal(registered_service, ServiceRegistration(LifecycleApiService, service=LifecycleServiceCapability))

    def test_configure_api_service_fails_when_already_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).lifecycle.api_service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            LifecycleServicesConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'An existing service has been registered to serve the Lifecycle API capability but bootstrap.lifecycle.api_service_enabled has not been disabled')

    class DummyDriver(Service, LifecycleDriverCapability):

        def execute_lifecycle(self, lifecycle_name, lifecycle_scripts_tree, system_properties, properties, deployment_location):
            pass

        def get_lifecycle_execution(self, request_id, deployment_location):
            pass

    def test_configure_service(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).lifecycle.service_enabled = True
        configuration.property_groups.get_property_group(BootProperties).lifecycle.service_driver = self.DummyDriver
        self.mock_service_register.get_service_offering_capability.return_value = None
        LifecycleServicesConfigurator().configure(configuration, self.mock_service_register)
        service_registrations = self.assert_services_registered(1)
        self.assert_service_registration_equal(service_registrations[0], ServiceRegistration(
            LifecycleService, driver=LifecycleDriverCapability, lifecycle_config=LifecycleProperties, script_file_manager=LifecycleScriptFileManagerCapability, lifecycle_monitor_service=LifecycleExecutionMonitoringCapability))

    def test_configure_service_does_not_include_monitoring_when_async_messaging_disabled(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).lifecycle.service_enabled = True
        configuration.property_groups.get_property_group(LifecycleProperties).async_messaging_enabled = False
        self.mock_service_register.get_service_offering_capability.return_value = None
        LifecycleServicesConfigurator().configure(configuration, self.mock_service_register)
        service_registrations = self.assert_services_registered(1)
        self.assert_service_registration_equal(service_registrations[0], ServiceRegistration(LifecycleService, driver=LifecycleDriverCapability,
                                                                                             lifecycle_config=LifecycleProperties, script_file_manager=LifecycleScriptFileManagerCapability))

    def test_configure_service_fails_when_already_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).lifecycle.service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            LifecycleServicesConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'An existing service has been registered to serve the Lifecycle Service capability but bootstrap.lifecycle.service_enabled has not been disabled')

    def test_configure_monitoring(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).lifecycle.monitoring_service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = None
        LifecycleServicesConfigurator().configure(configuration, self.mock_service_register)
        service_registrations = self.assert_services_registered(1)
        self.assert_service_registration_equal(service_registrations[0], ServiceRegistration(LifecycleExecutionMonitoringService,
                                                                                             job_queue_service=JobQueueCapability, lifecycle_messaging_service=LifecycleMessagingCapability, driver=LifecycleDriverCapability))

    def test_configure_monitoring_fails_when_already_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).lifecycle.monitoring_service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            LifecycleServicesConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'An existing service has been registered to serve the Lifecycle Execution Monitoring Service capability but bootstrap.lifecycle.monitoring_service_enabled has not been disabled')

    def test_configure_messaging(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).lifecycle.messaging_service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = None
        LifecycleServicesConfigurator().configure(configuration, self.mock_service_register)
        registered_service = self.assert_single_service_registered()
        self.assert_service_registration_equal(registered_service, ServiceRegistration(LifecycleMessagingService, postal_service=PostalCapability, topics_configuration=TopicsProperties))

    def test_configure_messaging_fails_when_already_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).lifecycle.messaging_service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            LifecycleServicesConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'An existing service has been registered to serve the Lifecycle Messaging Service capability but bootstrap.lifecycle.messaging_service_enabled has not been disabled')

    def test_configure_scripts_file_manager(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).lifecycle.script_file_manager_service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = None
        LifecycleServicesConfigurator().configure(configuration, self.mock_service_register)
        registered_service = self.assert_single_service_registered()
        self.assert_service_registration_equal(registered_service, ServiceRegistration(LifecycleScriptFileManagerService, lifecycle_config=LifecycleProperties))

    def test_configure_messaging_fails_when_already_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).lifecycle.script_file_manager_service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            LifecycleServicesConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'An existing service has been registered to serve the Lifecycle Script File Manager Service capability but bootstrap.lifecycle.script_file_manager_service_enabled has not been disabled')
