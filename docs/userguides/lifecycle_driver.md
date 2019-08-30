# Creating a VNFC Driver application

## Project Setup 

Create the following directory structure:

```
myfirst-vnfc-driver/
  myfirstvnfcd/
    __init__.py
    service/
      __init__.py
      lifecycle.py
    app.py
  config.yml
  run.py
```

Create a `run.py` file for you application with the following contents:

```
from myfirstvnfcd.app import init_app

if __name__ == '__main__':
    init_app()
```

## Writing the Application

In the `lifecycle.py` file add the following contents: 

```
import ignition.model.lifecycle as lifecycle_model
from ignition.service.framework import Service
from ignition.service.lifecycle import LifecycleDriverCapability

class MyLifecycleDriver(Service, LifecycleDriverCapability):

    def execute_lifecycle(self, lifecycle_name, lifecycle_scripts_tree, system_properties, properties, deployment_location):
        print("Executing some Lifecycle")
        request_id = '1'
        return lifecycle_model.LifecycleExecuteResponse(request_id)

    def get_lifecycle_execution(self, request_id, deployment_location):
        print("Querying some Lifecycle Execution")
        request_id = '1'
        return lifecycle_model.LifecycleExecution(request_id, lifecycle_model.STATUS_IN_PROGRESS)
```

In the `app.py` file add the following contents: 

```
import ignition.boot.api as ignition
from myfirstvnfcd.service.infrastructure import MyLifecycleDriver

if __name__ == '__main__':
    app_builder = ignition.build_vnfc_driver('MyFirstVnfcDriver')
    app_builder.include_file_config_properties('./config.yml', required=True)
    app_builder.add_service(MyLifecycleDriver)
    app_builder.run()
```

In the `config.yml` file add the following contents:

```
---
application:
  port: 7777

messaging:
  connection_address: kafka:9092

```

The above code uses `build_vnfc_driver` method from the `boot.api` Ignition module to create the basic `BootstrapApplicationConfiguration` required for a VNFC driver. This configuration is set to load properties from the `config.yml` file located in the same directory as `run.py`.

Set the `application.port` value to the port your application should run on and set the `messaging.connection_address` to a valid Kafka instance.

The `add_service` method is used to set the driver for the Lifecycle API to an instance of a class you have created with the necessary methods to fulfill the Lifecycle Driver capability (see [Lifecycle Driver](#lifecycle-driver).

The `run` method will configure and start your `BootstrapApplication`.

That's it! Now run your app and view the Swagger UI at `http://localhost:7777/api/lifecycle/ui` (remember to update the port if you changed it in the python code)

```
python3 run.py
```

You will see the Lifecycle APIs available to try-out, any requests you make to them will ultimately call the `MyLifecycleDriver` instance to "do-the-work".

# Lifecycle Driver

The `LifecycleDriverCapability` in the `ignition.service.lifecycle` module describes the methods needed on a Lifecycle Driver. You should create a service class that extends this capability (make it a service class by also extending `ignition.service.framework.Service`).

The execute_lifecycle method is expected to return a response with a `request_id`. This id is used by bootstrapped Ignition services to asynchronously check it's status before notifying the Resource Manager via Kafka.
