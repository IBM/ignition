# Infrastructure

The Infrastructure API is a requirement of any VIM Driver. All of the APIs and Services listed below are enabled by default when using the `ignition.boot.api.build_vim_driver` method. 

## APIs

Ignition can bootstrap the following API for Infrastructure:

| Name               | Required Capability         | Bootstrap Enable/Disable flag        | Description                                                                                                                       |
| ------------------ | --------------------------- | ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| Infrastructure API | InfrastructureApiCapability | bootstrap.infrastructure.api_enabled | Adds the Infrastructure API to the Connexion app, registering the service offering the InfrastructureApiCapability as the handler |

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