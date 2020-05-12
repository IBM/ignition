# Resource Driver

The Resource Driver API is a requirement of any Resource driver. All of the APIs and Services listed below are enabled by default when using the `ignition.boot.api.build_resource_driver` method.

## APIs

Ignition will bootstrap the following API for the driver:

| Name          | Required Capability    | Bootstrap Enable/Disable flag   | Description                                                                                                             |
| ------------- | ---------------------- | ------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Resource Driver API | ResourceDriverApiCapability | bootstrap.resource_driver.api_enabled | Adds the Resource Driver API to the Connexion app, registering the service offering the ResourceDriverApiCapability as the handler |

When enabled this API will be accessible at `/api/driver` (view the Swagger for it at `/api/driver/ui` on a running driver).

The specification for this API is built into the Ignition Python package so must be viewed through the Swagger UI or at the Ignition Github page (`ignition/openapi/resource-driver.yaml`).

## Services

Ignition can bootstrap the following services for the Resource Driver API:

| Name                                | Capability                             | Required Capabilities                  | Bootstrap Enable/Disable flag                  | Description                                                                                                                                |
| ----------------------------------- | -------------------------------------- | -------------------------------------- | ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| ResourceDriverApiService                 | ResourceDriverApiCapability                 | ResourceDriverServiceCapability             | bootstrap.resource_driver.api_service_enabled        | Handles API requests, passing calls down to the ResourceDriverService Service                                                                          |
| ResourceDriverService                    | ResourceDriverServiceCapability             | LifecycleExecutionMonitoringCapability, ResourceDriverHandlerCapability | bootstrap.resource_driver.service_enabled            | Service layer for handling execution requests, will ultimately call a handler (to handle the implementation of the request) |
| LifecycleExecutionMonitoringService | LifecycleExecutionMonitoringCapability | LifecycleMessagingCapability           | bootstrap.resource_driver.lifecycle_monitoring_service_enabled | Service used by the ResourceDriverService to monitor the progress of execution requests, sending a message on Kafka when complete              |
| LifecycleMessagingService           | LifecycleMessagingCapability           | PostalCapability                       | bootstrap.resource_driver.lifecycle_messaging_service_enabled  | Service used by the LifecycleMonitoringService to send a message to Kafka for Lifecycle execution updates                                |

All Capability and Service implementations for the Resource Driver API can be found in the `service.resourcedriver` module.

By bootstrapping the above services, all you need to provide is a Service that fulfills the ResourceDriverHandlerCapability and you will have a functioning Resource Driver API.

## Configuration Properties

The LifecycleMessagingService depends on on the `topics.lifecycle_execution_events` property of the `MessagingProperties` group. This means the following configuration properties impact the messaging service:

| Property | Description | Default |
| --- | --- | --- |
| messaging.topics.lifecycle_execution_events.name | Name of the topic used to pass messages back to Brent | lm_vnfc_lifecycle_execution_events | 
| messaging.topics.lifecycle_execution_events.auto_create | Enable/disable auto-creation of the topic. This topic is usually created by an LM installation | False | 
| messaging.topics.lifecycle_execution_events.config | Map of configuration to be passed to the Topic when creating it | {} |

# Integration with your Driver

Let's look at the ResourceDriverHandlerCapability:

```python
class ResourceDriverHandlerCapability(Capability):

    @interface
    def execute_lifecycle(self, lifecycle_name, driver_files, system_properties, resource_properties, request_properties, associated_topology, deployment_location):
        """
        Execute a lifecycle transition/operation for a Resource.
        This method should return immediate response of the request being accepted,
        it is expected that the ResourceDriverService will poll get_lifecycle_execution on this driver to determine when the request has completed (or devise your own method).

        :param str lifecycle_name: name of the lifecycle transition/operation to execute
        :param ignition.utils.file.DirectoryTree driver_files: object for navigating the directory intended for this driver from the Resource package. The user should call "remove_all" when the files are no longer needed
        :param ignition.utils.propvaluemap.PropValueMap system_properties: properties generated by LM for this Resource: resourceId, resourceName, requestId, metricKey, resourceManagerId, deploymentLocation, resourceType
        :param ignition.utils.propvaluemap.PropValueMap resource_properties: property values of the Resource
        :param ignition.utils.propvaluemap.PropValueMap request_properties: property values of this request
        :param ignition.model.associated_topology.AssociatedTopology associated_topology: 3rd party resources associated to the Resource, from any previous transition/operation requests
        :param dict deployment_location: the deployment location the Resource is assigned to
        :return: an ignition.model.lifecycle.LifecycleExecuteResponse

        :raises:
            ignition.service.resourcedriver.InvalidDriverFilesError: if the scripts are not valid
            ignition.service.resourcedriver.InvalidRequestError: if the request is invalid e.g. if no script can be found to execute the transition/operation given by lifecycle_name
            ignition.service.resourcedriver.TemporaryResourceDriverError: there is an issue handling this request at this time
            ignition.service.resourcedriver.ResourceDriverError: there was an error handling this request
        """
        pass

    @interface
    def get_lifecycle_execution(self, request_id, deployment_location):
        """
        Retreive the status of a lifecycle transition/operation request

        :param str request_id: identifier of the request to check
        :param dict deployment_location: the deployment location the Resource is assigned to
        :return: an ignition.model.lifecycle.LifecycleExecution
        
        :raises:
            ignition.service.resourcedriver.RequestNotFoundError: if no request with the given request_id exists
            ignition.service.resourcedriver.TemporaryResourceDriverError: there is an issue handling this request at this time, an attempt should be made again at a later time
            ignition.service.resourcedriver.ResourceDriverError: there was an error handling this request
        """
        pass

    @interface 
    def find_reference(self, instance_name, driver_files, deployment_location):
        """
        Find a Resource, returning the necessary property output values and internal resources from those instances

        :param str instance_name: name used to filter the Resource to find
        :param ignition.utils.file.DirectoryTree driver_files: object for navigating the directory intended for this driver from the Resource package. The user should call "remove_all" when the files are no longer needed
        :param dict deployment_location: the deployment location to find the instance in
        :return: an ignition.model.references.FindReferenceResponse

        :raises:
            ignition.service.resourcedriver.InvalidDriverFilesError: if the scripts are not valid
            ignition.service.resourcedriver.InvalidRequestError: if the request is invalid e.g. if no script can be found to execute the transition/operation given by lifecycle_name
            ignition.service.resourcedriver.TemporaryResourceDriverError: there is an issue handling this request at this time
            ignition.service.resourcedriver.ResourceDriverError: there was an error handling this request
        """
```

There are several methods required on any Service implementing this Capability, in order to serve execute requests. The following sections describe the flow of an incoming request, outlines the role of Ignition and how your driver implementation is used.

## On Execute

The ResourceDriverApiService handles the incoming HTTP request, parsing the headers and body before making a call to the ResourceDriverService with the expected arguments. 

The ResourceDriverService takes the base64 encoded version of the `driver_files`, writes them to disk, then extracts the contents so they are available as full directories and files. The Service then calls the `execute_lifecycle` method on the ResourceDriverHandler provided by the user, passing all of the original parameters but with the `driver_files` base64 string replaced with a `ignition.utils.file.DirectoryTree` instance, which can be used to interact with the extracted contents of the files. 

The ResourceDriverHandler is expected to either:
- Complete the request by initiating execution of the target lifecycle, returning immediately with an instance of `ignition.model.lifecycle.LifecycleExecuteResponse` which includes a `request_id` which may be used at a later time to check the status of the execution.
- Raise an Exception if the request is invalid or cannot be accepted. This Exception will end the continuation of this flow and instead result in an error being returned to the client of the ResourceDriverApiService. 

On receipt of a LifecycleExecuteResponse, the ResourceDriverService will inform the LifecycleExecutionMonitoringService that it should monitor the completion of the execution, using the `request_id` from the response.

The LifecycleExecutionMonitoringService will periodically, using the JobQueueService (see [job queue](./job_queue)), check if execution has complete. It will do this by polling the `get_lifecycle_execution` method of the ResourceDriverHandler (particular care should be taken raising Exceptions from this method, see the [errors](#errors) section of this document).

Meanwhile, the ResourceDriverService will return the LifecycleExecuteResponse to the ResourceDriverApiService, so it may convert it to a HTTP response and return it to the original client.

In the background, LifecycleExecutionMonitoringService continues to call `get_lifecycle_execution` and checks the status of the `ignition.model.lifecycle.LifecycleExecution` returned. If it returns as "IN_PROGRESS" then the job is placed back on the job queue and called again later. If the status is "COMPLETE" or "FAILED", the LifecycleExecutionMonitoringService uses the LifecycleMessagingService to send out a message on Kafka to inform Brent of the result.

If the execution has failed, the ResourceDriverHandler should include `failure_details` on the `LifecycleExecution`. This must be an instance of `ignition.model.failure.FailureDetails` and description of the error and one of the following failure codes:

| Failure Code | Description |
| --- | --- |
| RESOURCE_NOT_FOUND | An element of the Resource (most likely the Infrastructure) cannot be found | 
| INFRASTRUCTURE_ERROR | There was an error with the Infrastructure |
| INSUFFICIENT_CAPACITY | There is not enough capacity in the VIM to complete this execution |
| INTERNAL_ERROR | For all other types of errors |

## Execution Errors

Your ResourceDriverHandler is free to raise any Python errors when handling execution requests in order to indicate a failure (errors thrown by `get_lifecycle_execution` have implications on the monitoring service, discussed later in this section). To customise the response returned to the API client on error, see [error handling](../../api-error-handling.md).

In the `resourcedriver` module of Ignition there are existing error types you are encouraged to use:

| Error | Description |
| --- | --- |
| UnreachableDeploymentLocationError | To be used for issues related to connecting with the deployment location |
| InvalidDriverFilesError | To be used for issues related to the files provided (HTTP Status: 400) |
| InvalidLifecycleNameError | To be used on execute to indicate the lifecycle_name provided is not valid (HTTP Status: 400) |
| RequestNotFoundError | To be used on a Get request to indicate the request could not be found (HTTP Status: 400) |
| TemporaryResourceDriverError | To be used to indicate the request cannot be managed at this time (HTTP Status: 503) |
| ResourceDriverError | General purpose error for driver requests (HTTP Status: 500) |

The LifecycleExecutionMonitoringService has specific behaviour attached to Exception handling, as it continuously polls `get_lifecycle_execution` and needs to know when it should stop monitoring a particular task. As a result, it will detect the following behaviours and react accordingly:

| Error | Handling |
| --- | --- |
| TemporaryResourceDriverError | The monitoring service will re-queue the job, to check the status of the task later |
| Any other exception | The monitoring service will forget this request and no longer poll for it's status |

## On Find

The ResourceDriverApiService handles the incoming HTTP request, parsing the headers and body before making a call to the ResourceDriverService with the expected arguments. 

The ResourceDriverService forwards this call down to the `find_reference` method on the ResourceDriverHandler provided by the user. 

The ResourceDriverHandler is expected to complete the request and return an instance of a `ignition.model.resourcedriver.FindReferenceResponse` with details of whether the Resource could be found or not. 

The ResourceDriverService takes this result and returns it to the ResourceDriverApiService so it may be converted to a HTTP response and returned to the original client.

## Find Errors

All errors raised during a `find_reference` request are converted to a suitable HTTP response. You should use any of the errors described in [Execution Errors](#execution-errors) where suitable, otherwise raise custom errors instead.