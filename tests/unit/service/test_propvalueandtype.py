import unittest
import logging
import sys
from ignition.utils.propvaluemap import PropValueMap, OBFUSCATED_VALUE
from ignition.api.exceptions import BadRequest

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)

class TestPropValueAndType(unittest.TestCase):

    def test_constructor(self):
        PropValueMap({
            'prop1': {
                'value': 'value1',
                'type': 'string'
            },
            'prop2': {
                'value': 'value2',
                'type': 'key'
            }
        })

        with self.assertRaises(ValueError) as context:
            PropValueMap({
                'prop1': {
                    'value': 'value1',
                },
                'prop2': {
                    'value': 'value2',
                    'type': 'key'
                }
            })
            self.assertTrue('Value must have a type property' in context.exception)

        with self.assertRaises(ValueError) as context:
            PropValueMap({
                'prop1': {
                    'type': 'string',
                },
                'prop2': {
                    'value': 'value2',
                    'type': 'key'
                }
            })
            self.assertTrue('Value must have a value property' in context.exception)

    def test_basic_update_and_get(self):
        values = PropValueMap({
            'prop1': {
                'value': 'value1',
                'type': 'string'
            },
            'prop2': {
                'value': 'value2',
                'type': 'key'
            }
        })
        self.assertEqual(values.get('prop1', None), 'value1')
        self.assertEqual(values.get('prop3', None), None)
        self.assertEqual(values['prop1'], 'value1')

        with self.assertRaises(ValueError) as context:
            values['prop3'] = "value3"
            self.assertTrue('Value must have a type property' in context.exception)

        with self.assertRaises(ValueError) as context:
            values['prop3'] = {
                "type": "string"
            }
            self.assertTrue('Value must have a value property' in context.exception)

        values['prop3'] = {
            "value": "value3",
            "type": "string"
        }
        self.assertEqual(values.get('prop3', None), "value3")
        self.assertEqual(values['prop3'], "value3")

    def test_get_keys(self):
        values = PropValueMap({
            'prop1': {
                'value': 'value1',
                'type': 'string'
            },
            'prop2': {
                'value': 'value2',
                'type': 'key'
            },
            'prop3': {
                'value': 'value3',
                'type': 'string'
            }
        })

        self.assertEqual(values.get_keys(), PropValueMap({
            'prop2': {
                'value': 'value2',
                'type': 'key'
            }
        }))

        self.assertEqual(next(iter(values.get_keys().items())), ('prop2', 'value2'))

    def test_items_with_types(self):
        values = PropValueMap({
            'prop1': {
                'value': 'value1',
                'type': 'string'
            },
            'prop2': {
                'value': 'value2',
                'type': 'key'
            },
            'prop3': {
                'value': 'value3',
                'type': 'string'
            }
        })

        it = values.items_with_types()
        self.assertEqual(next(it), {
            'value': 'value1',
            'type': 'string'
        })

    def test_get_props(self):
        values = PropValueMap({
            'prop1': {
                'value': 'value1',
                'type': 'string'
            },
            'prop2': {
                'value': 'value2',
                'type': 'key'
            },
            'prop3': {
                'value': 'value3',
                'type': 'string'
            }
        })

        self.assertEqual(values.get_props(), PropValueMap({
            'prop1': {
                'value': 'value1',
                'type': 'string'
            },
            'prop2': {
                'value': OBFUSCATED_VALUE,
                'type': 'key'
            },
            'prop3': {
                'value': 'value3',
                'type': 'string'
            }
        }))

    def test_delete(self):
        values = PropValueMap({
            'prop1': {
                'value': 'value1',
                'type': 'string'
            },
            'prop2': {
                'value': 'value2',
                'type': 'key'
            },
            'prop3': {
                'value': 'value3',
                'type': 'string'
            }
        })

        del values['prop1']
        self.assertEqual(values, PropValueMap({
            'prop2': {
                'value': 'value2',
                'type': 'key'
            },
            'prop3': {
                'value': 'value3',
                'type': 'string'
            }
        }))

        with self.assertRaises(KeyError) as context:
            del values['prop1']
            self.assertEqual(values, PropValueMap({
                'prop2': {
                    'value': 'value2',
                    'type': 'key'
                },
                'prop3': {
                    'value': 'value3',
                    'type': 'string'
                }
            }))




