from connection import _get_client
from containers import Set
from key import Key
from utils import DictWithDefault

class Attribute(object):
    def __init__(self, index=False):
        self.index = index

    def __set__(self, instance, value):
        instance.write_local(self.name, value)

    def __get__(self, instance, owner):
        return instance.read_local(self.name)


class Index(object):
    pass


class Attributes(object):

    def __get__(self, instance, owner):
        if not hasattr(instance, '_attr_values'):
            def default_read_remote(h, k):
                h.setdefault(k, instance.read_remote(k))
            instance._attr_values = DictWithDefault(default_read_remote)
        return instance._attr_values


class ModelBase(type):
    def __new__(cls, name, bases, attrs):

        __attributes = []
        for k, v in attrs.iteritems():
            if isinstance(v, Attribute):
                v.name = k
                __attributes.append(k)
        attrs['__attributes'] = __attributes
        key = Key(name)
        attrs['key'] = key
        attrs['all'] = Set(key['all'])
        return type.__new__(cls, name, bases, attrs)


class Model(object):
    _db = None
    _attributes = Attributes()
    __metaclass__ = ModelBase

    def __init__(self, **kwargs):
        if self.__class__._db is None:
            self.__class__._db = _get_client()
        self.update_attributes(**kwargs)

    def update_attributes(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def read_local(self, key):
        return self._attributes[key]

    def read_remote(self, key):
        if not self.is_new:
            return self.db.hget(self.key, key)

    def write_local(self, key, value):
        self._attributes[key] = value

    def write(self):
        if not self.attributes:
            for att in self.attributes:
                value = getattr(self, att)
                if value:
                    self.db.hset(self.key, att, value)
                else:
                    self.db.hdel(self.key, att)

    def initialize_id(self):
        self.id = str(self.db.incr(self.__class__.key['id']))

    def create_model_membership(self):
        self.__class__.all.add(self.id)

    def save(self):
        if not self.is_new:
            return self.create()

        self.write()
        self.update_indices()
        return self

    def create(self):
        self.initialize_id()

        self.create_model_membership()
        self.write()
        self.update_indices()
        return self


    def update_indices(self):
        self.delete_from_indices()
        self.add_to_indices()

    def delete_from_indices(self):
        pass

    def add_to_indices(self):
        pass

    @property
    def attributes(self):
        return self.__class__.__dict__['__attributes']

    @property
    def key(self):
        if not self.is_new:
            return self.__class__.key[self.id]

    @property
    def is_new(self):
        return hasattr(self, 'id')

    @property
    def db(self):
        return self.__class__._db


class Manager(object):
    pass
