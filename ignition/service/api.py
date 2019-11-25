from ignition.api.exceptions import BadRequest

class BaseController():

    def get_required_param(self, request_data, param_name):
        if param_name not in request_data:
            raise BadRequest('\'{0}\' is a required param but was not found in the request data'.format(param_name))
        return request_data.get(param_name)

    def get_param(self, request_data, param_name, default_value=None):
        return request_data.get(param_name, default_value)

    def get_body(self, request_data):
        if 'body' not in request_data:
            raise BadRequest('No body found in request data')
        return request_data.get('body')

    def get_body_required_field(self, body, field_name):
        if field_name not in body:
            raise BadRequest('\'{0}\' is a required field but was not found in the request data body'.format(field_name))
        return body.get(field_name)
    
    def get_body_field(self, body, field_name, default_value=None):
        return body.get(field_name, default_value)
