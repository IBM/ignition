import unittest

class TestExample(unittest.TestCase):

    def test_something(self):
        a = 1
        self.assertEqual(a+1, 2)