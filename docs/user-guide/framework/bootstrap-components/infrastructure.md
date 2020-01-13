# Infrastructure

The Infrastructure API is a requirement of any VIM Driver. All of the APIs and Services listed below are enabled by default when using the `ignition.boot.api.build_vim_driver` method. 

## APIs

Ignition can bootstrap the following API for Infrastructure:

| Name               | Required Capability         | Bootstrap Enable/Disable flag        | Description                                                                                                                       |
| ------------------ | --------------------------- | ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| Infrastructure API | InfrastructureApiCapability | bootstrap.infrastructure.api_enabled | Adds the Infrastructure API to the Connexion app, registering the service offering the InfrastructureApiCapability as the handler |

When enabled this API will be accessible at `/api/infrastructure` (view the Swagger for it at `/api/infrastructure/ui` of a running driver).

The specification for this API is built into the Ignition Python package so must be viewed through the Swagger UI or at the Ignition Github page (`ignition/openapi/vim_infrastructure.yaml`).

## Services

Ignition can bootstrap the following services for the Infrastructure API:

| Name                                | Capability                             | Required Capabilities                  | Bootstrap Enable/Disable flag                       | Description                                                                                                                                           |
| ----------------------------------- | -------------------------------------- | -------------------------------------- | --------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| InfrastructureApiService            | InfrastructureApiCapability            | InfrastructureServiceCapability        | bootstrap.infrastructure.api_service_enabled        | Handles API requests, passing calls down to the Infrastructure Service                                                                                |
| InfrastructureService               | InfrastructureServiceCapability        | InfrastructureTaskMonitoringCapability | bootstrap.infrastructure.service_enabled            | Service layer for handling Infrastructure requests, will ultimately call a driver (to do something in the target VIM)                                 |
| InfrastructureTaskMonitoringService | InfrastructureTaskMonitoringCapability | InfrastructureMessagingCapability      | bootstrap.infrastructure.monitoring_service_enabled | Service used by the Infrastructure Service to monitor the progress of create/delete Infrastructure requests, sending a message on Kafka when complete |
| InfrastructureMessagingService      | InfrastructureMessagingCapability      | PostalCapability                       | bootstrap.infrastructure.messaging_service_enabled  | Service used by the Infrastructure Monitoring Service to send a message to Kafka for Infrastructure task updates                                      |

All Capability and Service implementations for Infrastructure can be found in the `service.infrastructure` module.

By bootstrapping the above services, all you need to provide is a Service that fulfills the InfrastructureDriverCapability and you will have a functioning Infrastructure API.

## Configuration Properties

The InfrastructureMessagingService depends on on the `topics.infrastructure_task_events` property of the `MessagingProperties` group. This means the following configuration properties impact the messaging service:

| Property | Description | Default |
| --- | --- | --- |
| messaging.topics.infrastructure_task_events.name | Name of the topic used to pass messages back to Brent | lm_vim_infrastructure_task_events | 
| messaging.topics.infrastructure_task_events.auto_create | Enable/disable auto-creation of the topic. This topic is usually created by an LM installation | False | 
| messaging.topics.infrastructure_task_events.config | Map of configuration to be passed to the Topic when creating it | {} |

# Integration with your Infrastructure Driver

Let's look at the InfrastructureDriverCapability:

```python
class InfrastructureDriverCapability(Capability):
    """
    The InfrastructureDriver is the expected integration point for VIM Drivers to implement communication with the VIM on an Infrastructure request
    """
    @interface
    def create_infrastructure(self, template, template_type, system_properties, properties, deployment_location):
        """
        Initiates a request to create infrastructure based on a TOSCA template.
        This method should return immediate response of the request being accepted,
        it is expected that the InfrastructureService will poll get_infrastructure_task on this driver to determine when the request has complete.

        :param str template: template of infrastructure to be created
        :param str template_type: type of template used i.e. TOSCA or Heat
        :param ignition.utils.propvaluemap.PropValueMap system_properties: properties generated by LM for this Resource: resourceId, resourceName, requestId, metricKey, resourceManagerId, deploymentLocation, resourceType
        :param ignition.utils.propvaluemap.PropValueMap properties: property values of the Resource
        :param dict deployment_location: the deployment location to deploy to
        :return: an ignition.model.infrastructure.CreateInfrastructureResponse

        :raises:
            ignition.service.infrastructure.InvalidInfrastructureTemplateError: if the Template is not valid
            ignition.service.infrastructure.TemporaryInfrastructureError: there is an issue handling this request at this time
            ignition.service.infrastructure.UnreachableDeploymentLocationError: the Deployment Location cannot be reached
            ignition.service.infrastructure.InfrastructureError: there was an error handling this request
        """
        pass

    @interface
    def get_infrastructure_task(self, infrastructure_id, request_id, deployment_location):
        """
        Get information about the infrastructure (created or deleted)

        :param str infrastructure_id: identifier of the infrastructure to check
        :param str request_id: identifier of the request to check
        :param dict deployment_location: the location the infrastructure was deployed to
        :return: an ignition.model.infrastructure.InfrastructureTask instance describing the status

        :raises:
            ignition.service.infrastructure.InfrastructureNotFoundError: if no infrastructure with the given infrastructure_id exists
            ignition.service.infrastructure.InfrastructureRequestNotFoundError: if no request with the given request_id exists
            ignition.service.infrastructure.UnreachableDeploymentLocationError: the Deployment Location cannot be reached
            ignition.service.infrastructure.TemporaryInfrastructureError: there is an issue handling this request at this time, an attempt should be made again at a later time
            ignition.service.infrastructure.InfrastructureError: there was an error handling this request
        """
        pass

    @interface
    def delete_infrastructure(self, infrastructure_id, deployment_location):
        """
        Initiates a request to delete infrastructure previously created with the given infrastructure_id.
        This method should return immediate response of the request being accepted,
        it is expected that the InfrastructureService will poll get_infrastructure_task on this driver to determine when the request has complete.

        :param str infrastructure_id: identifier of the infrastructure to be removed
        :param dict deployment_location: the location the infrastructure was deployed to
        :return: an ignition.model.infrastructure.DeleteInfrastructureResponse

        :raises:
            ignition.service.infrastructure.InfrastructureNotFoundError: if no infrastructure with the given infrastructure_id exists
            ignition.service.infrastructure.UnreachableDeploymentLocationError: the Deployment Location cannot be reached
            ignition.service.infrastructure.TemporaryInfrastructureError: there is an issue handling this request at this time, an attempt should be made again at a later time
            ignition.service.infrastructure.InfrastructureError: there was an error handling this request
        """
        pass

    @interface
    def find_infrastructure(self, template, template_type, instance_name, deployment_location):
        """
        Finds infrastructure instances that meet the requirements set out in the given TOSCA template, returning the desired output values from those instances

        :param str template: tosca template of infrastructure to be found
        :param str template_type: type of template used i.e. TOSCA or Heat
        :param str instance_name: name given as search criteria
        :param dict deployment_location: the deployment location to deploy to
        :return: an ignition.model.infrastructure.FindInfrastructureResponse

        :raises:
            ignition.service.infrastructure.InvalidInfrastructureTemplateError: if the Template is not valid
            ignition.service.infrastructure.UnreachableDeploymentLocationError: the Deployment Location cannot be reached
            ignition.service.infrastructure.TemporaryInfrastructureError: there is an issue handling this request at this time, an attempt should be made again at a later time
            ignition.service.infrastructure.InfrastructureError: there was an error handling this request
        """
        pass
```

There are several methods required on any Service implementing this Capability, in order to serve Create/Delete/Find infrastructure requests. The following sections describe the flow of an incoming request, outlines the role of Ignition and how your driver implementation is used.

## On Create

The InfrastructureApiService handles the incoming HTTP request, parsing the headers and body before making a call to the InfrastructureService with the expected arguments. 

The InfrastructureService forwards this call down to the `create_infrastructure` method on the `InfrastructureDriver` provided by the user. 

The `InfrastructureDriver` is expected to either:
- Complete the request by initiating a creation of the infrastructure, returning immediately with an instance of `ignition.model.infrastructure.CreateInfrastructureResponse` which includes an `infrastructure_id` and `request_id` which may be used at a later time to check the status of the infrastructure being created. For example, in the Openstack VIM driver implementation, we return the Stack ID assigned to infrastructure.
- Raise an Exception if the request is invalid or cannot be accepted. This Exception will end the continuation of this flow and instead result in an error being returned to the client of the InfrastructureApiService.

On receipt of a CreateInfrastructureResponse, the InfrastructureService will inform the InfrastructureTaskMonitoringService that it should monitor the completion of the infrastructure creation, using the `infrastructure_id` and `request_id` on the response.

The InfrastructureTaskMonitoringService will periodically, using the JobQueueService (see [job queue](./job_queue)), check if infrastructure has been created. It will do this by polling the `get_infrastructure_task` method of the `InfrastructureDriver` (particular care should be taken raising Exceptions from this method, see the [errors](#errors) section of this document).

Meanwhile, the InfrastructureService will return the `CreateInfrastructureResponse` to the InfrastructureApiService, so it may convert it to a HTTP response and return it to the original client.

In the background, InfrastructureTaskMonitoringService continues to call `get_infrastructure_task` and checks the status of the `ignition.model.infrastructure.InfrastructureTask` returned. If it returns as "IN_PROGRESS" then the job is placed back on the job queue and called again later. If the status is "COMPLETE" or "FAILED", the InfrastructureTaskMonitoringService uses the InfrastructureMessagingService to send out a message on Kafka to inform Brent of the result. 

If the task has failed, the `InfrastructureDriver` should include `failure_details` on the `InfrastructureTask`. This must be an instance of `ignition.model.failure.FailureDetails` and description of the error and one of the following failure codes:

| Failure Code | Description |
| --- | --- |
| RESOURCE_ALREADY_EXISTS | An element of the Infrastructure cannot be created |
| INFRASTRUCTURE_ERROR | There was an error creating the Infrastructure |
| INSUFFICIENT_CAPACITY | There is not enough capacity in the VIM to create this Infrastructure |
| INTERNAL_ERROR | For all other types of errors |

## On Delete

The flow of a delete infrastructure request is the same as a create - instead of `create_infrastructure` the `delete_infrastructure` method of the user provided `InfrastructureDriver` is called and a `ignition.model.infrastructure.DeleteInfrastructureResponse` is expected. 

## On Find

The InfrastructureApiService handles the incoming HTTP request, parsing the headers and body before making a call to the InfrastructureService with the expected arguments. 

The InfrastructureService forwards this call down to the `find_infrastructure` method on the `InfrastructureDriver` provided by the user. 

The `InfrastructureDriver` is expected to complete the request and return an instance of a `ignition.model.infrastructure.FindInfrastructureResponse` with details of whether the infrastructure could be found or not. 

The InfrastructureService takes this result and returns it to the InfrastructureApiService so it may be converted to a HTTP response and returned to the original client.

## Errors

Your InfrastructureDriver is free to raise any Python errors when handling create, delete, get or find requests in order to indicate a failure (errors thrown by `get_infrastructure_task` have implications on the monitoring service, discussed later in this section). To customise the response returned to the API client on error, see [error handling](../../api-error-handling.md).

However, please note, in the `infrastructure` module of Ignition there are already some error types you may use:

| Error | Description |
| --- | --- |
| InvalidInfrastructureTemplateError | To be used on Create or Find, to indicate the Template provided is not valid (HTTP Status: 400) |
| InfrastructureNotFoundError | To be used on a Delete and Get requests to indicate that the infrastructure could not be found (HTTP Status: 400) | 
| InfrastructureRequestNotFoundError | To be used on a Get request to indicate the infrastructure request could not be found (HTTP Status: 400) |
| TemporaryInfrastructureError | To be used to indicate the infrastructure request cannot be managed at this time (HTTP Status: 503) |
| UnreachableDeploymentLocationError | To be used to indicate the Deployment Location cannot be reached (HTTP Status: 400) |
| InfrastructureError | General purpose error for infrastructure (HTTP Status: 500) |

The InfrastructureTaskMonitoringService has specific behaviour attached to Exception handling, as it continuously polls `get_infrastructure_task` and needs to know when it should stop monitoring a particular task. As a result, it will detect the following behaviours and react accordingly:

| Error | Handling |
| --- | --- |
| TemporaryInfrastructureError | The monitoring service will re-queue the job, to check the status of the task later |
| UnreachableDeploymentLocationError | The monitoring service will re-queue the job, to check the status of the task later |
| Any other exception | The monitoring service will forget this infrastructure request and no longer poll for it's status |
