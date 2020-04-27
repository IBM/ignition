STATUS_IN_PROGRESS = 'IN_PROGRESS'
STATUS_COMPLETE = 'COMPLETE'
STATUS_FAILED = 'FAILED'
STATUS_UNKNOWN = 'UNKNOWN'

class LifecycleExecuteResponse():

    def __init__(self, request_id, associated_topology=None):
        self.request_id = request_id
        self.associated_topology = associated_topology

def lifecycle_execute_response_dict(execute_response):
    message = {
        'requestId': execute_response.request_id
    }
    if execute_response.associated_topology is not None:
        message['associatedTopology'] = execute_response.associated_topology.to_dict()
    else:
        message['associatedTopology'] = {}
    return message

class LifecycleExecution():

    def __init__(self, request_id, status, failure_details=None, outputs=None, associated_topology=None):
        self.request_id = request_id
        self.status = status
        self.failure_details = failure_details
        self.outputs = outputs
        self.associated_topology = associated_topology

    def __str__(self):
      return f'request_id: {self.request_id} status: {self.status} failure_details: {self.failure_details} outputs: {self.outputs} associated_topology: {self.associated_topology}'

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
    else:
        message['outputs'] = {}
    if lifecycle_execution.associated_topology is not None:
        message['associatedTopology'] = lifecycle_execution.associated_topology.to_dict()
    else:
        message['associatedTopology'] = {}
    return message