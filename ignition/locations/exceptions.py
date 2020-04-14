from ignition.api.exceptions import ApiException

class InvalidDeploymentLocationError(ApiException):
    status_code = 400
