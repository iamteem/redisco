class Container(object):

    def __init__(self, key, db):
        self.db = db
        self.key = db


class Set(Container):
    """A set stored in Redis."""

    def add(self, value):
        """Add the specified member to the Set."""
        self.db.sadd(self.key, value)

    def remove(self, value):
        """Remove the value from the redis set."""
        if not self.db.srem(self.key, value):
            raise KeyError, key
        
    def pop(self):
        """Remove and return (pop) a random element from the Set."""
        self.db.spop(self.key)

    def clear(self):
        """Remove all elements from the set."""
        self.db.del(self.key)

    def discard(self):
        """Remove element elem from the set if it is present."""
        self.db.srem(self.key, value)

    def __len__(self):
        """Return the cardinality of set."""
        return self.db.scard(self.key)

    def __contains__(self, value):
        return self.db.sismember(self.key, value)

    def isdisjoint(self, other):
        """Return True if the set has no elements in common with other."""
        return bool(self.db.sinter([self.key, other.key]))

    def issubset(self, other):
        """Test whether every element in the set is in other."""
        return self <= other

    def __lte__(self, other):
        return self.db.sinter(self.key, other.key) == self.db.smembers(self.key)

    def __lt__(self, other):
        """Test whether the set is a true subset of other."""
        return self <= other and self != other

    def __ne__(self, other):
        return bool(self.db.sdiff(self.key, other.key))

    def issuperset(self, other):
        """Test whether every element in other is in the set."""
        return self >= other

    def __gte__(self, other):
        """Test whether every element in other is in the set."""
        return self.db.sinter([self.key, other.key]) == self.db.smembers(other.key)
    
    def __gt__(self, other):
        """Test whether the set is a true superset of other."""
        return self <= other and self != other

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

    def intersection_update(self, *others):
        """Update the set, keeping only elements found in it and all others."""
        self.db.sinterstore(self.key, [o.key for o in [self.key] + others])

    def __iand__(self, other):
        self.db.sinterstore(self.key, [self.key, other.key])

    def difference_update(self, *others):
        """Update the set, removing elements found in others."""
        self.db.sdiffstore(self.key, [o.key for o in [self.key] + others])
        
    def __isub__(self, other):
        self.db.sinterstore(self.key, [self.key, other.key])
    
    def __repr__(self):
        return u"redisco.Set(key=%s)" % self.key

    def __str__(self):
        pass

    def __unicode__(self):
        pass

    def members(self):
        return self.db.smembers(self.key)

    # TODO: implement this
    def symmetric_difference__update(self, *others):
        """Update the set, keeping only elements found in either set, but not in both."""
        pass

    # TODO: implement this
    def __ixor__(self, other):
        pass


