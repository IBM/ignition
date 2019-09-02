import unittest
from unittest.mock import MagicMock
from abc import ABC, abstractmethod
from ignition.service.framework import ServiceRegister, ServiceRegistration, ServiceInstances, ServiceInitialiser, Service, Capability, RequirementNotACapabilityException, NoServiceInstanceException, ServiceNotFoundException, RequiredCapabilityNotOffered, CyclicDependencyException, NotAServiceException, DuplicateServiceException, DuplicateCapabilityException

class MessagingCapability(Capability, ABC):

    @abstractmethod
    def send_message(self, message):
        pass

class MessagingService(Service, MessagingCapability):

    def send_message(self, message):
        pretend_to_send = message

class AnotherMessagingService(Service, MessagingCapability):

    def send_message(self, message):
        pretend_to_send = message

class MonitoringCapability(Capability, ABC):

    @abstractmethod
    def monitor(self, monitored_item):
        pass

class MonitoringService(Service, MonitoringCapability):

    def monitor(self, monitored_item):
        pretend_to_monitor = monitored_item

class HealthCheckCapability(Capability, ABC):

    @abstractmethod
    def check(self, item):
        pass

class HealthCheckService(Service, HealthCheckCapability):
    
    def check(self, item):
        pretend_to_check = item

class MultiService(Service, HealthCheckCapability, MonitoringCapability):

    def monitor(self, monitored_item):
        pretend_to_monitor = monitored_item

    def check(self, item):
        pretend_to_check = item

class PersistenceCapability(Capability, ABC):

    @abstractmethod
    def persist(self, entity):
        pass

class PersistenceService(Service, PersistenceCapability):

    def persist(self, entity):
        pretend_to_persist = entity

class TestServiceRegister(unittest.TestCase):

    def test_add_service(self):
        register = ServiceRegister()
        service_class = MessagingService
        register.add_service(ServiceRegistration(service_class))
        services = register.get_services()
        self.assertEqual(len(services), 1)
        self.assertIn(service_class, services)
        self.assertEqual(service_class, register.get_service_offering_capability(MessagingCapability))
        capabilities = register.get_capabilities()
        self.assertEqual(len(capabilities), 2)
        self.assertIn(MessagingService, capabilities)
        self.assertIn(MessagingCapability, capabilities)

    def test_add_non_service_class_throws_error(self):
        register = ServiceRegister()
        service_class = Exception
        with self.assertRaises(NotAServiceException) as context:
            register.add_service(ServiceRegistration(service_class))
        self.assertEqual(str(context.exception), 'Service class argument given is not a subclass of Service: <class \'Exception\'>')
        self.assertEqual(context.exception.problem_class, service_class)

    def test_add_duplicate_service_class_throws_error(self):
        register = ServiceRegister()
        service_class = MessagingService
        register.add_service(ServiceRegistration(service_class))
        with self.assertRaises(DuplicateServiceException) as context:
            register.add_service(ServiceRegistration(service_class))
        self.assertEqual(str(context.exception), 'Attempting to add a duplicate service: {0}'.format(MessagingService))
        self.assertEqual(context.exception.service_class, service_class)

    def test_add_service_with_same_capability_throws_error(self):
        register = ServiceRegister()
        service_class = MessagingService
        register.add_service(ServiceRegistration(service_class))
        with self.assertRaises(DuplicateCapabilityException) as context:
            register.add_service(ServiceRegistration(AnotherMessagingService))
        self.assertEqual(str(context.exception), 'Service \'{0}\' offers capability \'{1}\' which has already been offered by \'{2}\''.format(AnotherMessagingService, MessagingCapability, MessagingService))
        self.assertEqual(context.exception.offending_service_class, AnotherMessagingService)
        self.assertEqual(context.exception.original_service_class, MessagingService)
        self.assertEqual(context.exception.capability_class, MessagingCapability)

    def test_add_service_with_requirements(self):
        register = ServiceRegister()
        register.add_service(ServiceRegistration(MessagingService))
        register.add_service(ServiceRegistration(HealthCheckService))
        register.add_service(ServiceRegistration(MonitoringService, messaging_service=MessagingCapability, health_check=HealthCheckCapability))
        monitoring_required_capabilities = register.get_service_required_capabilities(MonitoringService)
        self.assertEqual(2, len(monitoring_required_capabilities))
        self.assertIn(MessagingCapability, monitoring_required_capabilities)
        self.assertIn(HealthCheckCapability, monitoring_required_capabilities)

    def test_add_service_with_requirement_to_unknown_capability_adds_capability(self):
        register = ServiceRegister()
        register.add_service(ServiceRegistration(MonitoringService, messaging_service=MessagingCapability))
        capabilities = register.get_capabilities()
        self.assertEqual(3, len(capabilities))
        self.assertIn(MonitoringCapability, capabilities)
        self.assertIn(MonitoringService, capabilities)
        self.assertIn(MessagingCapability, capabilities)
        monitoring_required_capabilities = register.get_service_required_capabilities(MonitoringService)
        self.assertEqual(1, len(monitoring_required_capabilities))
        self.assertIn(MessagingCapability, monitoring_required_capabilities)
        # Can still add Service later
        register.add_service(ServiceRegistration(MessagingService))
        capabilities = register.get_capabilities()
        self.assertEqual(4, len(capabilities))
        self.assertIn(MonitoringCapability, capabilities)
        self.assertIn(MonitoringService, capabilities)
        self.assertIn(MessagingCapability, capabilities)
        self.assertIn(MessagingService, capabilities)

    def test_add_service_with_requirement_to_non_capability_throws_error(self):
        register = ServiceRegister()
        with self.assertRaises(RequirementNotACapabilityException) as context:
            register.add_service(ServiceRegistration(MonitoringService, helper=unittest.TestCase))
        self.assertEqual(str(context.exception), 'Service \'{0}\' not allowed requirement to class \'{1}\' as it does not subclass Capability'.format(MonitoringService, unittest.TestCase))
        self.assertEqual(context.exception.service_class, MonitoringService)
        self.assertEqual(context.exception.offending_capability_class, unittest.TestCase)

    def test_add_service_with_multiple_capabilities(self):
        register = ServiceRegister()
        register.add_service(ServiceRegistration(MultiService))
        capabilities = register.get_capabilities()
        self.assertEqual(3, len(capabilities))
        self.assertIn(MultiService, capabilities)
        self.assertIn(MonitoringCapability, capabilities)
        self.assertIn(HealthCheckCapability, capabilities)

    def test_get_service_offering_capability_no_service_found_returns_none(self):
        register = ServiceRegister()
        service = register.get_service_offering_capability(HealthCheckCapability)
        self.assertIsNone(service)

    def test_get_service_required_capabilities_with_none_returns_none(self):
        register = ServiceRegister()
        register.add_service(ServiceRegistration(MessagingService))
        requirements = register.get_service_required_capabilities(MessagingService)
        self.assertEqual(0, len(requirements))

    def test_get_service_required_capabilities_with_service_not_found_throws_error(self):
        register = ServiceRegister()
        with self.assertRaises(ServiceNotFoundException) as context:
            register.get_service_required_capabilities(MessagingService)
        self.assertEqual(str(context.exception), 'Service \'{0}\' not found'.format(MessagingService))
        self.assertEqual(context.exception.service_class, MessagingService)

    def test_get_service_requirements(self):
        register = ServiceRegister()
        register.add_service(ServiceRegistration(HealthCheckService, messaging=MessagingCapability, monitoring=MonitoringCapability))
        requirements = register.get_service_requirements(HealthCheckService)
        self.assertEqual(2, len(requirements))
        self.assertIn('messaging', requirements)
        self.assertIn('monitoring', requirements)
        self.assertEqual(requirements['messaging'], MessagingCapability)
        self.assertEqual(requirements['monitoring'], MonitoringCapability)

    def test_order_services_by_requirements(self):
        register = ServiceRegister()
        register.add_service(ServiceRegistration(HealthCheckService, messaging=MessagingCapability, monitoring=MonitoringCapability))
        register.add_service(ServiceRegistration(MonitoringService, messaging=MessagingCapability))
        register.add_service(ServiceRegistration(MessagingService))
        register.add_service(ServiceRegistration(PersistenceService))
        ordered_services = register.order_services_by_requirements()
        self.assertEqual(4, len(ordered_services))
        self.assertIn(HealthCheckService, ordered_services)
        self.assertIn(MonitoringService, ordered_services)
        self.assertIn(MessagingService, ordered_services)
        self.assertIn(PersistenceService, ordered_services)
        self.assertTrue(ordered_services.index(HealthCheckService) > ordered_services.index(MonitoringService))
        self.assertTrue(ordered_services.index(HealthCheckService) > ordered_services.index(MessagingService))
        self.assertTrue(ordered_services.index(MonitoringService) > ordered_services.index(MessagingService))
    
    def test_order_services_by_requirements_with_cyclic_dependency_throws_error(self):
        register = ServiceRegister()
        register.add_service(ServiceRegistration(HealthCheckService, monitoring=MonitoringCapability))
        register.add_service(ServiceRegistration(MonitoringService, health=HealthCheckCapability))
        register.add_service(ServiceRegistration(MessagingService, persistence=PersistenceCapability))
        register.add_service(ServiceRegistration(PersistenceService, persistence=MessagingCapability))
        with self.assertRaises(CyclicDependencyException) as context:
            register.order_services_by_requirements()
        self.assertEqual(2, len(context.exception.cyclic_dependencies))
        if context.exception.cyclic_dependencies[0].first_dependent is PersistenceService:
            self.assertEqual(MessagingService, context.exception.cyclic_dependencies[0].second_dependent)
        else:
            self.assertEqual(MessagingService, context.exception.cyclic_dependencies[0].first_dependent)
            self.assertEqual(PersistenceService, context.exception.cyclic_dependencies[0].second_dependent)
        if context.exception.cyclic_dependencies[1].first_dependent is HealthCheckService:
            self.assertEqual(MonitoringService, context.exception.cyclic_dependencies[1].second_dependent)
        else:
            self.assertEqual(MonitoringService, context.exception.cyclic_dependencies[1].first_dependent)
            self.assertEqual(HealthCheckService, context.exception.cyclic_dependencies[1].second_dependent)

    def test_order_services_by_requirements_no_service_for_capability_throws_error(self):
        register = ServiceRegister()
        register.add_service(ServiceRegistration(MonitoringService, messaging=MessagingCapability))
        with self.assertRaises(RequiredCapabilityNotOffered) as context:
            register.order_services_by_requirements()
        self.assertEqual(str(context.exception), 'No service found offering capability \'{0}\' required by service \'{1}\''.format(MessagingCapability, MonitoringService))
        self.assertEqual(context.exception.capability_class, MessagingCapability)
        self.assertEqual(context.exception.required_by_service_class, MonitoringService)

class TestServiceInstances(unittest.TestCase):

    def test_add_and_get_instance(self):
        service_instances = ServiceInstances()
        messaging_instance = MessagingService()
        monitoring_instance = MonitoringService()
        service_instances.add_instance_of(messaging_instance, MessagingService)
        service_instances.add_instance_of(monitoring_instance, MonitoringService)
        get_messaging_service = service_instances.get_instance(MessagingService)
        self.assertEqual(get_messaging_service, messaging_instance)
        get_monitoring_service = service_instances.get_instance(MonitoringService)
        self.assertEqual(get_monitoring_service, monitoring_instance)

    def test_add_instance_of_same_service_class_throws_error(self):
        service_instances = ServiceInstances()
        messaging_instance = MessagingService()
        service_instances.add_instance_of(messaging_instance, MessagingService)
        with self.assertRaises(ValueError) as context:
            service_instances.add_instance_of(messaging_instance, MessagingService)
        self.assertEqual(str(context.exception), 'Instances already exists for service_class: {0}'.format(MessagingService))
        
    def test_get_instance_not_found_returns_none(self):
        service_instances = ServiceInstances()
        result = service_instances.get_instance(MessagingService)
        self.assertIsNone(result)

class SimpleCapability(Capability):
    pass

class SimpleService(Service, SimpleCapability):
    pass


class ServiceWithCapturedArgs(Service, Capability):
    
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

class TestServiceInitialiser(unittest.TestCase):

    def test_build_instances(self):
        service_instances = ServiceInstances()
        service_register = ServiceRegister()
        service_register.add_service(ServiceRegistration(ServiceWithCapturedArgs))
        initialiser = ServiceInitialiser(service_instances, service_register)
        initialiser.build_instances()
        captured_instance = service_instances.get_instance(ServiceWithCapturedArgs)
        self.assertEqual(captured_instance.args, ())
        self.assertEqual(captured_instance.kwargs, {})

    def test_build_instance_with_args(self):
        service_instances = ServiceInstances()
        service_register = ServiceRegister()
        service_register.add_service(ServiceRegistration(ServiceWithCapturedArgs, 'testarg', 1))
        initialiser = ServiceInitialiser(service_instances, service_register)
        initialiser.build_instances()
        captured_instance = service_instances.get_instance(ServiceWithCapturedArgs)
        self.assertEqual(captured_instance.args, ('testarg', 1))
        self.assertEqual(captured_instance.kwargs, {})

    def test_build_instances_does_not_build_provided(self):
        mock_service_instances = MagicMock()
        mock_service_register = MagicMock()
        mock_service_class = MagicMock()
        initialiser = ServiceInitialiser(mock_service_instances, mock_service_register)
        mock_service_register.order_services_by_requirements.return_value = [mock_service_class]
        mock_service_register.is_service_set_as_provided.return_value = True
        initialiser.build_instances()
        mock_service_class.assert_not_called()
        mock_service_instances.add_instance_of.assert_not_called()

    def test_build_instance_with_requirements(self):
        service_instances = ServiceInstances()
        service_register = ServiceRegister()
        service_register.add_service(ServiceRegistration(SimpleService))
        service_register.add_service(ServiceRegistration(ServiceWithCapturedArgs, simple_service=SimpleCapability))
        initialiser = ServiceInitialiser(service_instances, service_register)
        initialiser.build_instances()
        simple_instance = service_instances.get_instance(SimpleService)
        self.assertIsNotNone(simple_instance)
        self.assertIsInstance(simple_instance, SimpleService)
        captured_instance = service_instances.get_instance(ServiceWithCapturedArgs)
        self.assertIsNotNone(captured_instance)
        self.assertIsInstance(captured_instance, ServiceWithCapturedArgs)
        self.assertEqual(captured_instance.args, ())
        self.assertEqual(captured_instance.kwargs, {'simple_service': simple_instance})

    def test_build_instance_with_requirement_to_provided_instance(self):
        service_instances = ServiceInstances()
        service_register = ServiceRegister()
        provided_instance = SimpleService()
        service_instances.add_instance_of(provided_instance, SimpleService)
        simple_service_registration = ServiceRegistration(SimpleService)
        simple_service_registration.provided = True
        service_register.add_service(simple_service_registration)
        service_register.add_service(ServiceRegistration(ServiceWithCapturedArgs, simple_service=SimpleCapability))
        initialiser = ServiceInitialiser(service_instances, service_register)
        initialiser.build_instances()
        captured_instance = service_instances.get_instance(ServiceWithCapturedArgs)
        self.assertIsNotNone(captured_instance)
        self.assertIsInstance(captured_instance, ServiceWithCapturedArgs)
        self.assertEqual(captured_instance.args, ())
        self.assertEqual(captured_instance.kwargs, {'simple_service': provided_instance})

    def test_build_instance_with_requirement_to_capability_with_no_service_throws_error(self):
        service_instances = ServiceInstances()
        service_register = ServiceRegister()
        service_register.add_service(ServiceRegistration(ServiceWithCapturedArgs, simple_service=SimpleCapability))
        initialiser = ServiceInitialiser(service_instances, service_register)
        with self.assertRaises(RequiredCapabilityNotOffered) as context:
            initialiser.build_instances()
        self.assertEqual(str(context.exception), 'No service found offering capability \'{0}\' required by service \'{1}\''.format(SimpleCapability, ServiceWithCapturedArgs))
        self.assertEqual(context.exception.capability_class, SimpleCapability)
        self.assertEqual(context.exception.required_by_service_class, ServiceWithCapturedArgs)

    def test_build_instance_with_requirement_to_service_without_an_instance_throws_error(self):
        service_instances = ServiceInstances()
        service_register = ServiceRegister()
        provided_instance = SimpleService()
        simple_service_registration = ServiceRegistration(SimpleService)
        # Never add an instance to service_instances
        simple_service_registration.provided = True
        service_register.add_service(simple_service_registration)
        service_register.add_service(ServiceRegistration(ServiceWithCapturedArgs, simple_service=SimpleCapability))
        initialiser = ServiceInitialiser(service_instances, service_register)
        with self.assertRaises(NoServiceInstanceException) as context:
            initialiser.build_instances()
        self.assertEqual(str(context.exception), 'No instance of service \'{0}\' has been created, required by \'{1}\''.format(SimpleService, ServiceWithCapturedArgs))
        self.assertEqual(context.exception.service_class, SimpleService)
        self.assertEqual(context.exception.required_by_service_class, ServiceWithCapturedArgs)
