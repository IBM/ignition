# Add Custom APIs

Ignition bootstraps APIs and common services required by Resource drivers. However, it is reasonable to expect that each driver would configure additional APIs or Services in their application, for debugging or monitoring purposes. 

The simplest way to add a custom API is with the `add_api` method of an Ignition `ApplicationBuilder`. With this method you only need to provide a path to a valid OpenAPI specification for your API and the `Capability` expected to handle requests.

## Example

As an example, we are going to add a `helloworld` API to a driver. This assumes you have already followed the [creating a driver](./creating-a-driver.md) user guide. 

Start by creating a new `api_specs` sub-package under the main package of your application (i.e. `mydriver`). In this sub-package, add an empty `__init__.py` file and create a `helloworld.yaml` file with the following OpenAPI specification:

```
openapi: 3.0.0
info:
  description: Hello World API
  version: "1.0.0-oas3"
  title: Hello World
servers:
  - url: /api/helloworld
tags:
  - name: helloworld
    description: Hello World API
paths:
  /:
    get:
      tags:
        - helloworld
      summary: Say hello
      description: >-
        Returns hello world
      operationId: .get
      responses:
        "200":
          description: Request accepted
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Response"
        "400":
          description: Bad request
components:
  schemas:
    Response:
      type: object
      properties:
        msg:
          type: string

```

Now we must create a Service to handle requests made on this API. Do this by creating a `helloworld.py` file under the `service` package and add the following:

```
from ignition.service.framework import Service, Capability, interface

class HelloWorldApiCapability(Capability):

    @interface
    def get(self, **kwarg):
        pass

class HelloWorldApiService(Service, HelloWorldApiCapability):

    def get(self, **kwarg):
        return ({'msg': 'Hello, World!'}, 200)
```

To register the API and the Service handling it's requests, open the `app.py` file and add the highlighted lines (with `#ADD`):

```
import logging
import ignition.boot.api as ignition
import pathlib
import os
import mydriver.config as driverconfig
from mydriver.service.resourcedriver import ResourceDriver
## ADD
import mydriver.api_specs as api_specs
from mydriver.service.helloworld import HelloWorldApiService, HelloWorldApiCapability 
## -----

default_config_dir_path = str(pathlib.Path(driverconfig.__file__).parent.resolve())
default_config_path = os.path.join(default_config_dir_path, 'default_config.yml')

## ADD
# Grabs the __init__.py from an api_specs package in your application then takes it's parent, the api_specs directory itself
api_spec_path = str(pathlib.Path(api_specs.__file__).parent.resolve())
## -----

def create_app():
    app_builder = ignition.build_resource_driver('My Driver')
    app_builder.include_file_config_properties(default_config_path, required=True)
    app_builder.include_file_config_properties('./mydriver_config.yml', required=False)
    # custom config file e.g. for K8s populated from Helm chart values
    app_builder.include_file_config_properties('/var/mydriver/mydriver_config.yml', required=False)
    app_builder.include_environment_config_properties('MYDRIVER_CONFIG', required=False)
    app_builder.add_service(ResourceDriver)
    ## ADD
    app_builder.add_api(os.path.join(api_spec_path, 'helloworld.yaml'), HelloWorldApiCapability) 
    app_builder.add_service(HelloWorldApiService)
    ## -----
    return app_builder.configure()


def init_app():
    app = create_app()
    return app.run()
```

Once the above changes have been made, run your application and navigate to `http://<host>:<port>/api/helloworld/ui` to use your new API.