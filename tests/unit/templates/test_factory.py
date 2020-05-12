import unittest 
import os
import tempfile
import shutil
import ignition
import ignition.templates.factory as factory

EXPECTED_PRODUCTS_DIR = os.path.dirname(__file__)
EXPECTED_RESOURCE_DRIVER = os.path.join(EXPECTED_PRODUCTS_DIR, 'expected_resource_driver')

class TestDriverGenRequest(unittest.TestCase):

    def test_init(self):
        request = factory.DriverGenRequest([factory.DRIVER_TYPE_RESOURCE], 'Test Driver', '0.5.0', port=7777, module_name='tdriver', \
            description='unit test driver', docker_name='tddock', helm_name='tdhelm', helm_node_port='30777')
        self.assertEqual(request.driver_types, [factory.DRIVER_TYPE_RESOURCE])
        self.assertEqual(request.app_name, 'Test Driver')
        self.assertEqual(request.version, '0.5.0')
        self.assertEqual(request.port, 7777)
        self.assertEqual(request.module_name, 'tdriver')
        self.assertEqual(request.description, 'unit test driver')
        self.assertEqual(request.docker_name, 'tddock')
        self.assertEqual(request.helm_name, 'tdhelm')
        self.assertEqual(request.helm_node_port, '30777')

    def test_defaults(self):
        request = factory.DriverGenRequest([factory.DRIVER_TYPE_RESOURCE], 'Test Driver', '0.5.0')
        self.assertEqual(request.module_name, 'testdriver')
        self.assertTrue(request.port >= 7000 and request.port <= 7999)
        self.assertEqual(request.description, None)
        self.assertEqual(request.docker_name, 'test-driver')
        self.assertEqual(request.helm_name, 'test-driver')
        self.assertTrue(request.helm_node_port >= 30000 and request.helm_node_port <= 30999)

    def test_default_module_name(self):
        request = factory.DriverGenRequest([factory.DRIVER_TYPE_RESOURCE], 'Test-_Special !"£$%^&*()+={}[]:;@~#<>?,./¬ Chars', '0.5.0')
        self.assertEqual(request.module_name, 'testspecialchars')

    def test_default_helm_name(self):
        request = factory.DriverGenRequest([factory.DRIVER_TYPE_RESOURCE], 'Test-_Special !"£$%^&*()+={}[]:;@~#<>?,./¬ Chars', '0.5.0')
        self.assertEqual(request.helm_name, 'test-_special-chars')

    def test_default_docker_name(self):
        request = factory.DriverGenRequest([factory.DRIVER_TYPE_RESOURCE], 'Test-_Special !"£$%^&*()+={}[]:;@~#<>?,./¬ Chars', '0.5.0')
        self.assertEqual(request.docker_name, 'test-_special-chars')

    def __do_test_module_name_validation(self, invalid_value):
        module_name = 'invalid{0}driver'.format(invalid_value)
        with self.assertRaises(ValueError) as context:
            factory.DriverGenRequest([factory.DRIVER_TYPE_RESOURCE], 'Test Driver', '0.5.0', module_name=module_name)
        self.assertEqual(str(context.exception), 'module_name must be a string with characters from a-z, A-Z, 0-9 but was: {0}'.format(module_name))

    def test_module_name_validation(self):
        for char in '!"£$%^&*()-_+={}[]:;@~#<>?,./¬ ':
            self.__do_test_module_name_validation(char)

    def __do_test_helm_name_validation(self, invalid_value):
        helm_name = 'invalid{0}driver'.format(invalid_value)
        with self.assertRaises(ValueError) as context:
            factory.DriverGenRequest([factory.DRIVER_TYPE_RESOURCE], 'Test Driver', '0.5.0', helm_name=helm_name)
        self.assertEqual(str(context.exception), 'helm_name must be a string with characters from a-z, A-Z, 0-9, dash (-) or underscore (_) but was: {0}'.format(helm_name))

    def test_helm_name_validation(self):
        for char in '!"£$%^&*()+={}[]:;@~#<>?,./¬ ':
            self.__do_test_helm_name_validation(char)
        factory.DriverGenRequest([factory.DRIVER_TYPE_RESOURCE], 'Test Driver', '0.5.0', helm_name='dashed-driver')
        factory.DriverGenRequest([factory.DRIVER_TYPE_RESOURCE], 'Test Driver', '0.5.0', helm_name='underscore_driver')

    def __do_test_docker_name_validation(self, invalid_value):
        docker_name = 'invalid{0}driver'.format(invalid_value)
        with self.assertRaises(ValueError) as context:
            factory.DriverGenRequest([factory.DRIVER_TYPE_RESOURCE], 'Test Driver', '0.5.0', docker_name=docker_name)
        self.assertEqual(str(context.exception), 'docker_name must be a string with characters from a-z, A-Z, 0-9, dash (-) or underscore (_) but was: {0}'.format(docker_name))

    def test_helm_name_validation(self):
        for char in '!"£$%^&*()+={}[]:;@~#<>?,./¬ ':
            self.__do_test_docker_name_validation(char)
        factory.DriverGenRequest([factory.DRIVER_TYPE_RESOURCE], 'Test Driver', '0.5.0', docker_name='dashed-driver')
        factory.DriverGenRequest([factory.DRIVER_TYPE_RESOURCE], 'Test Driver', '0.5.0', docker_name='underscore_driver')


class TestDriverProducer(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def test_produce_resourcedriver(self):
        request = factory.DriverGenRequest([factory.DRIVER_TYPE_RESOURCE], 'Test Driver', '0.5.0', port=7777, module_name='tdriver', \
            description='unit test driver', docker_name='tddock', helm_name='tdhelm', helm_node_port='30777')
        producer = factory.DriverProducer(request, self.tmp_dir)
        producer.produce()
        qa = DriverProductQA(EXPECTED_RESOURCE_DRIVER, self.tmp_dir)
        qa.check()

class DriverProductQA:

    def __init__(self, expected_product, product):
        self.expected_product = expected_product
        self.product = product
        self.tc = unittest.TestCase('__init__')
        self.tc.maxDiff = None

    def check(self):
        self.__check_directory(self.expected_product, self.product)
    
     
    def __check_directory(self, expected_directory, directory):
        expected_files = os.listdir(expected_directory)
        actual_files = os.listdir(directory)
        missing_files = []
        remaining_files = actual_files.copy()
        for expected_file in expected_files.copy():
            if expected_file in actual_files:
                remaining_files.remove(expected_file)
            else:
                missing_files.append(expected_file)
        if len(missing_files)>0:
            self.tc.fail('Directory {0} is missing expected files: {1}'.format(directory, missing_files))
        if len(remaining_files)>0:
            self.tc.fail('Directory {0} has files which were not expected: {1}'.format(directory, remaining_files))
        
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            expected_item_path = os.path.join(expected_directory, item)
            if os.path.isdir(item_path):
                if not os.path.isdir(expected_item_path):
                    self.tc.fail('Item {0} is not expected to be a directory'.format(item_path))
                self.__check_directory(expected_item_path, item_path)
            else:
                if not os.path.isfile(expected_item_path):
                    self.tc.fail('Item {0} should be a directory but was a file'.format(item_path))
                self.__check_file(expected_item_path, item_path)

    def __check_file(self, expected_file, subject_file):
        with open(expected_file, 'r') as f:
            expected_file_content = f.read()
        with open(subject_file, 'r') as f:
            subject_file_content = f.read()
        if os.path.basename(expected_file) == 'setup.py':
            expected_file_content = expected_file_content.replace('IGNITION_VERSION', ignition.__version__)
        self.tc.assertEqual(subject_file_content, expected_file_content, 'Contents of {0} does not match contents of expected file {1}'.format(subject_file, expected_file))
            

            