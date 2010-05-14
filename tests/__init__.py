import unittest
from containers import SetTestCase, ListTestCase
from redisco.connection import connect

def all_tests():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SetTestCase))
    suite.addTest(unittest.makeSuite(ListTestCase))
    return suite
