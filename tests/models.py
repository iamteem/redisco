import base64
import redis
import unittest
from redisco import models

class Person(models.Model):
    first_name = models.Attribute()
    last_name = models.Attribute()

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

    def test_getitem(self):
        person1 = Person(first_name="Granny", last_name="Goose")
        person1.save()
        person2 = Person(first_name="Jejomar", last_name="Binay")
        person2.save()

        p1 = Person.objects.get_by_id(1)
        p2 = Person.objects.get_by_id(2)

        self.assertEqual('Jejomar', p2.first_name)
        self.assertEqual('Binay', p2.last_name)

        self.assertEqual('Granny', p1.first_name)
        self.assertEqual('Goose', p1.last_name)

    def test_manager_create(self):
        person = Person.objects.create(first_name="Granny", last_name="Goose")

        p1 = Person.objects.get_by_id(1)
        self.assertEqual('Granny', p1.first_name)
        self.assertEqual('Goose', p1.last_name)

    def test_indices(self):
        person = Person.objects.create(first_name="Granny", last_name="Goose")
        db = person.db
        key = person.key()
        ckey = Person._key

        index = 'Person:first_name:%s' % base64.b64encode("Granny").replace("\n", "")
        self.assertTrue(index in db.smembers(key['_indices']))
        self.assertTrue("1" in db.smembers(index))

    def test_find(self):
        Person.objects.create(first_name="Granny", last_name="Goose")
        Person.objects.create(first_name="Clark", last_name="Kent")
        Person.objects.create(first_name="Granny", last_name="Mommy")
        Person.objects.create(first_name="Granny", last_name="Kent")
        persons = Person.objects.filter(first_name="Granny")

        self.assertEqual('1', persons[0].id)
        self.assertEqual(3, len(persons))

        persons = Person.objects.filter(first_name="Clark")
        self.assertEqual(1, len(persons))

        # by index
        persons = Person.objects.filter(full_name="Granny Mommy")
        self.assertEqual(1, len(persons))
        self.assertEqual("Granny Mommy", persons[0].full_name())

    
    def test_iter(self):
        Person.objects.create(first_name="Granny", last_name="Goose")
        Person.objects.create(first_name="Clark", last_name="Kent")
        Person.objects.create(first_name="Granny", last_name="Mommy")
        Person.objects.create(first_name="Granny", last_name="Kent")

        for person in Person.objects.all():
            self.assertTrue(person.full_name() in ("Granny Goose",
                "Clark Kent", "Granny Mommy", "Granny Kent",))

    def test_sort(self):
        Person.objects.create(first_name="Zeddicus", last_name="Zorander")
        Person.objects.create(first_name="Richard", last_name="Cypher")
        Person.objects.create(first_name="Richard", last_name="Rahl")
        Person.objects.create(first_name="Kahlan", last_name="Amnell")

        res = Person.objects.order('first_name').all()
        self.assertEqual("Kahlan", res[0].first_name)
        self.assertEqual("Richard", res[1].first_name)
        self.assertEqual("Richard", res[2].first_name)
        self.assertEqual("Zeddicus Zorander", res[3].full_name())

        res = Person.objects.order('-full_name').all()
        self.assertEqual("Zeddicus Zorander", res[0].full_name())
        self.assertEqual("Richard Rahl", res[1].full_name())
        self.assertEqual("Richard Cypher", res[2].full_name())
        self.assertEqual("Kahlan Amnell", res[3].full_name())

    def test_all(self):
        person1 = Person(first_name="Granny", last_name="Goose")
        person1.save()
        person2 = Person(first_name="Jejomar", last_name="Binay")
        person2.save()

        all = Person.objects.all()
        self.assertEqual(set([person1, person2]), set(all.members))

    def test_limit(self):
        Person.objects.create(first_name="Zeddicus", last_name="Zorander")
        Person.objects.create(first_name="Richard", last_name="Cypher")
        Person.objects.create(first_name="Richard", last_name="Rahl")
        Person.objects.create(first_name="Kahlan", last_name="Amnell")

        res = Person.objects.order('first_name').all().limit(3)
        self.assertEqual(3, len(res))
        self.assertEqual("Kahlan", res[0].first_name)
        self.assertEqual("Richard", res[1].first_name)
        self.assertEqual("Richard", res[2].first_name)

        res = Person.objects.order('first_name').limit(3, offset=1)
        self.assertEqual(3, len(res))
        self.assertEqual("Richard", res[0].first_name)
        self.assertEqual("Richard", res[1].first_name)
        self.assertEqual("Zeddicus", res[2].first_name)

    def test_integer_field(self):
        class Character(models.Model):
            n = models.IntegerField()
            m = models.Attribute()

        Character.objects.create(n=1998, m="A")
        Character.objects.create(n=3100, m="b")
        Character.objects.create(n=1, m="C")

        chars = Character.objects.all()
        self.assertEqual(3, len(chars))
        self.assertEqual(1998, chars[0].n)
        self.assertEqual("A", chars[0].m)

    def test_list_field(self):
        class Cake(models.Model):
            name = models.Attribute()
            ingredients = models.ListField(str)
            sizes = models.ListField(int)

        Cake.objects.create(name="StrCake",
                            ingredients=['strawberry', 'sugar', 'dough'])
        Cake.objects.create(name="Normal Cake",
                            ingredients=['sugar', 'dough'])
        Cake.objects.create(name="No Sugar Cake",
                            ingredients=['dough'])
        cake = Cake.objects.all()[0]
        self.assertEqual(['strawberry', 'sugar', 'dough'],
                cake.ingredients)
        with_sugar = Cake.objects.filter(ingredients='sugar')
        self.assertTrue(2, len(with_sugar))

    def test_reference_field(self):
        return
        class Word(models.Model):
            pass

        class Character(models.Model):
            n = models.IntegerField()
            m = models.Attribute()
            word = models.ReferenceField(Word)

        word = Word.objects.create()
        a = Character.objects.create(n=32, m='a', word=word)
        b = Character.objects.create(n=33, m='b', word=word)
        c = Character.objects.create(n=34, m='c', word=word)

