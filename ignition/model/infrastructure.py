STATUS_IN_PROGRESS = 'IN_PROGRESS'
STATUS_COMPLETE = 'COMPLETE'
STATUS_FAILED = 'FAILED'
STATUS_UNKNOWN = 'UNKNOWN'


class CreateInfrastructureResponse():

    def __init__(self, infrastructure_id, request_id):
        self.infrastructure_id = infrastructure_id
        self.request_id = request_id


class DeleteInfrastructureResponse():

    def __init__(self, infrastructure_id, request_id):
        self.infrastructure_id = infrastructure_id
        self.request_id = request_id


class InfrastructureTask():

    def __init__(self, infrastructure_id, request_id, status, failure_details=None, outputs=None):
        self.infrastructure_id = infrastructure_id
        self.request_id = request_id
        self.status = status
        self.failure_details = failure_details
        self.outputs = outputs

    def __str__(self):
        return 'infrastructure_id: {0.infrastructure_id} request_id: {0.request_id} status: {0.status} failure_details: {0.failure_details} outputs: {0.outputs}'.format(self)


def infrastructure_task_dict(infrastructure_task):
    message = {
        'requestId': infrastructure_task.request_id,
        'infrastructureId': infrastructure_task.infrastructure_id,
        'status': infrastructure_task.status
    }
    if infrastructure_task.failure_details is not None:
        message['failureDetails'] = {
            'failureCode': infrastructure_task.failure_details.failure_code,
            'description': infrastructure_task.failure_details.description
        }
    if infrastructure_task.outputs is not None:
        message['outputs'] = infrastructure_task.outputs
    return message


class FindInfrastructureResponse():

    def __init__(self, infrastructure_id, outputs=None):
        self.infrastructure_id = infrastructure_id
        self.outputs = outputs

    def __str__(self):
        return 'infrastructure_id: {0.infrastructure_id} outputs: {0.outputs}'.format(self)


def infrastructure_find_response_dict(find_infrastructure_response):
    message = {
        'infrastructureId': find_infrastructure_response.infrastructure_id,
        'outputs': find_infrastructure_response.outputs
    }
    return message
