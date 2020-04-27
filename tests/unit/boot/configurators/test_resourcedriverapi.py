from unittest.mock import patch, MagicMock
from .utils import ConfiguratorTestCase
from ignition.boot.config import BootstrapApplicationConfiguration, BootProperties
from ignition.boot.configurators.resourcedriverapi import ResourceDriverApiConfigurator, ResourceDriverServicesConfigurator
from ignition.service.resourcedriver import ResourceDriverProperties, ResourceDriverApiCapability, ResourceDriverServiceCapability, DriverFilesManagerCapability, ResourceDriverHandlerCapability, LifecycleExecutionMonitoringCapability, LifecycleMessagingCapability, ResourceDriverApiService, ResourceDriverService, DriverFilesManagerService, LifecycleExecutionMonitoringService, LifecycleMessagingService
from ignition.service.messaging import TopicsProperties, PostalCapability, MessagingProperties
from ignition.service.queue import JobQueueCapability
from ignition.service.framework import Service, ServiceRegistration


class TestResourceDriverApiConfigurator(ConfiguratorTestCase):

    def __bootstrap_config(self):
        configuration = BootstrapApplicationConfiguration()
        boot_config = BootProperties()
        configuration.property_groups.add_property_group(boot_config)
        resource_driver_config = ResourceDriverProperties()
        configuration.property_groups.add_property_group(resource_driver_config)
        messaging_config = MessagingProperties()
        messaging_config.connection_address = 'test'
        configuration.property_groups.add_property_group(messaging_config)
        return configuration

    def test_configure_nothing_when_api_enabled_is_false(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).resource_driver.api_enabled = False
        ResourceDriverApiConfigurator().configure(configuration, self.mock_service_register, self.mock_service_instances, self.mock_api_register)
        self.mock_service_register.add_service.assert_not_called()
        self.mock_api_register.register_api.assert_not_called()

    def test_configure_fails_when_api_spec_is_not_defined(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).resource_driver.api_enabled = True
        configuration.property_groups.get_property_group(ResourceDriverProperties).api_spec = None
        with self.assertRaises(ValueError) as context:
            ResourceDriverApiConfigurator().configure(configuration, self.mock_service_register, self.mock_service_instances, self.mock_api_register)
        self.assertEqual(str(context.exception), 'resource_driver.api_spec must be set when bootstrap.resource_driver.api_enabled is True')

    def test_configure_fails_when_api_service_not_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).resource_driver.api_enabled = True
        configuration.property_groups.get_property_group(ResourceDriverProperties).api_spec = 'resource-driver.yaml'
        self.mock_service_register.get_service_offering_capability.return_value = None
        with self.assertRaises(ValueError) as context:
            ResourceDriverApiConfigurator().configure(configuration, self.mock_service_register, self.mock_service_instances, self.mock_api_register)
        self.assertEqual(str(context.exception), 'No service has been registered with the ResourceDriverApiCapability, did you forget to register one? Or try enabling bootstrap.resource_driver.api_service_enabled')

    def test_configure_fails_when_api_service_instance_not_available(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).resource_driver.api_enabled = True
        configuration.property_groups.get_property_group(ResourceDriverProperties).api_spec = 'resource-driver.yaml'
        self.mock_service_register.get_service_offering_capability.return_value = ResourceDriverApiService
        self.mock_service_instances.get_instance.return_value = None
        with self.assertRaises(ValueError) as context:
            ResourceDriverApiConfigurator().configure(configuration, self.mock_service_register, self.mock_service_instances, self.mock_api_register)
        self.assertEqual(str(context.exception), 'No instance of the Resource Driver API service has been built')

    @patch('ignition.boot.configurators.resourcedriverapi.build_resolver_to_instance')
    def test_configure_api(self, mock_build_resolver_to_instance):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).resource_driver.api_enabled = True
        configuration.property_groups.get_property_group(ResourceDriverProperties).api_spec = 'resource-driver.yaml'
        self.mock_service_register.get_service_offering_capability.return_value = ResourceDriverApiService
        mock_resolver = MagicMock()
        mock_build_resolver_to_instance.return_value = mock_resolver
        ResourceDriverApiConfigurator().configure(configuration, self.mock_service_register, self.mock_service_instances, self.mock_api_register)
        self.mock_service_register.get_service_offering_capability.assert_called_once_with(ResourceDriverApiCapability)
        self.mock_service_instances.get_instance.assert_called_once_with(ResourceDriverApiService)
        mock_build_resolver_to_instance.assert_called_once_with(self.mock_service_instances.get_instance.return_value)
        self.mock_api_register.register_api.assert_called_once_with('resource-driver.yaml', resolver=mock_resolver)


class TestResourceDriverServicesConfigurator(ConfiguratorTestCase):

    def __bootstrap_config(self):
        configuration = BootstrapApplicationConfiguration()
        boot_config = BootProperties()
        configuration.property_groups.add_property_group(boot_config)
        resource_driver_config = ResourceDriverProperties()
        configuration.property_groups.add_property_group(resource_driver_config)
        messaging_config = MessagingProperties()
        messaging_config.connection_address = 'test'
        configuration.property_groups.add_property_group(messaging_config)
        return configuration

    def test_configure_nothing_when_disabled(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).resource_driver.api_service_enabled = False
        configuration.property_groups.get_property_group(BootProperties).resource_driver.service_enabled = False
        configuration.property_groups.get_property_group(BootProperties).resource_driver.service_enabled = False
        configuration.property_groups.get_property_group(BootProperties).resource_driver.lifecycle_monitoring_service_enabled = False
        configuration.property_groups.get_property_group(BootProperties).resource_driver.lifecycle_messaging_service_enabled = False
        ResourceDriverServicesConfigurator().configure(configuration, self.mock_service_register)
        self.mock_service_register.add_service.assert_not_called()

    def test_configure_api_service(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).resource_driver.api_service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = None
        ResourceDriverServicesConfigurator().configure(configuration, self.mock_service_register)
        registered_service = self.assert_single_service_registered()
        self.assert_service_registration_equal(registered_service, ServiceRegistration(ResourceDriverApiService, service=ResourceDriverServiceCapability))

    def test_configure_api_service_fails_when_already_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).resource_driver.api_service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            ResourceDriverServicesConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'An existing service has been registered to serve the Resource Driver API capability but bootstrap.resource_driver.api_service_enabled has not been disabled')

    class DummyDriver(Service, ResourceDriverHandlerCapability):

        def execute_lifecycle(self, lifecycle_name, driver_files, system_properties, resource_properties, request_properties, internal_resources, deployment_location):
            pass

        def get_lifecycle_execution(self, request_id, deployment_location):
            pass
            
        def find_reference(self, instance_name, driver_files, deployment_location):
            pass

    def test_configure_service(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).resource_driver.service_enabled = True
        configuration.property_groups.get_property_group(BootProperties).resource_driver.service_driver = self.DummyDriver
        self.mock_service_register.get_service_offering_capability.return_value = None
        ResourceDriverServicesConfigurator().configure(configuration, self.mock_service_register)
        service_registrations = self.assert_services_registered(1)
        self.assert_service_registration_equal(service_registrations[0], ServiceRegistration(
            ResourceDriverService, handler=ResourceDriverHandlerCapability, resource_driver_config=ResourceDriverProperties, driver_files_manager=DriverFilesManagerCapability, lifecycle_monitor_service=LifecycleExecutionMonitoringCapability))

    def test_configure_service_does_not_include_monitoring_when_async_messaging_disabled(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).resource_driver.service_enabled = True
        configuration.property_groups.get_property_group(ResourceDriverProperties).async_messaging_enabled = False
        self.mock_service_register.get_service_offering_capability.return_value = None
        ResourceDriverServicesConfigurator().configure(configuration, self.mock_service_register)
        service_registrations = self.assert_services_registered(1)
        self.assert_service_registration_equal(service_registrations[0], ServiceRegistration(ResourceDriverService, handler=ResourceDriverHandlerCapability,
                                                                                             resource_driver_config=ResourceDriverProperties, driver_files_manager=DriverFilesManagerCapability))

    def test_configure_service_fails_when_already_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).resource_driver.service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            ResourceDriverServicesConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'An existing service has been registered to serve the Resource Driver Service capability but bootstrap.resource_driver.service_enabled has not been disabled')

    def test_configure_monitoring(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).resource_driver.lifecycle_monitoring_service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = None
        ResourceDriverServicesConfigurator().configure(configuration, self.mock_service_register)
        service_registrations = self.assert_services_registered(1)
        self.assert_service_registration_equal(service_registrations[0], ServiceRegistration(LifecycleExecutionMonitoringService,
                                                                                             job_queue_service=JobQueueCapability, lifecycle_messaging_service=LifecycleMessagingCapability, handler=ResourceDriverHandlerCapability))

    def test_configure_monitoring_fails_when_already_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).resource_driver.lifecycle_monitoring_service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            ResourceDriverServicesConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'An existing service has been registered to serve the Resource Driver Lifecycle Execution Monitoring Service capability but bootstrap.resource_driver.lifecycle_monitoring_service_enabled has not been disabled')

    def test_configure_messaging(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).resource_driver.lifecycle_messaging_service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = None
        ResourceDriverServicesConfigurator().configure(configuration, self.mock_service_register)
        registered_service = self.assert_single_service_registered()
        self.assert_service_registration_equal(registered_service, ServiceRegistration(LifecycleMessagingService, postal_service=PostalCapability, topics_configuration=TopicsProperties))

    def test_configure_messaging_fails_when_already_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).resource_driver.lifecycle_messaging_service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            ResourceDriverServicesConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'An existing service has been registered to serve the Resource Driver Lifecycle Messaging Service capability but bootstrap.resource_driver.lifecycle_messaging_service_enabled has not been disabled')

    def test_configure_scripts_file_manager(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).resource_driver.driver_files_manager_service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = None
        ResourceDriverServicesConfigurator().configure(configuration, self.mock_service_register)
        registered_service = self.assert_single_service_registered()
        self.assert_service_registration_equal(registered_service, ServiceRegistration(DriverFilesManagerService, resource_driver_config=ResourceDriverProperties))

    def test_configure_messaging_fails_when_already_registered(self):
        configuration = self.__bootstrap_config()
        configuration.property_groups.get_property_group(BootProperties).resource_driver.driver_files_manager_service_enabled = True
        self.mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            ResourceDriverServicesConfigurator().configure(configuration, self.mock_service_register)
        self.assertEqual(str(context.exception), 'An existing service has been registered to serve the Driver File Manager Service capability but bootstrap.resource_driver.driver_files_manager_service_enabled has not been disabled')
