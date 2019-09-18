# Creating a VIM Driver application

## Project Setup

Create the following directory structure:

```
myfirst-vim-driver/
  myfirstvd/
    __init__.py
    service/
      __init__.py
      infrastructure.py
    app.py
  config.yml
  run.py
```

Create a `run.py` file for you application with the following contents:

```
from myfirstvd.app import init_app

if __name__ == '__main__':
    init_app()
```

## Writing the Application

In the `infrastructure.py` file add the following contents:

```
import ignition.model.infrastructure as infrastructure_model
from ignition.service.framework import Service
from ignition.service.infrastructure import InfrastructureDriverCapability

class MyInfrastructureDriver(Service, InfrastructureDriverCapability):

    def create_infrastructure(self, template, inputs, deployment_location):
        print("Creating some Infrastructure")
        infrastructure_id = '1'
        request_id = '1'
        return infrastructure_model.CreateInfrastructureResponse(infrastructure_id, request_id)

    def get_infrastructure_task(self, infrastructure_id, request_id, deployment_location):
        print("Querying some Infrastructure")
        return infrastructure_model.InfrastructureTask(infrastructure_id, request_id, infrastructure_model.STATUS_IN_PROGRESS)

    def delete_infrastructure(self, infrastructure_id, deployment_location):
        print("Deleting some Infrastructure")
        request_id = '2'
        return infrastructure_model.DeleteInfrastructureResponse(infrastructure_id, request_id)

    def find_infrastructure(self, template, instance_name, deployment_location):
        print("Finding some Infrastructure")
        return infrastructure_model.FindInfrastructureResponse()
```

In the `app.py` file add the following contents:

```
import ignition.boot.api as ignition
from myfirstvd.service.infrastructure import MyInfrastructureDriver

def init_app():
    app_builder = ignition.build_vim_driver('MyFirstVimDriver')
    app_builder.include_file_config_properties('./config.yml', required=True)
    app_builder.add_service(MyInfrastructureDriver)
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

The above code uses `build_vim_driver` method from the `boot.api` Ignition module to create the basic `BootstrapApplicationConfiguration` required for a VIM driver. This configuration is set to load properties from the `config.yml` file located in the same directory as `run.py`.

Set the `application.port` value to the port your application should run on and set the `messaging.connection_address` to a valid Kafka instance.

The `add_service` method is used to set the driver for the Infrastructure API to an instance of a class you have created with the necessary methods to fulfill the Infrastructure Driver capability (see [Infrastructure Driver](#infrastructure-driver).

Finally `app_builder.run()` will configure and start your `BootstrapApplication`.

That's it! Now run your app and view the Swagger UI at `http://localhost:7777/api/infrastructure/ui` (remember to update the port if you changed it)

```
python3 run.py
```

You will see the Infrastructure APIs available to try-out, any requests you make to them will ultimately call the `MyInfrastructureDriver` instance to "do-the-work".

# Infrastructure Driver

The `InfrastructureDriverCapability` from the `ignition.service.infrastructure` module describes the methods needed on an Infrastructure Driver. You should create a service class that extends this capability (make it a service class by also extending `ignition.service.framework.Service`).

The create_infrastructure and delete_infrastructure methods are expected to return a response with a `request_id`. This id is used by bootstrapped Ignition services to asynchronously check it's status before notifying the Resource Manager via Kafka.
