import unittest
from redisco.connection import connect
connect(host='localhost', port=6380, db=10)
from containers import SetTestCase, ListTestCase, SortedSetTestCase
from models import ModelTestCase

def all_tests():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SetTestCase))
    suite.addTest(unittest.makeSuite(ListTestCase))
    suite.addTest(unittest.makeSuite(SortedSetTestCase))
    suite.addTest(unittest.makeSuite(ModelTestCase))
    return suite
