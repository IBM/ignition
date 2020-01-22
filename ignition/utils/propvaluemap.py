from collections.abc import MutableMapping
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)

OBFUSCATED_VALUE = "****"

"""
A dictionary that holds property type and value for driver requests, with special handling
for key properties.
"""
class PropValueMap(MutableMapping):
    def __init__(self, values={}):
        self.values = OrderedDict()
        self.update(values)

    def __getitem__(self, key):
        value_and_type = self.values[key]
        if value_and_type is None:
            return None
        elif value_and_type['type'] == 'key':
            value = value_and_type['privateKey']
            public_key = value_and_type.get('publicKey', None)
            if public_key is not None:
                value += '\n---\n' + public_key
            return value
        else:
            return value_and_type['value']

    def __delitem__(self, key):
        del self.values[key]

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            if value.get('type', None) is None:
                raise ValueError("Value must have a type property")
            if value['type'] == 'key':
                if value.get('privateKey', None) is None:
                    raise ValueError("Value must have a privateKey property")
            if 'value' not in value:
                value['value'] = None
            if key in self:
                del self.values[key]
            self.values[key] = value
        else:
            # assume type == 'string'
            self.values[key] = {
                'value': value,
                'type': 'string'
            }

    def __iter__(self):
        return iter(self.values)

    def __len__(self):
        return len(self.values)

    def __repr__(self):
        return f"{type(self).__name__}({self.values})"

    def get_type(self, prop_name):
        value_and_type = self.__getitem__(prop_name)
        if value_and_type is None:
            return None
        else:
            return value_and_type.type

    def obfuscate_value(self, prop_value):
        if prop_value[1]['type'] == 'key':
            prop_value[1]['privateKey'] = OBFUSCATED_VALUE
        return prop_value

    def get_value_and_type(self, key, default=None):
        return self.values.get(key, default)

    def items_with_types(self):
        return ValueAndTypeIterator(self)

    """
    get properties, with "key" values obfuscated as "*****"
    """
    def get_props(self):
        logger.info('get_props')
        return PropValueMap(dict(map(self.obfuscate_value, self.values.items())))

    """ 
    get key properties, complete with un-obfuscated value
    """
    def get_keys(self):
        return PropValueMap({ prop_name: prop_value for prop_name, prop_value in self.values.items() if prop_value['type'] == 'key'})

class ValueAndTypeIterator:
    def __init__(self, propvaluemap):
        self.propvaluemap = propvaluemap
        self.keys = list(propvaluemap.keys())
        self.idx = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.idx < len(self.keys):
            idx = self.idx
            self.idx += 1
            return (self.keys[idx], self.propvaluemap.get_value_and_type(self.keys[idx]))
        else:
            raise StopIteration
