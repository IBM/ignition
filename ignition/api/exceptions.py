import json
import inspect
import logging
from werkzeug.exceptions import HTTPException
from werkzeug.wrappers import Response

logger = logging.getLogger(__name__)


class ApiException(Exception):
    pass


class HandlerEntry():

    def __init__(self, exception_type, handler):
        if not inspect.isclass(exception_type):
            raise ValueError('exception_type must be a class type')
        if not callable(handler):
            raise ValueError('handler must be a callable type')
        handler_args = inspect.getfullargspec(handler).args
        valid_handler = (len(handler_args) == 1) or (len(handler_args) == 2 and handler_args[0] == 'self')
        if not valid_handler:
            raise ValueError('handler must accept a single argument (excluding self)')
        self.exception_type = exception_type
        self.handler = handler


class ErrorResponseConverter():

    def __init__(self):
        self.handlers = []

    def register_handler(self, exception_type, handler):
        self.handlers.append(HandlerEntry(exception_type, handler))

    def handle(self, exception):
        logger.exception('API error occurred: {0}'.format(exception))
        error_response = {
            'localizedMessage': str(exception),
            'status': 500
        }
        if isinstance(exception, HTTPException) and hasattr(exception, 'code'):
            error_response['status'] = exception.code
        elif isinstance(exception, ApiException) and hasattr(exception, 'status_code'):
            error_response['status'] = exception.status_code
        for handler_entry in self.handlers:
            handler_exception_type = handler_entry.exception_type
            if isinstance(exception, handler_exception_type):
                handler_func = handler_entry.handler
                handler_response = handler_func(exception)
                if isinstance(handler_response, dict):
                    for key, value in handler_response.items():
                        error_response[key] = value
        status = error_response['status']
        return Response(json.dumps(error_response), status=status, mimetype="application/json")


def validation_error_handler(exception):
    return {'status': 400}


class BadRequest(ApiException):
    status_code = 400
