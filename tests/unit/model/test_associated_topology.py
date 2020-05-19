import unittest
from ignition.model.associated_topology import AssociatedTopologyEntry, AssociatedTopology, RemovedTopologyEntry

class TestRemovedTopologyEntry(unittest.TestCase):
    
    def test_from_dict(self):
        data = None
        entry = RemovedTopologyEntry.from_dict(data)
        self.assertIsInstance(entry, RemovedTopologyEntry)

    def test_to_dict(self):
        entry = RemovedTopologyEntry()
        self.assertIsNone(entry.to_dict())

class TestAssociatedTopologyEntry(unittest.TestCase):
    
    def test_from_dict(self):
        data = {
            'id': '123',
            'type': 'Testing'
        }
        entry = AssociatedTopologyEntry.from_dict(data)
        self.assertEqual(entry.element_id, '123')
        self.assertEqual(entry.element_type, 'Testing')
    
    def test_to_dict(self):
        entry = AssociatedTopologyEntry('123', 'Testing')
        result = entry.to_dict()
        self.assertEqual(result, {
            'id': '123',
            'type': 'Testing'
        })

class TestAssociatedTopology(unittest.TestCase):

    def test_from_dict_which_is_empty(self):
        data = {}
        topology = AssociatedTopology.from_dict(data)
        self.assertIsNotNone(topology)

    def test_from_dict(self):
        data = {
            'TestA': {
                'id': 'A',
                'type': 'VimA'
            },
            'TestB': {
                'id': 'B',
                'type': 'VimB'
            }
        }
        topology = AssociatedTopology.from_dict(data)
        find_A = topology.find_id('A')
        self.assertEqual(len(find_A), 1)
        self.assertIn('TestA', find_A)
        self.assertEqual(find_A['TestA'].element_type, 'VimA')
        find_B = topology.find_id('B')
        self.assertEqual(len(find_B), 1)
        self.assertIn('TestB', find_B)
        self.assertEqual(find_B['TestB'].element_type, 'VimB')

    def test_to_dict(self):
        entry_A = AssociatedTopologyEntry('A', 'VimA')
        entry_B = AssociatedTopologyEntry('B', 'VimB')
        topology = AssociatedTopology({'TestA': entry_A, 'TestB': entry_B})
        result = topology.to_dict()
        self.assertEqual(result,  {
            'TestA': {
                'id': 'A',
                'type': 'VimA'
            },
            'TestB': {
                'id': 'B',
                'type': 'VimB'
            }
        })
        
    def test_add(self):
        topology = AssociatedTopology()
        in_entry = AssociatedTopologyEntry('123', 'CustomType')
        topology.add('A', in_entry)
        out_entry = topology.get('A')
        self.assertEqual(out_entry, in_entry)

    def test_add_invalid(self):
        topology = AssociatedTopology()
        with self.assertRaises(ValueError) as context:
            topology.add('A', 'not_an_entry')
        self.assertEqual(str(context.exception), 'Associated topology entry should an instance of AssociatedTopologyEntry or RemovedTopologyEntry but was <class \'str\'>')

    def test_add_entry(self):
        topology = AssociatedTopology()
        topology.add_entry('A', '123', 'CustomType')
        out_entry = topology.get('A')
        self.assertEqual(out_entry, AssociatedTopologyEntry('123', 'CustomType'))

    def test_add_removed(self):
        topology = AssociatedTopology()
        topology.add_removed('A')
        out_entry = topology.get('A')
        self.assertIsInstance(out_entry, RemovedTopologyEntry)

    def test_find_id(self):
        topology = AssociatedTopology()
        topology.add_entry('A', '123', 'CustomType')
        topology.add_entry('B', '123', 'CustomType2')
        topology.add_entry('C', '456', 'CustomType')
        results = topology.find_id('123')
        self.assertEqual(len(results), 2)
        self.assertIn('A', results)
        self.assertIn('B', results)
    
    def test_find_type(self):
        topology = AssociatedTopology()
        topology.add_entry('A', '123', 'CustomType')
        topology.add_entry('B', '123', 'CustomType2')
        topology.add_entry('C', '456', 'CustomType')
        results = topology.find_type('CustomType')
        self.assertEqual(len(results), 2)
        self.assertIn('A', results)
        self.assertIn('C', results)

    def test_get_returns_none_if_not_found(self):
        topology = AssociatedTopology()
        result = topology.get('Test')
        self.assertIsNone(result)