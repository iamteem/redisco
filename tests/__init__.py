import unittest
from containers import TestSet

def all_tests():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSet))
    return suite
