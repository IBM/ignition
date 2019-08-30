import unittest
from ignition.boot.config import PropertyGroups, PropertyGroupError
from ignition.service.config import ConfigurationPropertiesGroup


class TestProperties(ConfigurationPropertiesGroup):

    def __init__(self):
        super().__init__('test')


class TestPropertiesB(ConfigurationPropertiesGroup):

    def __init__(self):
        super().__init__('test')


class TestPropertiesC(ConfigurationPropertiesGroup):

    def __init__(self):
        super().__init__('test')


class TestPropertyGroups(unittest.TestCase):

    def test_add_property_group(self):
        groups = PropertyGroups()
        test_props = TestProperties()
        groups.add_property_group(test_props)
        get_prop_result = groups.get_property_group(TestProperties)
        self.assertEqual(test_props, get_prop_result)

    def test_get_property_group_fails_when_not_found(self):
        groups = PropertyGroups()
        with self.assertRaises(PropertyGroupError) as context:
            groups.get_property_group(TestProperties)
        self.assertEqual(str(context.exception), 'No instance for property group class: {0}'.format(TestProperties))

    def test_all_groups(self):
        groups = PropertyGroups()
        test_propsA = TestProperties()
        test_propsB = TestPropertiesB()
        test_propsC = TestPropertiesC()
        groups.add_property_group(test_propsA)
        groups.add_property_group(test_propsB)
        groups.add_property_group(test_propsC)
        all_groups = groups.all_groups()
        self.assertIsInstance(all_groups, list)
        self.assertEqual(len(all_groups), 3)
        self.assertIn(test_propsA, all_groups)
        self.assertIn(test_propsB, all_groups)
        self.assertIn(test_propsC, all_groups)
