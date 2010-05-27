import collections
from functools import partial
from connection import _get_client

class Container(object):
    """Create a container object saved in Redis.

    Arguments:
        key -- the Redis key this container is stored at
        db  -- the Redis client object. Default: None

    When ``db`` is not set, the gets the default connection from
    ``redisco.connection`` module.
    """

    def __init__(self, key, db=None):
        if db is None:
            self.db = _get_client()
        else:
            self.db = db
        self.key = key

    def clear(self):
        """Remove container from Redis database."""
        del self.db[self.key]

    def __getattribute__(self, att):
        if att in object.__getattribute__(self, 'DELEGATEABLE_METHODS'):
            return partial(getattr(object.__getattribute__(self, 'db'), att), self.key)
        else:
            return object.__getattribute__(self, att)

    DELEGATEABLE_METHODS = ()


class Set(Container):
    """A set stored in Redis."""

    def add(self, value):
        """Add the specified member to the Set."""
        self.db.sadd(self.key, value)

    def remove(self, value):
        """Remove the value from the redis set."""
        if not self.db.srem(self.key, value):
            raise KeyError, value
        
    def pop(self):
        """Remove and return (pop) a random element from the Set."""
        return self.db.spop(self.key)

    def discard(self, value):
        """Remove element elem from the set if it is present."""
        self.db.srem(self.key, value)

    def __len__(self):
        """Return the cardinality of set."""
        return self.db.scard(self.key)

    # TODO: Note, the elem argument to the __contains__(), remove(),
    #       and discard() methods may be a set
    def __contains__(self, value):
        return self.db.sismember(self.key, value)

    def isdisjoint(self, other):
        """Return True if the set has no elements in common with other."""
        return not bool(self.db.sinter([self.key, other.key]))

    def issubset(self, other):
        """Test whether every element in the set is in other."""
        return self <= other

    def __le__(self, other):
        return self.db.sinter([self.key, other.key]) == self.all()

    def __lt__(self, other):
        """Test whether the set is a true subset of other."""
        return self <= other and self != other

    def __eq__(self, other):
        if other.key == self.key:
            return True
        slen, olen = len(self), len(other)
        if olen == slen:
            return self.members == other.members
        else:
            return False

    def issuperset(self, other):
        """Test whether every element in other is in the set."""
        return self >= other

    def __ge__(self, other):
        """Test whether every element in other is in the set."""
        return self.db.sinter([self.key, other.key]) == other.all()
    
    def __gt__(self, other):
        """Test whether the set is a true superset of other."""
        return self >= other and self != other


    # SET Operations
    def union(self, key, *others):
        """Return a new set with elements from the set and all others."""
        if not isinstance(key, str):
            raise ValueError("String expected.")
        self.db.sunionstore(key, [self.key] + [o.key for o in others])
        return Set(key)

    def intersection(self, key, *others):
        """Return a new set with elements common to the set and all others."""
        if not isinstance(key, str):
            raise ValueError("String expected.")
        self.db.sinterstore(key, [self.key] + [o.key for o in others])
        return Set(key)

    def difference(self, key, *others):
        """Return a new set with elements in the set that are not in the others."""
        if not isinstance(key, str):
            raise ValueError("String expected.")
        self.db.sdiffstore(key, [self.key] + [o.key for o in others])
        return Set(key)

    def update(self, *others):
        """Update the set, adding elements from all others."""
        self.db.sunionstore(self.key, [self.key] + [o.key for o in others])

    def __ior__(self, other):
        self.db.sunionstore(self.key, [self.key, other.key])
        return self

    def intersection_update(self, *others):
        """Update the set, keeping only elements found in it and all others."""
        self.db.sinterstore(self.key, [o.key for o in [self.key] + others])

    def __iand__(self, other):
        self.db.sinterstore(self.key, [self.key, other.key])
        return self

    def difference_update(self, *others):
        """Update the set, removing elements found in others."""
        self.db.sdiffstore(self.key, [o.key for o in [self.key] + others])
        
    def __isub__(self, other):
        self.db.sdiffstore(self.key, [self.key, other.key])
        return self
    
    def __repr__(self):
        return u"<redisco.containers.Set(key=%s)>" % self.key

    def __str__(self):
        return str(self.__repr__())

    def __unicode__(self):
        return self.__str__()

    def all(self):
        return self.db.smembers(self.key)
    members = property(all)

    def copy(self, key):
        """Copy the set to another key and return the new Set.

        WARNING: If the key exists, it overwrites it.
        """
        copy = Set(key=key, db=self.db)
        copy.clear()
        copy |= self
        return copy

    def __iter__(self):
        m = self.members
        for e in m:
            yield e

    DELEGATEABLE_METHODS = ('sadd', 'srem', 'spop', 'smembers',
            'scard', 'sismember', 'srandmember')


class List(Container):

    def all(self):
        """Returns all items in the list."""
        return self.db.lrange(self.key, 0, -1)
    members = property(all)

    def __len__(self):
        return self.db.llen(self.key)

    def __getitem__(self, index):
        if isinstance(index, int):
            return self.db.lindex(self.key, index)
        elif isinstance(index, slice):
            indices = index.indices(len(self))
            return self.db.lrange(self.key, indices[0], indices[1])
        else:
            raise TypeError

    def __setitem__(self, index, value):
        self.db.lset(self.key, index, value)

    def append(self, value):
        """Append the value to the list."""
        self.db.rpush(self.key, value)
    push = append

    def extend(self, iterable):
        """Extend list by appending elements from the iterable."""
        map(lambda i: self.db.rpush(self.key, i), iterable)

    def count(self, value):
        """Return number of occurrences of value."""
        return self.members.count(value)

    def index(self, value):
        """Return first index of value."""
        return self.all().index(value)

    def pop(self):
        """Remove and return the last item"""
        return self.db.rpop(self.key)

    def shift(self):
        """Remove and return the first item."""
        return self.db.lpop(self.key)

    def unshift(self, value):
        """Add an element at the beginning of the list."""
        self.db.lpush(self.key, value)

    def remove(self, value, num=1):
        """Remove first occurrence of value."""
        self.db.lrem(self.key, value, num)

    def reverse(self):
        """Reverse in place."""
        r = self[:]
        r.reverse()
        self.clear()
        self.extend(r)

    def copy(self, key):
        """Copy the list to a new list.

        WARNING: If key exists, it clears it before copying.
        """
        copy = List(key, self.db)
        copy.clear()
        copy.extend(self)
        return copy

    def trim(self, start, end):
        """Trim the list from start to end."""
        self.db.ltrim(self.key, start, end)

    def __iter__(self):
        m = self.members
        for e in range(len(m)):
            yield m[e]

    DELEGATEABLE_METHODS = ('lrange', 'lpush', 'rpush', 'llen',
            'ltrim', 'lindex', 'lset', 'lpop', 'lrem', 'rpop',)

class SortedSet(Container):

    def add(self, member, score):
        self.db.zadd(self.key, member, score)

    def remove(self, member):
        self.db.zrem(self.key, member)

    def incr_by(self, member, increment):
        self.db.zincrby(self.key, member, increment)

    def rank(self, member):
        """Return the rank (the index) of the element."""
        return self.db.zrank(self.key, member)

    def revrank(self, member):
        """Return the rank of the member in reverse order."""
        return self.db.zrevrank(self.key, member)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return self.db.zrange(self.key, index.start, index.stop)
        else:
            return self.db.zrange(self.key, index, index)[0]

    def score(self, member):
        return self.db.zscore(self.key, member)

    def __len__(self):
        return self.db.zcard(self.key)

    def __contains__(self, val):
        return self.db.zscore(self.key, val) is not None

    @property
    def members(self):
        return self.db.zrange(self.key, 0, -1)

    def __iter__(self):
        return self.members.__iter__()

    @property
    def _min_score(self):
        return self.db.zscore(self.key, self.__getitem__(0))

    @property
    def _max_score(self):
        return self.db.zscore(self.key, self.__getitem__(-1))

    def lt(self, v, limit=None, offset=None):
        if limit is not None and offset is None:
            offset = 0
        return self.db.zrangebyscore(self.key, self._min_score, "(%f" % v,
                start=offset, num=limit)

    def le(self, v, limit=None, offset=None):
        if limit is not None and offset is None:
            offset = 0
        return self.db.zrangebyscore(self.key, self._min_score, v,
                start=offset, num=limit)

    def gt(self, v, limit=None, offset=None):
        if limit is not None and offset is None:
            offset = 0
        return self.db.zrangebyscore(self.key, "(%f" % v, self._max_score,
                start=offset, num=limit)

    def ge(self, v, limit=None, offset=None):
        if limit is not None and offset is None:
            offset = 0
        return self.db.zrangebyscore(self.key, "(%f" % v, self._max_score,
                start=offset, num=limit)

    def between(self, min, max, limit=None, offset=None):
        if limit is not None and offset is None:
            offset = 0
        return self.db.zrangebyscore(self.key, min, max,
                start=offset, num=limit)

    def eq(self, value):
        return self.db.zrangebyscore(self.key, value, value)

    DELEGATEABLE_METHODS = ('zadd', 'zrem', 'zincrby', 'zrank',
            'zrevrank', 'zrange', 'zrangebyscore', 'zcard',
            'zscore', 'zremrangebyrank', 'zremrangebyscore')


class NonPersistentList(object):
    def __init__(self, l):
        self._list = l

    @property
    def members(self):
        return self._list

    def __iter__(self):
        return iter(self.members)

    def __len__(self):
        return len(self._list)


class Hash(Container, collections.MutableMapping):
    """Dict storage."""

    def __getitem__(self, att):
        return self.hget(att)

    def __setitem__(self, att, val):
        self.hset(att, val)

    def __delitem__(self, att):
        self.hdel(att)

    def __len__(self):
        return self.hlen()

    def __iter__(self):
        return self.hgetall().__iter__()

    def __contains__(self, att):
        return self.hexists(att)

    def __repr__(self):
        return "<%s '%s' %s>" % (self.__class__.__name__, self.key, self.hgetall())

    def keys(self):
        return self.hkeys()

    def values(self):
        return self.hvals()

    @property
    def dict(self):
        return self.hgetall()


    DELEGATEABLE_METHODS = ('hlen', 'hset', 'hdel', 'hkeys',
            'hgetall', 'hvals', 'hget', 'hexists')
