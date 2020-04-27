import unittest
from ignition.model.associated_topology import AssociatedTopologyEntry, AssociatedTopology

class TestAssociatedTopologyEntry(unittest.TestCase):
    
    def test_from_dict(self):
        data = {
            'id': '123',
            'name': 'Test',
            'type': 'Testing'
        }
        entry = AssociatedTopologyEntry.from_dict(data)
        self.assertEqual(entry.identifier, '123')
        self.assertEqual(entry.name, 'Test')
        self.assertEqual(entry.element_type, 'Testing')
    
    def test_to_dict(self):
        entry = AssociatedTopologyEntry('123', 'Test', 'Testing')
        result = entry.to_dict()
        self.assertEqual(result, {
            'id': '123',
            'name': 'Test',
            'type': 'Testing'
        })

class TestAssociatedTopology(unittest.TestCase):

    def test_from_list(self):
        data = [
            {
                'id': 'A',
                'name': 'TestA',
                'type': 'VimA'
            },
            {
                'id': 'B',
                'name': 'TestB',
                'type': 'VimB'
            }
        ]
        resources = AssociatedTopology.from_list(data)
        resource_A = resources.get_by_id('A')
        self.assertIsNotNone(resource_A)
        self.assertEqual(resource_A.name, 'TestA')
        self.assertEqual(resource_A.element_type, 'VimA')
        resource_B = resources.get_by_id('B')
        self.assertIsNotNone(resource_B)
        self.assertEqual(resource_B.name, 'TestB')
        self.assertEqual(resource_B.element_type, 'VimB')

    def test_to_list(self):
        resource_A = AssociatedTopologyEntry('A', 'TestA', 'VimA')
        resource_B = AssociatedTopologyEntry('B', 'TestB', 'VimB')
        resources = AssociatedTopology([resource_A, resource_B])
        result = resources.to_list()
        self.assertEqual(result, [
            {
                'id': 'A',
                'name': 'TestA',
                'type': 'VimA'
            },
            {
                'id': 'B',
                'name': 'TestB',
                'type': 'VimB'
            }
        ])
        