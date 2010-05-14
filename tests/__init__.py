import unittest
from containers import SetTestCase

def all_tests():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SetTestCase))
    return suite
