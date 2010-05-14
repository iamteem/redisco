import unittest
from containers import SetTestCase, ListTestCase
from models import ModelTestCase
from redisco.connection import connect

def all_tests():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SetTestCase))
    suite.addTest(unittest.makeSuite(ListTestCase))
    suite.addTest(unittest.makeSuite(ModelTestCase))
    return suite


if __name__ == '__main__':
    unittest.main()
