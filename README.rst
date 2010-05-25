=======
Redisco
=======
Python Containers and Simple Models for Redis

Description
-----------
Redisco allows you to store objects in Redis_. It is inspired by Ruby library
Ohm_ and its design and code are loosely based on Ohm and the Django ORM.
It is built on top of redis-py_. It includes container classes that allow
easier access to Redis sets, lists, and sorted sets.

Installation
------------
Redisco requires latest version of redis-py so get it first.

    pip install git+http://github.com/andymccurdy/redis-py.git@master#egg=redis-py

Then install redisco.

    pip install git+http://github.com/iamteem/redisco.git@master#egg=redisco


Models
------
Example

::

    from redisco import models
    class Person(models.Model):::
        name = models.Attribute(required=True)
        created_at = models.DateTimeField(auto_add=True)
        fave_colors = models.ListField(str)

    >>> person = Person(name="Conchita")
    >>> person.is_valid()
    True
    >>> person.save()
    True
    >>> conchita = Person.objects.filter(name='Conchita')[0]
    >>> conchita.name
    'Conchita'
    >>> conchita.created_at
    datetime.datetime(2010, 5, 24, 16, 0, 31, 954704)


Model Attributes
----------------

Here are the model attributes and value types they can store.

:Attribute:       unicode
:IntegerField:    int
:DateTimeField:   DateTime
:DateField:       Date
:FloatField:      float
:BooleanField:    bool
:ReferenceField:  reference to another model
:ListField:       list of unicode, int, float, models

Options for creating attributes include required, default, and validator.
DateField and DateTimeField have the auto_now_add and auto_now.

Queries
-------

Queries are executed using a manager, accessed via the objects class
attribute.

Examples

::

    Person.objects.all()
    Person.objects.filter(name='Conchita')
    Person.objects.filter(name='Conchita').first()
    Person.objects.all().order('name')
    Person.objects.filter(fave_colors='Red')

Ranged Queries
--------------

Redisco has a limited support for queries involving ranges -- it can only
filter fields that are numeric, i.e. DateField, DateTimeField, IntegerField,
and FloatField. The zfilter method of the manager is used for these queries.

::

    Person.objects.zfilter(created_at__lt=datetime(2010, 4, 20, 5, 2, 0))
    Person.objects.zfilter(created_at__gte=datetime(2010, 4, 20, 5, 2, 0))
    Person.objects.zfilter(created_at__in=(datetime(2010, 4, 20, 5, 2, 0), datetime(2010, 5, 1)))


Containers
----------
Redisco has three containers that roughly match Redis's supported data
structures: lists, sets, sorted set. Anything done to the container is
persisted to Redis.

Sets
----
    >>> import redis
    >>> from redisco.containers import Set
    >>> s = Set('myset')
    >>> s.add('apple')
    >>> s.add('orange')
    >>> s.members
    set(['orange', 'apple'])
    >>> t = Set('nset')
    >>> t.add('kiwi')
    >>> t.add('guava')
    >>> t.members
    set(['kiwi', 'guava'])
    >>> s.update(t)
    >>> s.members
    set(['kiwi', 'orange', 'guava', 'apple'])

Lists
-----

    >>> import redis
    >>> from redisco.containers import List
    >>> l = List('alpha')
    >>> l.append('a')
    >>> l.append('b')
    >>> l.append('c')
    >>> 'a' in l
    True
    >>> 'd' in l
    False
    >>> len(l)
    3
    >>> l.index('b')
    1
    >>> l.members
    ['a', 'b', 'c']


Sorted Sets
-----------

    >>> zset = SortedSet('zset')
    >>> zset.members
    ['d', 'a', 'b', 'c']
    >>> 'e' in zset
    False
    >>> 'a' in zset
    True
    >>> zset.rank('d')
    0
    >>> zset.rank('b')
    2
    >>> zset[1]
    'a'
    >>> zset.add('f', 200)
    >>> zset.members
    ['d', 'a', 'b', 'c', 'f']
    >>> zset.add('d', 99)
    >>> zset.members
    ['a', 'b', 'c', 'd', 'f']



.. _Redis: http://code.google.com/p/redis/
.. _Ohm: http://github.com/soveran/ohm/
.. _redis-py: http://github.com/andymccurdy/redis-py/
