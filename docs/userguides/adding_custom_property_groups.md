# Add Custom Property Groups

An application built with Ignition can be configured to load configuration properties from `yml` files. **Property groups** are registered to the application, with a **key namespace** to identify the properties they should bind to in the file.

As an example, take the following configuration file:

```
app:
  database:
    host: localhost
    port: 8080
```

A property group to read these properties may be defined as:

```
from ignition.service.config import ConfigurationPropertiesGroup, ConfigurationProperties

class AppProperties(ConfigurationPropertiesGroup):

    def __init__(self):
        super().__init__('app')
        self.database = DatabaseProperties()

class DatabaseProperties(ConfigurationProperties):

    def __init__(self):
        self.host = None
        self.port = None
```

When registered to the application, the registered instance of the `AppProperties` will be populated with the values from the configuration file, so `self.database.host` would be set to `localhost`.

## Example

As a more complete example, we are going to add some custom property groups to the `helloworld` API added as part of [Add Custom APIs](./adding_custom_apis.md).

Start by adding the following to the `helloworld.py` file:

```
from ignition.service.config import ConfigurationPropertiesGroup
from ignition.service.framework import Service, Capability, interface

class HelloWorldProperties(ConfigurationPropertiesGroup, Service, Capability):

    def __init__(self):
        super().__init__('helloworld')
        self.name = 'World'
```

By making `HelloWorldProperties` a `Capability` and `Service`, it will be available as a dependency to our `HelloWorldApiService`. Update the constructor of `HelloWorldApiService` to accept the properties and base the response on the configured values:

```
class HelloWorldApiService(Service, HelloWorldApiCapability):

    def __init__(self, **kwargs):
        self.helloworld_properties = kwargs.get('helloworld_properties')

    def get(self, **kwarg):
        return ({'msg': 'Hello, {0}!'.format(self.helloworld_properties.name)}, 200)
```

Open `app.py` and configure the property group. We will also need to update the registration of `HelloWorldApiService` to specify the dependency on the `HelloWorldProperties`:

```
import ignition.boot.api as ignition
import examplevd.api_specs as api_specs
import pathlib
from examplevd.service.infrastructure import MyInfrastructureDriver
from examplevd.service.helloworld import HelloWorldApiService, HelloWorldApiCapability, HelloWorldProperties #ADD

# Grabs the __init__.py from an api_specs package in your application then takes it's parent, the api_specs directory itself
api_spec_path = str(pathlib.Path(api_specs.__file__).parent.resolve())

def init_app():
    app_builder = ignition.build_vim_driver('MyFirstVimDriver')
    app_builder.include_file_config_properties('./config.yml', required=True)
    app_builder.add_service(MyInfrastructureDriver)

    app_builder.add_api(os.path.join(api_spec_path, 'helloworld.yaml'), HelloWorldApiCapability)
    app_builder.add_property_group(HelloWorldProperties()) #ADD
    app_builder.add_service(HelloWorldApiService, helloworld_properties=HelloWorldProperties) #ADD

    app_builder.run()
```

Finally add the following properties to `config.yml`:

```
helloworld:
  name: Mr Joe Bloggs
```

Now run the application, try the `helloworld` API and note how it responds with `Hello, Mr Joe Bloggs!`. Update the `name` property to a different value, restart the application and note how the response changes.
