from connection import _get_client
from containers import Set
from key import Key
from utils import DictWithDefault


class MissingID(Exception):
    pass

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


class ModelSet(Set):

    def __init__(self, model, key=None, db=None):
        super(ModelSet, self).__init__(key or model.ckey['all'], db)
        self.model = model

    @property
    def members(self):
        ids = super(ModelSet, self).members
        return set(map(lambda id: self.model(id=id), ids))


class Manager(object):

    def __getitem__(self, index):
        if self.exists(index):
            return self.model(id=index)

    def __call__(self, model):
        self.model = model
        return self

    def exists(self, index):
        return str(index) in self.all()

    def all(self):
        return ModelSet(self.model)

class ManagerDescriptor(object):

    def __init__(self):
        self.manager = Manager()

    def __get__(self, instance, owner):
        return self.manager(owner)

class ModelBase(type):
    def __new__(cls, name, bases, attrs):

        # get the inherited stuff from the bases
        __attributes, managers = [], []
        for base in bases:
            for k, v in base.__dict__.items():
                if isinstance(v, Attribute):
                    v.name = k
                    __attributes.append(k)

        # get the attributes
        for k, v in attrs.iteritems():
            if isinstance(v, Attribute):
                v.name = k
                __attributes.append(k)
        if not attrs.has_key('__attributes'):
            attrs['__attributes'] = __attributes
        else:
            attrs['__attributes'].extend(__attributes)

        key = Key(name)
        attrs['ckey'] = key
        attrs['_db'] = None
        attrs['_attributes'] = Attributes()
        attrs['objects'] = ManagerDescriptor()
        return type.__new__(cls, name, bases, attrs)


class Model(object):
    __metaclass__ = ModelBase

    def __init__(self, **kwargs):
        if self.__class__._db is None:
            self.__class__._db = _get_client()

        if 'id' in kwargs:
            self.id = kwargs['id']
            del kwargs['id']
        else:
            self.id = None
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
        if self.attributes:
            for att in self.attributes:
                value = getattr(self, att)
                if value:
                    self.db.hset(self.key, att, value)
                else:
                    self.db.hdel(self.key, att)

    def initialize_id(self):
        self.id = str(self.db.incr(self.ckey['id']))

    def create_model_membership(self):
        self.__class__.objects.all().add(self.id)

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
            return self.__class__.ckey[self.id]

    @property
    def is_new(self):
        return not hasattr(self, '_id')

    @property
    def db(self):
        return self.__class__._db

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    def __eq__(self, other):
        return type(self) == type(other) and self.key == other.key

    def __hash__(self):
        return hash(self.key)

