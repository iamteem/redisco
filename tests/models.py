import redis
import unittest
from redisco import models

class Person(models.Model):
    first_name = models.Attribute(indexed=True)
    last_name = models.Attribute(indexed=True)

    def full_name(self):
        return "%s %s" % (self.first_name, self.last_name,)

    class Meta:
        indices = ['full_name']


class ModelTestCase(unittest.TestCase):
    def setUp(self):
        self.client = redis.Redis(host='localhost', port=6380, db=10)
        self.client.flushdb()

    def tearDown(self):
        self.client.flushdb()

    def test_key(self):
        self.assertEqual('Person', Person._key)


    def test_is_new(self):
        p = Person(first_name="Darken", last_name="Rahl")
        self.assertTrue(p.is_new())

    def test_attributes(self):
        person = Person(first_name="Granny", last_name="Goose")
        self.assertEqual("Granny", person.first_name)
        self.assertEqual("Goose", person.last_name)

    def test_save(self):
        person1 = Person(first_name="Granny", last_name="Goose")
        person1.save()
        person2 = Person(first_name="Jejomar", last_name="Binay")
        person2.save()

        self.assertEqual('1', person1.id)
        self.assertEqual('2', person2.id)

    def test_find(self):
        person1 = Person(first_name="Granny", last_name="Goose")
        person1.save()
        person2 = Person(first_name="Jejomar", last_name="Binay")
        person2.save()

        p1 = Person.objects['1']
        p2 = Person.objects[2]

        self.assertEqual('Jejomar', p2.first_name)
        self.assertEqual('Binay', p2.last_name)

        self.assertEqual('Granny', p1.first_name)
        self.assertEqual('Goose', p1.last_name)

    def test_all(self):
        person1 = Person(first_name="Granny", last_name="Goose")
        person1.save()
        person2 = Person(first_name="Jejomar", last_name="Binay")
        person2.save()

        all = Person.objects.all()
        self.assertEqual(set([person1, person2]), all.members)

