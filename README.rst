=======
Redisco
=======
A Python object mapping library for Redis

Description
-----------
Redisco allows you to store objects in Redis_.  It is inspired by Ruby library
Ohm_ and its design and code are loosely based on Ohm and the Django ORM.
It is built on top of redis-py_.

Installation
------------
Redisco requires bleeding version of redis-py so get it first. (As of this
writing, commit dd8421273d4b17adfda56e8b753bdf92d4d43fb5 in github works with
redisco 0.1.)

    pip install git+http://github.com/andymccurdy/redis-py.git@master#egg=redis-py

Then, install redisco.

    pip install git+http://github.com/iamteem/redisco.git@master#egg=redisco


Models
------
Example

    >>> from redisco.models import Model, Attribute, DateTimeField
    >>> class Person(Model):
    ...     name = Attribute(required=True)
    ...     created_at = DateTimeField(auto_add=True)
    ...
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


Containers
----------
Redisco has three containers that roughly match Redis's supported data
structures: lists, sets, sorted set. Anything done to the container is
persisted to Redis.

    # Sets

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

    # Lists
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

    # Sorted Sets
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
