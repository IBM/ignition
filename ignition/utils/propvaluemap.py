from collections.abc import MutableMapping
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)

OBFUSCATED_VALUE = "****"

class PropValueMap(MutableMapping):
    def __init__(self, values={}):
        self.values = OrderedDict()
        self.update(values)

    def __getitem__(self, key):
        valueAndType = self.values[key]
        if valueAndType is None:
            return None
        else:
            return valueAndType['value']

    def __delitem__(self, key):
        del self.values[key]

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            if value.get('type', None) is None:
                raise ValueError("Value must have a type property")
            if value['type'] == 'key':
                if value.get('privateKey', None) is None:
                    raise ValueError("Value must have a privateKey property")
            else:
                if value.get('value', None) is None:
                    raise ValueError("Value must have a value property")
            if key in self:
                del self[self[key]]
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

    def get_type(self, propName):
        value_and_type = self.__getitem__(propName)
        if value_and_type is None:
            return None
        else:
            return value_and_type.type

    def obfuscate_value(self, prop_value):
        if prop_value[1]['type'] == 'key':
            prop_value[1]['value'] = OBFUSCATED_VALUE
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
        idx = self.idx
        self.idx += 1
        return self.propvaluemap.get_value_and_type(self.keys[idx])
