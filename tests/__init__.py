import unittest
from redisco.connection import connect
connect(host='localhost', port=6380, db=10)
from containers import SetTestCase, ListTestCase, SortedSetTestCase
from models import ModelTestCase

