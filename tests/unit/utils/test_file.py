import unittest
import uuid
import tempfile
import shutil
import os
from ignition.utils.file import DirectoryTree

class TestDirectoryTree(unittest.TestCase):

    def setUp(self):
        self.root_dir = tempfile.mkdtemp()
        ##root/
        ##  Definitions/
        ##      infrastructure/
        ##          tosca.yaml
        ##  lifecycle/
        ##      start.sh
        ##  README.md
        self.readme_file = 'README.md'
        with open(os.path.join(self.root_dir, self.readme_file), 'w') as file:
            pass

        self.lifecycle_dir = 'lifecycle'
        self.lifecycle_start_script_file = 'start.sh'
        os.mkdir(os.path.join(self.root_dir, self.lifecycle_dir))
        with open(os.path.join(self.root_dir, self.lifecycle_dir, self.lifecycle_start_script_file), 'w') as file:
            pass

        self.definitions_dir = 'Definitions'
        self.infrastructure_dir = 'infrastructure'
        self.infrastructure_tosca_file = 'tosca.yaml'
        os.mkdir(os.path.join(self.root_dir, self.definitions_dir))
        os.mkdir(os.path.join(self.root_dir, self.definitions_dir, self.infrastructure_dir))
        with open(os.path.join(self.root_dir, self.definitions_dir, self.infrastructure_dir, self.infrastructure_tosca_file), 'w') as file:
            pass

    def tearDown(self):
        shutil.rmtree(self.root_dir)

    def test_has_directory_returns_true_when_found(self):
        tree = DirectoryTree(self.root_dir)
        self.assertTrue(tree.has_directory(self.lifecycle_dir))

    def test_has_directory_returns_false_when_not_found(self):
        tree = DirectoryTree(self.root_dir)
        self.assertFalse(tree.has_directory('myDirectory'))

    def test_has_directory_returns_false_when_not_a_directory(self):
        tree = DirectoryTree(self.root_dir)
        self.assertFalse(tree.has_directory(self.readme_file))

    def test_has_directory_with_path(self):
        tree = DirectoryTree(self.root_dir)
        self.assertTrue(tree.has_directory(os.path.join(self.definitions_dir, self.infrastructure_dir)))

    def test_get_directory_tree(self):
        tree = DirectoryTree(self.root_dir)
        sub_tree = tree.get_directory_tree(self.lifecycle_dir)
        self.assertIsNotNone(sub_tree)
        self.assertIsInstance(sub_tree, DirectoryTree)
        self.assertEqual(sub_tree.root_path, os.path.join(self.root_dir, self.lifecycle_dir))

    def test_get_directory_tree_throws_error_when_not_found(self):
        tree = DirectoryTree(self.root_dir)
        with self.assertRaises(ValueError) as context:
            tree.get_directory_tree('myDirectory')
        self.assertEqual(str(context.exception), 'No directory at myDirectory found in root path {0}'.format(self.root_dir))

    def test_get_directory_tree_throws_error_when_not_a_directory(self):
        tree = DirectoryTree(self.root_dir)
        with self.assertRaises(ValueError) as context:
            tree.get_directory_tree(self.readme_file)
        self.assertEqual(str(context.exception), '{0} in root path {1} is not a directory'.format(self.readme_file, self.root_dir))

    def test_get_directory_tree_with_path(self):
        tree = DirectoryTree(self.root_dir)
        sub_tree = tree.get_directory_tree(os.path.join(self.definitions_dir, self.infrastructure_dir))
        self.assertIsNotNone(sub_tree)
        self.assertIsInstance(sub_tree, DirectoryTree)
        self.assertEqual(sub_tree.root_path, os.path.join(self.root_dir, self.definitions_dir, self.infrastructure_dir))

    def test_has_file_returns_true_when_found(self):
        tree = DirectoryTree(self.root_dir)
        self.assertTrue(tree.has_file(self.readme_file))

    def test_has_file_returns_false_when_not_found(self):
        tree = DirectoryTree(self.root_dir)
        self.assertFalse(tree.has_file('myFile'))

    def test_has_file_returns_false_when_not_a_file(self):
        tree = DirectoryTree(self.root_dir)
        self.assertFalse(tree.has_file(self.lifecycle_dir))

    def test_has_file_with_path(self):
        tree = DirectoryTree(self.root_dir)
        self.assertTrue(tree.has_file(os.path.join(self.lifecycle_dir, self.lifecycle_start_script_file)))

    def test_get_file_path(self):
        tree = DirectoryTree(self.root_dir)
        path = tree.get_file_path(self.readme_file)
        self.assertEqual(path, os.path.join(self.root_dir, self.readme_file))

    def test_get_file_path_throws_error_when_not_found(self):
        tree = DirectoryTree(self.root_dir)
        with self.assertRaises(ValueError) as context:
            tree.get_file_path('myFile')
        self.assertEqual(str(context.exception), 'No file at myFile found in root path {0}'.format(self.root_dir))

    def test_get_file_path_throws_error_when_not_a_file(self):
        tree = DirectoryTree(self.root_dir)
        with self.assertRaises(ValueError) as context:
            tree.get_file_path(self.lifecycle_dir)
        self.assertEqual(str(context.exception), '{0} in root path {1} is not a file'.format(self.lifecycle_dir, self.root_dir))

    def test_get_file_path_with_path(self):
        tree = DirectoryTree(self.root_dir)
        path = tree.get_file_path(os.path.join(self.definitions_dir, self.infrastructure_dir, self.infrastructure_tosca_file))
        self.assertEqual(path, os.path.join(self.root_dir, self.definitions_dir, self.infrastructure_dir, self.infrastructure_tosca_file))