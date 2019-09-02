STATUS_IN_PROGRESS = 'IN_PROGRESS'
STATUS_COMPLETE = 'COMPLETE'
STATUS_FAILED = 'FAILED'
STATUS_UNKNOWN = 'UNKNOWN'

class LifecycleExecuteResponse():

    def __init__(self, request_id):
        self.request_id = request_id

class LifecycleExecution():

    def __init__(self, request_id, status, failure_details=None, outputs=None):
        self.request_id = request_id
        self.status = status
        self.failure_details = failure_details
        self.outputs = outputs

    def __str__(self):
      return 'request_id: {0.request_id} status: {0.status} failure_details: {0.failure_details} outputs: {0.outputs}'.format(self)

def lifecycle_execution_dict(lifecycle_execution):
    message = {
        'requestId': lifecycle_execution.request_id,
        'status': lifecycle_execution.status
    }
    if lifecycle_execution.failure_details is not None:
        message['failureDetails'] = { 
            'failureCode': lifecycle_execution.failure_details.failure_code,
            'description': lifecycle_execution.failure_details.description
        }
    if lifecycle_execution.outputs is not None:
        message['outputs'] = lifecycle_execution.outputs
    return message