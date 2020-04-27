# Request Queue

A Request Queue is a core Ignition feature that can be used by drivers to provide a request queue for handling API requests. In Ignition, a request queue is implemented using a message bus (a partitioned Kafka topic), rather than in-memory, to maintain high availability. API requests are queued on the message bus, and each instance of the driver will take requests from the queue, then either complete them or requeue them by posting them back to the bus.

If `resource_driver.lifecycle_request_queue.enabled` is `True`, driver "execute_lifecycle" API calls are intercepted and placed on the request queue. The `KafkaLifecycleRequestQueueService` provides an API for reading from this topic one request at a time and committing the request (that is, committing the Kafka topic offset relating to the request) when the request processing is complete.

By default, request queues are disabled but can be enabled with:

```
resource_driver:
  lifecycle_request_queue:
    enabled: True
```

## Services

The following request queue services are auto-configured when enabled:

| Name                     | Capability         | Required Capabilities             | Bootstrap Enable/Disable flag       | Topic Name   | Failed Request Topic Name |Description                                                                                                                                     |
| ------------------------ | ------------------ | --------------------------------- | ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| KafkaLifecycleRequestQueueService | LifecycleRequestQueueCapability | LifecycleMessagingCapability, MessagingProperties, ResourceDriverProperties, PostalCapability, DriverFilesManagerCapability, LifecycleConsumerFactoryCapability | lifecycle.request_queue.enabled | `[Driver Name]_lifecycle_request_queue` | `[Driver Name]_lifecycle_request_failed_queue` | Handles placing Execute Lifecycle API requests on the queue and handles reading requests from the queue |

## Configuration Properties

The request queues can be configured in the normal way (through a configuration file or through a Helm values file) as follows:

```
resource_driver:
  lifecycle_request_queue:
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

The `group_id` should be the same for all replicas of a driver installation, though this can be changed to another string if desired. 

`auto_create` should be left as `True` so that Ignition will create the topics during bootstrap if they don't already exist. 

`replication_factor` should be set to less than or equal to the number of Kafka brokers in your Kafka cluster. 

`topic.num_partitions` defines the concurrency of request handling (`failed_topic.partitions` can be kept to 1 partition, unless there are specific requirements to set it to a higher value). 

`retention.ms`, `message.timestamp.difference.max.ms` and `file.delete.delay.ms` define how long request messages are kept (defaulting to an hour, set this higher if you need to keep processed requests for longer).

### Adding Requests to the Queue

Requests are added to the request queue automatically by Ignition if the request queue is enabled (i.e. `resource_driver.lifecycle_request_queue.enabled` is True.

### Handling Requests from a Request Queue

When the request queue is enabled, the driver implementation of handling requests looks different.

The Lifecycle Driver API implementation for `execute_lifecycle` is now a noop (Ignition handles putting API requests on the Lifecycle Request Queue before they get to the driver).

```
from ignition.service.framework import Service
from ignition.service.resourcedriver import ResourceDriverCapability

class TestLifecycleDriver(Service, ResourceDriverCapability):
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

Note that the handler should catch all exceptions and handle accordingly if they want custom handling of exceptions. Any exceptions not handled by the handler will be caught by the request queue service and an appropriate asynchronous response constructed, much like in the example code. Any requests that cannot be parsed by the request queue service will result in the complete request being added to the failed request queue topic for the request queue type and driver (see the `Failed Request Topic Name` column in the table above). In all cases (failure and success), the Ignition request queue service is responsible for handling topic commits relating to request processing.

