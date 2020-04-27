class FindReferenceResponse():

    def __init__(self, result=None):
        self.result = result

    def __str__(self):
        return f'result: {self.result}'


class FindReferenceResult():

    def __init__(self, internal_resources=None, outputs=None):
        self.internal_resources = internal_resources if internal_resources is not None else []
        self.outputs = outputs if outputs is not None else []

    def __str__(self):
        return f'internal_resources: {self.internal_resources} outputs: {self.outputs}'


def find_reference_response_dict(find_reference_response):
    result = None
    if find_reference_response.result is not None:
        result = {
            'associatedTopology': find_reference_response.result.internal_resources,
            'outputs': find_reference_response.result.outputs
        }
    message = {'result': result}
    return message