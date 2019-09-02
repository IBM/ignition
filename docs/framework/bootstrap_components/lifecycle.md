# Lifecycle

The Lifecycle API is a requirement of any Lifecycle Driver. All of the APIs and Services listed below are enabled by default when using the `ignition.boot.api.build_lifecycle_driver` method.

## APIs

Ignition can bootstrap the following API for Lifecycle:

| Name          | Required Capability    | Bootstrap Enable/Disable flag   | Description                                                                                                             |
| ------------- | ---------------------- | ------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Lifecycle API | LifecycleApiCapability | bootstrap.lifecycle.api_enabled | Adds the Lifecycle API to the Connexion app, registering the service offering the LifecycleApiCapability as the handler |

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
