# Add Custom APIs

Ignition exists to bootstrap APIs and common services required by VIM/VNFC drivers. However, it is reasonable to expect that each driver would like to configure additional APIs or Services in their application.

The simplest way to add a custom API is with the `add_api` of an Ignition `ApplicationBuilder`. With this method you only need to provide a path to a valid OpenAPI specification for your API and the `Capability` expected to handle requests.

## Example

As an example, we are going to add a `helloworld` API to a VIM Driver. This assumes you have already followed the [Creating a VIM Driver application user guide](./vim_driver.md), so now have a project structure similar to:

```
example-vim-driver/
  examplevd/
    __init__.py
    service/
      __init__.py
      infrastructure.py
    app.py
  config.yml
  run.py
```

Start by creating a new `api_specs` sub-package under the main package of your application (i.e. `examplevd`). In this sub-package, add an empty `__init__.py` file and create a `helloworld.yaml` with the following OpenAPI specification:

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

Now we need to create a Service to handle requests made on this API. Do this by creating a `helloworld.py` file under the `service` package and add the following:

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
import ignition.boot.api as ignition
import examplevd.api_specs as api_specs #ADD
import pathlib #ADD
import os #ADD
from examplevd.service.infrastructure import MyInfrastructureDriver
from examplevd.service.helloworld import HelloWorldApiService, HelloWorldApiCapability #ADD

# Grabs the __init__.py from an api_specs package in your application then takes it's parent, the api_specs directory itself
api_spec_path = str(pathlib.Path(api_specs.__file__).parent.resolve()) #ADD

def init_app():
    app_builder = ignition.build_vim_driver('MyFirstVimDriver')
    app_builder.include_file_config_properties('./config.yml', required=True)
    app_builder.add_service(MyInfrastructureDriver)

    app_builder.add_api(os.path.join(api_spec_path, 'helloworld.yaml'), HelloWorldApiCapability) #ADD
    app_builder.add_service(HelloWorldApiService) #ADD

    app_builder.run()
```

Once the above changes have been made, run your application and navigate to `http://localhost:7777/api/helloworld/ui` to use your new API.
