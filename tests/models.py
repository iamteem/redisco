import redis
import unittest
from redisco import models

class Person(models.Model):
    first_name = models.Attribute(index=True)
    last_name = models.Attribute(index=True)
    full_name = models.Index()

    def full_name(self):
        return "%s %s" % (self.first_name, self.last_name,)


class Ninja(Person):
    weapon = models.Attribute()


class ModelTestCase(unittest.TestCase):
    def setUp(self):
        self.client = redis.Redis(host='localhost', port=6380, db=10)
        self.client.flushdb()

    def tearDown(self):
        self.client.flushdb()

    def test_key(self):
        self.assertEqual('Person', Person.key)

    def test_attributes(self):
        person = Person(first_name="Granny", last_name="Goose")
        self.assertEqual("Granny", person.first_name)
        self.assertEqual("Goose", person.last_name)

        naruto = Ninja(first_name="Naruto", last_name="Uzumaki",
                weapon="Rasengan")

        self.assertEqual("Naruto", naruto.first_name)
        self.assertEqual("Uzumaki", naruto.last_name)
        self.assertEqual("Rasengan", naruto.weapon)

    def test_save(self):
        person1 = Person(first_name="Granny", last_name="Goose")
        person1.save()
        person2 = Person(first_name="Jejomar", last_name="Binay")
        person2.save()

        self.assertEqual('1', person1.id)
        self.assertEqual('2', person2.id)
