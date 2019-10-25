# Ignition Services 

Ignition is built on 'Services' that each fulfill a 'Capability'.

## Capability

A Capability defines a set of methods that are required to fulfill a particular role in the system (i.e. an Interface).

For example, there might be a MessagingCapability that expects a single `send_message(the_message)` function. This would be defined by the following:

```
from ignition.service.framework import Capability, interface

class MessagingCapability(Capability):

    @interface
    def send_message(the_message):
      pass
```

## Service

A Service is simply a class. The intention is that a Service will claim to offer one or more capabilities by extending the class for each.

For example, there might be a KafkaMessagingService that fulfills the role of the MessagingCapability. This would be defined as:

```
from ignition.service.framework import Service

class KafkaMessagingService(Service, MessagingCapability):

    def send_message(the_message):
      send_to_kafka(the_message)
```

When a Service extends a Capability it must implement all methods marked with `@interface` otherwise an error will be thrown at runtime.

## Service Registration

Services are registered to the Ignition application when defining the configuration. Once an instance of the `BootstrapConfiguration` class is obtained, Services may be registered by adding to the `service_configurators`.

```
from ignition.boot.config import BootstrapConfiguration
from ignition.service.framework import ServiceRegistration

class MyConfigurator:

  def configure(self, configuration, service_register):
    # configuration is an instance of ignition.boot.config.BootstrapConfiguration
    # service_register is an instance of ignition.service.framework.ServiceRegister
    registration = ServiceRegistration(KafkaMessagingService)
    service_register.add_service(registration)

config = BootstrapConfiguration()
my_configurator = MyConfigurator()
config.service_configurators.append(my_configurator)
```

When Ignition is run it will construct an instance of each registered Service to be used by the system.

## API Registration

APIs are registered to the Ignition application when defining the configuration. Once an instance of the `BootstrapConfiguration` class is obtained, APIs may be registered by adding to the `api_configurators`.

```
from ignition.boot.config import BootstrapConfiguration
from ignition.service.framework import ServiceRegistration
from ignition.boot.connexionutils import build_resolver_to_instance

class MyConfigurator:

  def configure(self, configuration, service_register, service_instances, api_register):
    # configuration is an instance of ignition.boot.config.BootstrapConfiguration
    # service_register is an instance of ignition.service.framework.ServiceRegister
    # service_instances is an instance of ignition.service.framework.ServiceInstances
    # api_register is an instance of ignition.boot.app.ApiRegister
    api_spec = './my_spec.yaml' # full path to an openapi specification for your API
    api_service_instance = self.__get_service_for_api(service_register, service_instances)
    api_register.register_api(api_spec, resolver=build_resolver_to_instance(api_service_instance))

  def __get_service_for_api(self, service_register, service_instances):
    api_service_class = service_register.get_service_offering_capability(MyApiCapability)
    if api_service_class is None:
        raise ValueError('No service has been registered with the MyApiCapability')
    api_service_instance = service_instances.get_instance(api_service_class)
    if api_service_instance is None:
        raise ValueError('No instance of the MyApiCapability service has been built')

config = BootstrapConfiguration()
my_configurator = MyConfigurator()
config.api_configurators.append(my_configurator)
```

When Ignition is run it will include your `api_spec` on the running Connexion application. The object handling the API requests depends on how you have configured the `operationId` in your spec and the `resolver` in the `register_api` call.

In the above example, we use `resolver=build_resolver_to_instance(api_service_instance)` to resolve all `operationIds` to the instance of a previously configured Service.

### Rules of Registration

The following rules must be adhered to when registering a Service.

**A Service must extends from the Service class**

All registered Services must extend ignition.service.framework.Service

**Only one Service can offer a Capability**

When a Service is registered it is bound to all the capabilities it offers (Capability classes it extends). Any future Service that is registered CANNOT offer the same capability as one previously registered.

**Services can have arguments**

A Service being registered can have arguments, they must be defined as arguments on the registration, after the class:

```
class MyService(Service, MyCapability):

    def __init__(self, name, connection_address):
        self.name = name
        self.connection_address = connection_address

# 'Service1' will be passed to name and 'localhost:8080' will be passed to connection_address
registration = ServiceRegistration(MyService, 'Service1', 'localhost:8080')
```

Note: the above usage is recommended for any non-service based arguments. If you need one Service to be specified as an argument to another then see the Service Dependencies section of this document.

## Service Dependencies

In order for a Service to work, it may need to be injected with other registered Services that offer particular capabilities. For example, a Monitoring Service may need access to a service that can provide Messaging, to send messages out when it notices something has changed.

When a Service is registered, the capabilities it requires can be specified:

```
registration = ServiceRegistration(MonitoringService, messaging=MessagingCapability)
```

When an instance of this Service is created it will be provided with the instance of the Service that fulfills the required capabilities:

```
class MonitoringService(Service, MonitoringCapability):

    def __init__(self, **kwargs):
      messaging_service = kwargs.get('messaging')
```

A Service may require multiple capabilities, each will be provided as a keyword argument matching the name of the requirement at registration.

```
registration = ServiceRegistration(MonitoringService, messaging=MessagingCapability, health=HealthCapability)

class MonitoringService(Service, MonitoringCapability):

    def __init__(self, **kwargs):
      # Note how the services are available on the key 'messaging' and 'health' as this is how they were defined in the registration
      messaging_service = kwargs.get('messaging')
      health_service = kwargs.get('health')
```

### Rules of Dependencies

The following rules must be adhered to when registering Services with dependencies.

**Services cannot have cyclic dependencies**

Cyclic dependencies between Services are detected at initialisation time, not registration. An example of a cyclic dependency would be:

- ServiceA offers CapabilityA
- ServiceB offers CapabilityB
- ServiceA relies on CapabilityB
- ServiceB relies on CapabilityA

In this example, we cannot construct ServiceA before we construct ServiceB, however we also cannot construct ServiceB before we construct ServiceA.

## Service Initialisation

Services are initialised during the creation of a `BootstrapApplication`.

The `BootstrapRunner` class of the `boot.app` module (the `run` method of this module handles the BootstrapRunner for you) will call the `service_registration_pre_func` method, if one has been configured. It will then register any auto-configured Services based on the bootstrap configuration, before calling the `service_registration_post_func`, if configured.

Once all Services have been registered, the runner will order them based on dependencies, then initialise an instance of each one-by-one.
