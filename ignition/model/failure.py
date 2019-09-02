FAILURE_CODE_RESOURCE_ALREADY_EXISTS = 'RESOURCE_ALREADY_EXISTS'
FAILURE_CODE_RESOURCE_NOT_FOUND = 'RESOURCE_NOT_FOUND'
FAILURE_CODE_INFRASTRUCTURE_ERROR = 'INFRASTRUCTURE_ERROR'
FAILURE_CODE_INSUFFICIENT_CAPACITY = 'INSUFFICIENT_CAPACITY'
FAILURE_CODE_INTERNAL_ERROR = 'INTERNAL_ERROR'
FAILURE_CODE_UNKNOWN = 'UNKNOWN'

class FailureDetails():
    def __init__(self, failure_code, description=None):
        self.failure_code = failure_code
        self.description = description

    def __str__(self):
      return 'failure_code: {0.failure_code} description: {0.description}'.format(self)
