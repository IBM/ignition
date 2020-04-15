# Request Queue

A Request Queue is a core Ignition feature that can be used by both VIM and Lifecycle drivers to provide a request queue for handling API requests. There are two request queues, one each for infrastructure API requests and lifecycle API requests. In Ignition, a request queue is implemented using a message bus (a partitioned Kafka topic), rather than in-memory, to maintain high availability. API requests are queued on the message bus, and each instance of the VIM/Lifecycle driver will take jobs from the queue, then either complete them or requeue them by posting them back to the bus.

If `infrastructue.request_queue.enabled` is `True`, VIM/infrastructure driver "create_infrastructure" API calls are intercepted and placed on the infrastructure request queue. The `KafkaInfrastructureRequestQueueService` provides an API for reading from this topic one request at a time and committing the request (that is, committing the Kafka topic offset relating to the request) when the request processing is complete.

If `lifecycle.request_queue.enabled` is `True`, lifecycle driver "execute_lifecycle" API calls are intercepted and placed on the lifecycle request queue. The `KafkaLifecycleRequestQueueService` provides an API for reading from this topic one request at a time and committing the request (that is, committing the Kafka topic offset relating to the request) when the request processing is complete.

By default, both infrastructure and lifecycle request queues are disabled. They can be enabled individually as follows:

```
infrastructure:
  request_queue:
    enabled: True

lifecycle:
  request_queue:
    enabled: True
```

In Ignition a request queue is implemented using a message bus, rather than in-memory, to maintain high availability. API requests are queued on the message bus, and each instance of the VIM/Lifecycle driver will take jobs from the queue, then either complete them or requeue them by posting them back to the bus.

## Services

The following request queue services are auto-configured when enabled:

| Name                     | Capability         | Required Capabilities             | Bootstrap Enable/Disable flag       | Topic Name   | Failed Request Topic Name |Description                                                                                                                                     |
| ------------------------ | ------------------ | --------------------------------- | ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| KafkaInfrastructureRequestQueueService | InfrastructureRequestQueueCapability | InfrastructureMessagingCapability, MessagingProperties, InfrastructureProperties, PostalCapability, InfrastructureConsumerFactoryCapability | infrastructure.request_queue.enabled | `[Driver Name]_infrastructure_request_queue` | `[Driver Name]_infrastructure_request_failed_queue` | Handles placing infrastructure API requests on the queue and handles reading requests from the queue |
| KafkaLifecycleRequestQueueService | LifecycleRequestQueueCapability | LifecycleMessagingCapability, MessagingProperties, LifecycleProperties, PostalCapability, LifecycleScriptFileManagerCapability, LifecycleConsumerFactoryCapability | lifecycle.request_queue.enabled | `[Driver Name]_infrastructure_request_queue` | `[Driver Name]_infrastructure_request_failed_queue` | Handles placing lifecycle API requests on the queue and handles reading requests from the queue |

## Configuration Properties

The request queues can be configured in the normal way (through a configuration file or through a Helm values file) as follows:

```
lifecycle|infrastructure:
  request_queue:
    enabled: True
    group_id: ald_request_queue
    topic:
      auto_create: True
      num_partitions: 20
      replication_factor: 1
      config:
        # 1 hour
        retention.ms: 3600000
        message.timestamp.difference.max.ms: 3600000
        file.delete.delay.ms: 3600000
    failed_topic:
      auto_create: True
      num_partitions: 1
      replication_factor: 1
```

The `group_id` should be the same for all replicas of a driver installation, though this can be changed to another string if desired. `auto_create` should be left as `True` so that Ignition will create the topics during bootstrap if they don't already exist. `replication_factor` should be set to less than or equal to the number of Kafka brokers in your Kafka cluster. `topic.num_partitions` defines the concurrency of request handling (`failed_topic.partitions` can be kept to 1 partition, unless there are specific requirements to set it to a higher value). `retention.ms`, `message.timestamp.difference.max.ms` and `file.delete.delay.ms` define how long request messages are kept (defaulting to an hour, set this higher if you need to keep processed requests for longer).

### Adding Requests to the Queue

Requests are added to the request queue automatically by Ignition if the request queue is enabled (i.e. `infrastructure.request_queue.enabled` is True for infrastructure API calls, `lifecycle.request_queue.enabled` is True for lifecycle API calls).

### Handling Requests from a Request Queue

When handling requests when the request queue is enabled, the driver implementation looks different.

The Infrastructure/VIM Driver API implementation for `create_infrastructure` is now a noop (Ignition handles putting API requests on the Infrastructure Request Queue before they get to the driver).

```
from ignition.service.framework import Service
from ignition.service.infrastructure import InfrastructureDriverCapability

class TestInfrastructureDriver(Service, InfrastructureDriverCapability):
    ...

    def create_infrastructure(self, template, template_type, system_properties, properties, deployment_location):
        pass
```

The Lifecycle Driver API implementation for `execute_lifecycle` is now a noop (Ignition handles putting API requests on the Lifecycle Request Queue before they get to the driver).


```
from ignition.service.framework import Service
from ignition.service.lifecycle import LifecycleDriverCapability

class TestLifecycleDriver(Service, LifecycleDriverCapability):
    ...

    def execute_lifecycle(self, lifecycle_name, lifecycle_scripts_tree, system_properties, properties, deployment_location):
        pass
```

To make the Request Queue Services re-usable, they have no knowledge of how to handle requests, only how to receive them. The handling of each request is covered by a request handler that must be implemented by the driver, as follows:

```
# Lifecycle request queue handler
# request_queue_service is an instance of KafkaLifecycleRequestQueueService
request_queue = request_queue_service.get_lifecycle_request_queue('Name', TestLifecycleRequestHandler(self.messaging_service))
```

Here is the skeleton implementation of the Lifecycle request queue handler:

```
from ignition.model.lifecycle import LifecycleExecution
from ignition.model.failure import FailureDetails, FAILURE_CODE_INTERNAL_ERROR
from ignition.service.requestqueue import RequestHandler

class TestLifecycleRequestHandler(RequestHandler):
    def __init__(self, messaging_service):
      super(TestLifecycleRequestHandler, self).__init__()
      self.messaging_service = messaging_service

    def handle_request(self, request):
      try:
        if request is not None:
          # process request
          ...

          # send async response
          self.messaging_service.send_lifecycle_execution(result)
        else:
          logger.warn('Null request from request queue')
      except Exception as e:
        # handle exception e.g.
        self.messaging_service.send_lifecycle_execution(LifecycleExecution(request['request_id'], STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, "Unexpected exception: {0}".format(e)), {}))
```

Infrastructure request queue handlers are created and used in a similar way:

```
# Infrastructure request queue handler
# request_queue_service is an instance of KafkaInfrastructureRequestQueueService
request_queue = request_queue_service.get_infrastructure_request_queue('Name', TestRequestHandler(self.messaging_service))
```

Here is the skeleton implementation of the Infrastructure request queue handler:

```
from ignition.model.infrastructure import InfrastructureTask
from ignition.model.failure import FailureDetails, FAILURE_CODE_INTERNAL_ERROR
from ignition.service.requestqueue import RequestHandler

class TestInfrastructureRequestHandler(RequestHandler):
    def __init__(self, messaging_service):
      super(TestInfrastructureRequestHandler, self).__init__()
      self.messaging_service = messaging_service

    def handle_request(self, request):
      try:
        if request is not None:
          # process request
          ...

          # send async response
          self.messaging_service.send_infrastructure_task(result)
        else:
          logger.warn('Null request from request queue')
      except Exception as e:
        # handle exception e.g.
        self.messaging_service.send_infrastructure_task(InfrastructureTask(None, request['request_id'], FAILURE_CODE_INTERNAL_ERROR, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, "Unexpected exception: {0}".format(e)), {}))
```

Note that the handler should catch all exceptions and handle accordingly if they want custom handling of exceptions. Any exceptions not handled by the handler will be caught by the request queue service and an appropriate asynchronous response constructed, much like in the example code. Any requests that cannot be parsed by the request queue service will result in the complete request being added to the failed request queue topic for the request queue type and driver (see the `Failed Request Topic Name` column in the table above). In all cases (failure and success), the Ignition request queue service is responsible for handling topic commits relating to request processing.

