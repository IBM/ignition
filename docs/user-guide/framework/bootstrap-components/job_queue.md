# Job Queue

A Job Queue is a core feature required by many of the Services expected in a driver. As a result, all of the Services listed below are enabled by default when using the `ignition.boot.api.build_resource_driver` function. 

In Ignition a job queue is implemented using a message bus, rather than in-memory, to maintain high availability. Jobs are queued on the message bus, each instance of the driver will take jobs from the queue, then either complete them or requeue them by posting them back to the bus.

## Services

The following service is auto-configured when enabled:

| Name                     | Capability         | Required Capabilities             | Bootstrap Enable/Disable flag       | Description                                                                                                                                     |
| ------------------------ | ------------------ | --------------------------------- | ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| MessagingJobQueueService | JobQueueCapability | PostalCapability, InboxCapability | bootstrap.job_queue.service_enabled | Handles receiving jobs, passing them off to registered handlers, before requeing them if the handling indicates the job cannot be completed yet |

For an example of how the MessagingJobQueueService might be used see the LifecycleExecutionMonitoringService.

## Configuration Properties

The MessagingJobQueueService includes a `JobQueueProperties` property group, so the following properties may be configured in the configuration YAML file of a driver:

| Property | Description | Default |
| --- | --- | --- |
| job_queue.consumer_group_id | The Consumer Group ID to use when consuming the queue from the Messaging Service (this ensures on restart that the driver may continue reading the queue from the last message it saw before it stopped) | job_queue_consumer | 

In addition the MessagingJobQueueService also depends on the `topics.job_queue` property of the `MessagingProperties` group. This means the following configuration properties impact the job queue service:

| Property | Description | Default |
| --- | --- | --- |
| messaging.topics.job_queue.name | Name of the topic used as a Job Queue | The driver's app name with special characters removed and spaces replaced with underscores (e.g. ignition.build_resource_driver('Openstack VIM Driver') generates a topic name of 'Openstack_VIM_Driver') | 
| messaging.topics.job_queue.auto_create | Enable/disable auto-creation of the Job Queue topic. If disable then you must create it prior to starting the driver | True |
| messaging.topics.job_queue.config | Map of configuration to be passed to the Topic when creating it | See below |

Default job_queue.config:

```
retention.ms: 60000
message.timestamp.difference.max.ms: 60000
file.delete.delay.ms: 60000
```

### Adding Jobs to the Queue

Jobs are added to the queue using the `queue_job` method. The job will then be serialized and put on the message bus. Each job added to the queue must specify a `job_type` value.

```
my_job = {
    'job_type': 'DemoJob',
    # Any other fields can be included on the job
    'id': '123',
    'task': 'check'
}

queue_service.queue_job(my_job)
```

### Handling Jobs

To make the Job Queue Service re-usable, it has no knowledge of how to handle messages, only how to receive them. The handling of each message is covered by a job handler registered to the service. Each job handler is bound to a particular type (a required field of any job), so the queue service knows which handler to use when a new job is received.

```
# Registering a handle for any job with type 'DemoJob'

def my_handler(job):
    # Do something with the job
    job_complete = do_something(job)
    return job_complete

queue_service.register_job_handler('DemoJob', my_handler)
```

When asked to handle a job, the job handler must return `True` if the job has been complete or `False` if the job should be put back on the queue. Any errors returned by the handler will result in the job being removed from the queue, so they should only be raised in exceptional circumstances. If relying on errors from 3rd party systems to indicate a job is not finished, you should catch this error with the `except` keyword, log the error (if useful) and return `False` instead. 