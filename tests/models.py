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
        self.assertEqual('Person', Person.ckey)

    def test_attributes(self):
        person = Person(first_name="Granny", last_name="Goose")
        naruto = Ninja(first_name="Naruto", last_name="Uzumaki",
                weapon="Rasengan")

        self.assertEqual("Naruto", naruto.first_name)
        self.assertEqual("Uzumaki", naruto.last_name)
        self.assertEqual("Rasengan", naruto.weapon)
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

    def test_inheritance_save(self):
        person = Person(first_name="Granny", last_name="Goose")
        naruto = Ninja(first_name="Naruto", last_name="Uzumaki",
                weapon="Rasengan")

        self.assertEqual(set(['first_name', 'last_name', 'weapon']),
                set(Ninja.__dict__['__attributes']))

        person.save()
        naruto.save()

        self.assertEqual(1, len(Ninja.objects.all()))
        self.assertEqual(1, len(Person.objects.all()))

        n = Ninja.objects[1]
        self.assertEqual("Naruto", n.first_name)
        self.assertEqual("Uzumaki", n.last_name)
        self.assertEqual("Rasengan", n.weapon)

