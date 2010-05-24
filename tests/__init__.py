import unittest
from redisco.connection import connect
connect(host='localhost', port=6380, db=10)
from containers import SetTestCase, ListTestCase, SortedSetTestCase
from models import (ModelTestCase, DateFieldTestCase, FloatFieldTestCase,
        BooleanFieldTestCase)

def all_tests():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SetTestCase))
    suite.addTest(unittest.makeSuite(ListTestCase))
    suite.addTest(unittest.makeSuite(SortedSetTestCase))
    suite.addTest(unittest.makeSuite(ModelTestCase))
    suite.addTest(unittest.makeSuite(DateFieldTestCase))
    suite.addTest(unittest.makeSuite(FloatFieldTestCase))
    suite.addTest(unittest.makeSuite(BooleanFieldTestCase))
    return suite
