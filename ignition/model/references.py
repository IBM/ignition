class FindReferenceResponse():

    def __init__(self, result=None):
        self.result = result

    def __str__(self):
        return f'result: {self.result}'


class FindReferenceResult():

    def __init__(self, resource_id, associated_topology=None, outputs=None):
        self.resource_id = resource_id
        self.associated_topology = associated_topology
        self.outputs = outputs if outputs is not None else []

    def __str__(self):
        return f'resource_id: {self.resource_id} associated_topology: {self.associated_topology} outputs: {self.outputs}'


def find_reference_response_dict(find_reference_response):
    converted_result = None
    if find_reference_response.result is not None:
        find_result = find_reference_response.result
        converted_result = {
            'resourceId': find_result.resource_id,
            'outputs': find_result.outputs
        }
        if find_result.associated_topology is not None:
            converted_result['associatedTopology'] = find_result.associated_topology.to_dict()
        else:
            converted_result['associatedTopology'] = {}
    message = {'result': converted_result}
    return message