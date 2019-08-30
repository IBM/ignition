import unittest
from ignition.service.api import BaseController
from ignition.api.exceptions import BadRequest

class TestBaseController(unittest.TestCase):

    def test_get_body(self):
        controller = BaseController()
        body = controller.get_body({'body': '123'})
        self.assertEqual(body, '123')

    def test_get_body_throws_error_when_no_body(self):
        controller = BaseController()
        with self.assertRaises(BadRequest) as context:
            controller.get_body({'notbody': '123'})
        self.assertEqual(str(context.exception), 'No body found in request data')

    def test_get_body_required_field(self):
        controller = BaseController()
        body = {'name': 'TestName'}
        field_value = controller.get_body_required_field(body, 'name')
        self.assertEqual(field_value, 'TestName')

    def test_get_body_required_field_throws_error_when_not_found(self):
        controller = BaseController()
        body = {'name': 'TestName'}
        with self.assertRaises(BadRequest) as context:
            field_value = controller.get_body_required_field(body, 'age')
        self.assertEqual(str(context.exception), '\'age\' is a required field but was not found in the request data body')

    def test_get_body_field(self):
        controller = BaseController()
        body = {'name': 'TestName'}
        field_value = controller.get_body_field(body, 'name')
        self.assertEqual(field_value, 'TestName')
    
    def test_get_body_field_returns_default_when_not_found(self):
        controller = BaseController()
        body = {'name': 'TestName'}
        field_value = controller.get_body_field(body, 'age', 50)
        self.assertEqual(field_value, 50)