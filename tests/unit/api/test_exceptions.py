import unittest
from unittest.mock import MagicMock
import json
from ignition.api.exceptions import ErrorResponseConverter, HandlerEntry
from werkzeug.exceptions import NotFound, Conflict

def single_arg_handler(exception):
    return {'status': 418, 'localizedMessage': 'Single Arg Handler'}

def invalid_mulit_arg_handler(exception, not_allowed):
    return {'status': 418, 'localizedMessage': 'Multi Arg Handler'}

class TestErrorResponseConverter(unittest.TestCase):

    def single_arg_with_self_handler(self, exception):
        return {'status': 418}

    def test_register_handler_to_non_exception(self):
        converter = ErrorResponseConverter()
        with self.assertRaises(ValueError) as context:
            converter.register_handler('abc', single_arg_handler)
        self.assertEqual(str(context.exception), 'exception_type must be a class type')
    
    def test_register_handler_not_callable(self):
        converter = ErrorResponseConverter()
        with self.assertRaises(ValueError) as context:
            converter.register_handler(Exception, 'abc')
        self.assertEqual(str(context.exception), 'handler must be a callable type')

    def test_register_handler_accepts_handler_with_single_arg(self):
        converter = ErrorResponseConverter()
        converter.register_handler(Exception, single_arg_handler)
        self.assertEqual(len(converter.handlers), 1)
        handler_entry_for_exception = converter.handlers[0]
        self.assertIsInstance(handler_entry_for_exception, HandlerEntry)
        self.assertEqual(handler_entry_for_exception.handler, single_arg_handler)
        self.assertEqual(handler_entry_for_exception.exception_type, Exception)

    def test_register_handler_accepts_handler_with_single_arg_and_self(self):
        converter = ErrorResponseConverter()
        converter.register_handler(Exception, self.single_arg_with_self_handler)
        self.assertEqual(len(converter.handlers), 1)
        handler_entry_for_exception = converter.handlers[0]
        self.assertIsInstance(handler_entry_for_exception, HandlerEntry)
        self.assertEqual(handler_entry_for_exception.handler, self.single_arg_with_self_handler)
        self.assertEqual(handler_entry_for_exception.exception_type, Exception)

    def test_register_handler_does_not_accept_multi_arg(self):
        converter = ErrorResponseConverter()
        with self.assertRaises(ValueError) as context:
            converter.register_handler(Exception, invalid_mulit_arg_handler)
        self.assertEqual(str(context.exception), 'handler must accept a single argument (excluding self)')

    def test_handle_defaults(self):
        converter = ErrorResponseConverter()
        response = converter.handle(Exception())
        self.assertEqual(500, response.status_code)
        actual_body = json.loads(response.get_data())
        self.assertEqual(str(Exception()), actual_body['localizedMessage'])
        self.assertEqual(500, actual_body['status'])

    def test_handle_http_exception_code(self):
        converter = ErrorResponseConverter()
        response = converter.handle(NotFound())
        self.assertEqual(404, response.status_code)
        actual_body = json.loads(response.get_data())
        self.assertEqual(str(NotFound()), actual_body['localizedMessage'])
        self.assertEqual(404, actual_body['status'])

    def test_handle_http_exception_override(self):
        converter = ErrorResponseConverter()
        def override_conflict(exception):
            return {'status': 400, 'localizedMessage': 'That was bad'}
        converter.register_handler(Conflict, override_conflict)
        response = converter.handle(Conflict())
        self.assertEqual(400, response.status_code)
        actual_body = json.loads(response.get_data())
        self.assertEqual('That was bad', actual_body['localizedMessage'])
        self.assertEqual(400, actual_body['status'])

    def test_handler_adds_additional_keys(self):
        converter = ErrorResponseConverter()
        def handler(exception):
            return {'added_key': 'some_other_data'}
        converter.register_handler(Exception, handler)
        response = converter.handle(Exception())
        self.assertEqual(500, response.status_code)
        actual_body = json.loads(response.get_data())
        self.assertEqual(str(Exception()), actual_body['localizedMessage'])
        self.assertEqual(500, actual_body['status'])
        self.assertEqual('some_other_data', actual_body['added_key'])