# Error Handling

This section assumes you have already created your first driver and started working on your implementation of the `ResourceDriverHandlerCapability`. It's at this stage you might wonder how to customise the errors thrown by the bootstrapped API services. 

This guide will show you to easily customise the HTTP status code and localizedMessage included in the response by creating a Python exception to be raised in an implementation of a driver capability (or your own Service).

It will also show more advanced configuration to customise the full response body of an error. 

It's important to note that you should make sure any custom Exceptions you throw as part of API request handling adhere to the expectations of the APIs (see [Resource driver components](./framework/bootstrap-components/resourcedriver.md).

## Easy Customisation

### Create an Exception

In your Python code, import the `ApiException` and create a subclass from it. 

```
from ignition.api.exceptions import ApiException

class MissingFileError(ApiException):
    pass
```

Set a single class level attribute on this Exception to configure the HTTP status code that should be returned when raised:

```
class MissingFileError(ApiException):
    status_code = 400
```

### Raise the Exception

In your driver implementation, raise the Exception when you want this error to be returned to the API client:

```
class ValidationResult:
    def __init__(self, is_valid, reason):
        self.is_valid = is_valid
        self.reason = reason

class ResourceDriverHandler(Service, ResourceDriverHandlerCapability):

    def execute_lifecycle(self, lifecycle_name, driver_files, system_properties, resource_properties, request_properties, internal_resources, deployment_location):
        if not driver_files.has_file('expected_template.yaml'):
            raise MissingFileError('Missing an expected file')
        ...
```

In this example, if we call the Execute Lifecycle API we will receive an error response with a 400 HTTP status code. Update the `status_code` of the `TemplateInvalidError` to another code and try again to see response change. You will also notice the `localizedMessage` in the response body includes the message passed into the Exception (e.g. 'Missing an expected file')

## Advanced Customisation

### Register Exception Handler

When configuring the Ignition app builder, you may register error handlers to configure the response of specific Exception by class type.

```
class MyException(Exception):
    
    def __init__(self, message, server_name, context_info):
        super().__init__(message)
        self.server_name = server_name
        self.context_info = context_info

def handle_my_exception(exception):
    return {
        'localizedMessage': 'I am customing this message with some custom info: {0}'.format(exception.context_info),
        'server_name': exception.server_name,
        'status': 400
    }

def create_app():
    app_builder = ignition.build_resource_driver('My Driver')
    app_builder.api_error_converter.register_handler(MyException, handle_my_exception)
    ...
```

The `register_handler` function takes 2 parameters: the type of Exception to handle and a handler function. The handler function can be any callable Python function which accepts the instance of the Exception as a parameter.

The handler function should return a `dict` with keys to override or add to the response body. In the above example we have overriden the `localizedMessage` added to the response, then added a `server_name` value. 

### Raise the Exception

In your driver code, raise the Exception when you want this error to be returned to the API client:

```
from datetime import datetime 

class ResourceDriverHandler(Service, ResourceDriverHandlerCapability):

    def execute_lifecycle(self, lifecycle_name, driver_files, system_properties, resource_properties, request_properties, internal_resources, deployment_location):
        if not driver_files.has_file('expected_template.yaml'):x
            raise MyException('This is not valid', 'serverA', 'time is {0}'.format(datetime.now().strftime('%d/%m/%Y %H:%M:%S')))
        ...
```

In this example, if we call the Execute Lifecycle API we will receive an error response with a 400 HTTP status code and a body which includes:

```
{
    "localizedMessage": "I am customing this message with some custom info: time is 22/11/2019 16:13:25",
    "server_name": "serverA",
    "status": "400"
}
```