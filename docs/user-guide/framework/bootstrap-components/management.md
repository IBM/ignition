# Management

The Management API is provided to offer useful endpoints for common application administrative tasks.

All Services listed below are enabled by default on any Ignition application.

## APIs

The following API is bootstrapped by Ignition:

| Name               | Required Capability         | Bootstrap Enable/Disable flag        | Description                                                                                                                       |
| ------------------ | --------------------------- | ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| Management API | ManagementApi | bootstrap.management.api_enabled | Adds the Management API to the Connexion app, registering the service offering the ManagementApi as the handler |

When enabled this API will be accessible at `/management`.

The specification for this API is built into the Ignition Python package so must be viewed at the Ignition Github page (`ignition/openapi/management.yaml`).

## Services

To fulfill the Management APIs, the following services are bootstrapped by Ignition:

| Name                                | Capability                             | Required Capabilities                  | Bootstrap Enable/Disable flag                       | Description                                                                                                                                           |
| ----------------------------------- | -------------------------------------- | -------------------------------------- | --------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| ManagementApiService            | ManagementApi            | Management        | bootstrap.management.api_service_enabled        | Handles API requests, passing calls down to the service offering the Management capability                                                                            |
| ManagementService            | Management            | HealthChecker        | bootstrap.management.service_enabled        | Service layer for handling Management API requests                                                                            |
| HealthCheckerService            | HealthChecker            | -        | bootstrap.management.health.service_enabled        | Service used by the default ManagementService to check the Health of the application                                                                            |


All Capability and Service implementations for Management can be found in the `service.management` and `service.health` modules.

It is recommended that you do not disable or replace the above services. In future releases, the HealthCheck will be expanded to allow driver developers to customise the response based on their requirements.




