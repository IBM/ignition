import unittest
from ignition.service.framework import ServiceRegistration

class ConfiguratorTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_service_register = unittest.mock.MagicMock()
        self.mock_service_instances = unittest.mock.MagicMock()
        self.mock_api_register = unittest.mock.MagicMock()

    def assert_service_registration_equal(self, registered_service, expected_service_registration):
        self.assertEqual(registered_service.service_class, expected_service_registration.service_class)
        self.assertEqual(registered_service.args, expected_service_registration.args)
        self.assertEqual(registered_service.required_capabilities, expected_service_registration.required_capabilities)

    def assert_single_service_registered(self):
        add_service_calls = self.mock_service_register.add_service.call_args_list
        self.assertEqual(len(add_service_calls), 1)
        add_service_call = add_service_calls[0]
        add_service_call_args, kwargs = add_service_call
        self.assertEqual(len(add_service_call_args), 1)
        registered_service = add_service_call_args[0]
        self.assertIsInstance(registered_service, ServiceRegistration)
        return registered_service

    def assert_services_registered(self, expected_number):
        add_service_calls = self.mock_service_register.add_service.call_args_list
        self.assertEqual(len(add_service_calls), expected_number)
        service_registrations = []
        for add_service_call in add_service_calls:
            add_service_call_args, kwargs = add_service_call
            self.assertEqual(len(add_service_call_args), 1)
            registered_service = add_service_call_args[0]
            self.assertIsInstance(registered_service, ServiceRegistration)
            service_registrations.append(registered_service)
        return service_registrations
