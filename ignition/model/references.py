class FindReferenceResponse():

    def __init__(self, result=None):
        self.result = result

    def __str__(self):
        return f'result: {self.result}'


class FindReferenceResult():

    def __init__(self, associated_topology=None, outputs=None):
        self.associated_topology = associated_topology if associated_topology is not None else []
        self.outputs = outputs if outputs is not None else []

    def __str__(self):
        return f'associated_topology: {self.associated_topology} outputs: {self.outputs}'


def find_reference_response_dict(find_reference_response):
    result = None
    if find_reference_response.result is not None:
        result = {
            'associatedTopology': find_reference_response.result.associated_topology,
            'outputs': find_reference_response.result.outputs
        }
    message = {'result': result}
    return message