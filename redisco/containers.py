class Container(object):

    def __init__(self, key, db):
        self.db = db
        self.key = key

    def clear(self):
        """Remove container from Redis database."""
        del self.db[self.key]


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
            return not bool(self - other)
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

    def union(self, *others):
        """Return a new set with elements from the set and all others."""
        return self.db.sunion([self.key] + [o.key for o in others])

    def __or__(self, other):
        return self.db.sunion([self.key, other.key])

    def intersection(self, *others):
        """Return a new set with elements common to the set and all others."""
        return self.db.sinter([self.key] + [o.key for o in others])

    def __and__(self, other):
        return self.db.sinter([self.key, other.key])

    def difference(self, *others):
        """Return a new set with elements in the set that are not in the others."""
        return self.db.sdiff([self.key] + [o.key for o in others])

    def __sub__(self, other):
        return self.db.sdiff([self.key, other.key])

    def symmetric_difference(self, other):
        """Return a new set with elements in either the set or other but not both."""
        return self ^ other
    
    def __xor__(self, other):
        """Return a new set with elements in either the set or other but not both."""
        return self.db.sunion([self.key, other.key]) - self.db.sinter([self.key, other.key])

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
        pass

    def __unicode__(self):
        pass

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

    # TODO: implement this
    def symmetric_difference_update(self, *others):
        """Update the set, keeping only elements found in either set, but not in both."""
        pass

    # TODO: implement this
    def __ixor__(self, other):
        pass


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
