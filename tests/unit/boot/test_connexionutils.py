import unittest
import connexion
from unittest.mock import patch
from ignition.boot.connexionutils import build_resolver_to_instance

class DummyInstance():

    def __init__(self):
        self.method1_called = False
        self.inner = self.Inner()

    def method1(self):
        self.method1_called = True

    class Inner():

        def __init__(self):
            self.inner_method1_called = False

        def method1(self):
            self.inner_method1_called = True 

class Test_build_resolver_to_instance(unittest.TestCase):

    @patch('ignition.boot.connexionutils.build_resolver_func_to_instance')
    def test_build_resolver_to_instance(self, mock_build_resolver_func_to_instance):
        instance = DummyInstance()
        resolver = build_resolver_to_instance(instance)
        self.assertIsNotNone(resolver)
        self.assertIsInstance(resolver, connexion.resolver.Resolver)
        self.assertIsNotNone(resolver.function_resolver)
        self.assertEqual(resolver.function_resolver, mock_build_resolver_func_to_instance.return_value)

    def test_function_resolver_fails_if_function_name_is_none(self):
        instance = DummyInstance()
        resolver = build_resolver_to_instance(instance)
        with self.assertRaises(ValueError) as context:
            resolved_func = resolver.function_resolver(None)
        self.assertEqual(str(context.exception), 'Empty function name')

    @patch('ignition.boot.connexionutils.connexion.utils.get_function_from_name')
    def test_function_resolver_uses_default_resolver_if_not_prefixed(self, mock_get_function_from_name):
        instance = DummyInstance()
        resolver = build_resolver_to_instance(instance)
        resolver.function_resolver('func')
        mock_get_function_from_name.assert_called_once_with('func')

    def test_function_resolver_finds_method(self):
        instance = DummyInstance()
        resolver = build_resolver_to_instance(instance)
        resolved_func = resolver.function_resolver('.inner.method1')
        self.assertEqual(resolved_func, instance.inner.method1)
        resolved_func()
        self.assertTrue(instance.inner.inner_method1_called)

    def test_function_resolver_throws_error_when_method_not_found(self):
        instance = DummyInstance()
        resolver = build_resolver_to_instance(instance)
        with self.assertRaises(ValueError) as context:
            resolved_func = resolver.function_resolver('.meth2')
        self.assertEqual(str(context.exception), 'Cound not find meth2 in {0}'.format(instance))
