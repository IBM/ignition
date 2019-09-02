import unittest
from unittest.mock import MagicMock
from ignition.boot.configurators.utils import validate_no_service_with_capability_exists
from ignition.service.framework import Capability

class DummyCapability(Capability):
    pass

class Test_validate_no_service_with_capability_exists(unittest.TestCase):

    def test_validate_no_service_with_capability_exists(self):
        mock_service_register = MagicMock()
        mock_service_register.get_service_offering_capability.return_value = None
        validate_no_service_with_capability_exists(mock_service_register, DummyCapability, 'Dummy', 'a.b.c')
        mock_service_register.get_service_offering_capability.assert_called_once_with(DummyCapability)

    def test_validate_no_service_with_capability_exists_throws_error_when_exists(self):
        mock_service_register = MagicMock()
        mock_service_register.get_service_offering_capability.return_value = MagicMock()
        with self.assertRaises(ValueError) as context:
            validate_no_service_with_capability_exists(mock_service_register, DummyCapability, 'Dummy', 'a.b.c')
        self.assertEqual(str(context.exception), 'An existing service has been registered to serve the Dummy capability but a.b.c has not been disabled')
        
