# Lifecycle

The Lifecycle API is a requirement of any Lifecycle Driver. All of the APIs and Services listed below are enabled by default when using the `ignition.boot.api.build_lifecycle_driver` method.

## APIs

Ignition can bootstrap the following API for Lifecycle:

| Name          | Required Capability    | Bootstrap Enable/Disable flag   | Description                                                                                                             |
| ------------- | ---------------------- | ------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Lifecycle API | LifecycleApiCapability | bootstrap.lifecycle.api_enabled | Adds the Lifecycle API to the Connexion app, registering the service offering the LifecycleApiCapability as the handler |

When enabled this API will be accessible at `/api/lifecycle` (view the Swagger for it at `/api/lifecycle/ui` of a running driver).

The specification for this API is built into the Ignition Python package so must be viewed through the Swagger UI or at the Ignition Github page (`ignition/openapi/vnfc_lifecycle.yaml`).

## Services

Ignition can bootstrap the following services for the Lifecycle API:

| Name                                | Capability                             | Required Capabilities                  | Bootstrap Enable/Disable flag                  | Description                                                                                                                                |
| ----------------------------------- | -------------------------------------- | -------------------------------------- | ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| LifecycleApiService                 | LifecycleApiCapability                 | LifecycleServiceCapability             | bootstrap.lifecycle.api_service_enabled        | Handles API requests, passing calls down to the Lifecycle Service                                                                          |
| LifecycleService                    | LifecycleServiceCapability             | LifecycleExecutionMonitoringCapability | bootstrap.lifecycle.service_enabled            | Service layer for handling Lifecycle execution requests, will ultimately call a driver (to do something with the target Lifecycle scripts) |
| LifecycleExecutionMonitoringService | LifecycleExecutionMonitoringCapability | LifecycleMessagingCapability           | bootstrap.lifecycle.monitoring_service_enabled | Service used by the Lifecycle Service to monitor the progress of execution requests, sending a message on Kafka when complete              |
| LifecycleMessagingService           | LifecycleMessagingCapability           | PostalCapability                       | bootstrap.lifecycle.messaging_service_enabled  | Service used by the Lifecycle Monitoring Service to send a message to Kafka for Lifecycle execution updates                                |

All Capability and Service implementations for Lifecycle can be found in the `service.lifecycle` module.

By bootstrapping the above services, all you need to provide is a Service that fulfills the LifecycleDriverCapability and you will have a functioning Lifecycle API.

## Configuration Properties

The LifecycleMessagingService depends on on the `topics.lifecycle_execution_events` property of the `MessagingProperties` group. This means the following configuration properties impact the messaging service:

| Property | Description | Default |
| --- | --- | --- |
| messaging.topics.lifecycle_execution_events.name | Name of the topic used to pass messages back to Brent | lm_vnfc_lifecycle_execution_events | 
| messaging.topics.lifecycle_execution_events.auto_create | Enable/disable auto-creation of the topic. This topic is usually created by an LM installation | False | 
| messaging.topics.lifecycle_execution_events.config | Map of configuration to be passed to the Topic when creating it | {} |

# Integration with your Lifecycle Driver

Let's look at the LifecycleDriverCapability:

```python
class LifecycleDriverCapability(Capability):

    @interface
    def execute_lifecycle(self, lifecycle_name, lifecycle_scripts_tree, system_properties, properties, deployment_location):
        """
        Execute a lifecycle transition/operation for a Resource.
        This method should return immediate response of the request being accepted,
        it is expected that the LifecycleService will poll get_lifecycle_execution on this driver to determine when the request has complete (or devise your own method).

        :param str lifecycle_name: name of the lifecycle transition/operation to execute
        :param ignition.utils.file.DirectoryTree lifecycle_scripts_tree: object for navigating the directory of the lifecycle scripts for the Resource
        :param dict system_properties: properties generated by LM for this Resource: instance_id, instance_name
        :param dict properties: property values of the Resource
        :param dict deployment_location: the deployment location the Resource is assigned to
        :return: an ignition.model.lifecycle.LifecycleExecuteResponse
        """
        pass

    @interface
    def get_lifecycle_execution(self, request_id, deployment_location):
        """
        Retreive the status of a lifecycle transition/operation request

        :param str request_id: identifier of the request to check
        :param dict deployment_location: the deployment location the Resource is assigned to
        :return: an ignition.model.lifecycle.LifecycleExecution
        """
        pass
```

There are several methods required on any Service implementing this Capability, in order to serve execute lifecycle requests. The following sections describe the flow of an incoming request, outlines the role of Ignition and how your driver implementation is used.

## On Execute

The LifecycleApiService handles the incoming HTTP request, parsing the headers and body before making a call to the LifecycleService with the expected arguments. 

The LifecycleService takes the base64 encoded version of the `lifecycle_scripts`, writes them to disk, then extracts the contents so they are available as pure directories and files. The Service then calls the `execute_lifecycle` method on the `LifecycleDriver` provided by the user, passing all of the original parameters but with the `lifecycle_scripts` base64 string replaced with a `ignition.utils.file.DirectoryTree` instance, which can be used to interact with the extracted contents of the scripts. 

The `LifecycleDriver` is expected to either:
- Complete the request by initiating execution of the target lifecycle, returning immediately with an instance of `ignition.model.lifecycle.LifecycleExecuteResponse` which includes a `request_id` which may be used at a later time to check the status of the execution.
- Raise an Exception if the request is invalid or cannot be accepted. This Exception will end the continuation of this flow and instead result in an error being returned to the client of the LifecycleApiService. 

On receipt of a LifecycleExecuteResponse, the `LifecycleService` will inform the LifecycleExecutionMonitoringService that it should monitor the completion of the execution, using the `request_id` from the response.

The LifecycleExecutionMonitoringService will periodically, using the JobQueueService (see [job queue](./job_queue)), check if execution has complete. It will do this by calling the `get_lifecycle_execution` method of the `LifecycleDriver`

Meanwhile, the LifecycleService will return the LifecycleExecuteResponse to the LifecycleApiService, so it may convert it to a HTTP response and return it to the original client.

In the background, LifecycleExecutionMonitoringService continues to call `get_lifecycle_execution` and checks the status of the `ignition.model.lifecycle.LifecycleExecution` returned. If it returns as "IN_PROGRESS" then the job is placed back on the job queue and called again later. If the status is "COMPLETE" or "FAILED", the LifecycleExecutionMonitoringService uses the LifecycleMessagingService to send out a message on Kafka to inform Brent of the result.

If the execution has failed, the `LifecycleDriver` should include `failure_details` on the `LifecycleExecution`. This must be an instance of `ignition.model.failure.FailureDetails` and description of the error and one of the following failure codes:

| Failure Code | Description |
| --- | --- |
| RESOURCE_NOT_FOUND | An element of the Resource (most likely the Infrastructure) cannot be found | 
| INFRASTRUCTURE_ERROR | There was an error with the Infrastructure |
| INSUFFICIENT_CAPACITY | There is not enough capacity in the VIM to complete this execution |
| INTERNAL_ERROR | For all other types of errors |
