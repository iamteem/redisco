import base64
from connection import _get_client
from containers import Set, List
from key import Key
from utils import DictWithDefault


# Managers

class ManagerDescriptor(object):
    def __init__(self, manager):
        self.manager = manager

    def __get__(self, instance, owner):
        if instance != None:
            raise AttributeError
        return self.manager

class Manager(object):
    def __init__(self, model_class):
        self.model_class = model_class

    def get_model_set(self):
        return ModelSet(self.model_class)

    def all(self):
        return self.get_model_set()

    def __getitem__(self, idx):
        return self.get_model_set()[idx]

    def create(self, **kwargs):
        return self.get_model_set().create(**kwargs)

    def filter(self, **kwargs):
        return self.get_model_set().filter(**kwargs)

    def get_by_id(self, id):
        return self.get_model_set().get_by_id(id)

    def order(self, field):
        return self.get_model_set().order(field)

# Model Set
class ModelSet(Set):
    def __init__(self, model_class):
        self.model_class = model_class
        self.db = model_class._db
        self.key = model_class._key['all']
        self._filters = {}
        self._ordering = []

    #################
    # MAGIC METHODS #
    #################

    def __getitem__(self, index):
        l = list(self.set)
        try:
            return self._get_item_with_id(l[int(index)])
        except IndexError:
            return None

    def __repr__(self):
        return self.members

    def __str__(self):
        return "<ModelSet %s>" % self.model_class.__name__

    def __reversed__(self):
        pass

    def __iter__(self):
        for m in self.members:
            yield m

    def __repr__(self):
        pass

    def __len__(self):
        return len(self.set)

    ##########################################
    # METHODS THAT RETURN A SET OF INSTANCES #
    ##########################################

    @property
    def set(self):
        self.db.type(self.key)
        s = Set(self.key)
        if self._filters:
            indices = []
            for k, v in self._filters.iteritems():
                index = self._build_key_from_filter_item(k, v)
                if k not in self.model_class._indices:
                    raise AttributeNotIndexed(
                            "Attribute %s is not indexed in %s class." %
                            (k, self.model_class.__name__))
                indices.append(index)
            new_set_key = "~%s" % ("+".join([self.key] + indices),)
            s.intersection(new_set_key, *[Set(n) for n in indices])
            s = Set(new_set_key)
        if self._ordering:
            old_set_key = s.key
            for ordering in self._ordering:
                if ordering.startswith('-'):
                    desc = True
                    ordering = ordering.lstrip('-')
                else:
                    desc = False
                new_set_key = "%s#%s" % (old_set_key, ordering)
                by = "%s->%s" % (self.model_class._key['*'], ordering)
                self.db.sort(old_set_key,
                             by=by,
                             store=new_set_key,
                             alpha=True,
                             desc=desc)
                s = List(new_set_key)
        return s

    @property
    def members(self):
        return map(lambda id: self._get_item_with_id(id), self.set.members)

    def get_by_id(self, id):
        return self._get_item_with_id(id)


    #####################################
    # METHODS THAT MODIFY THE MODEL SET #
    #####################################

    def filter(self, **kwargs):
        clone = self._clone()
        if not clone._filters:
            clone._filters = {}
        clone._filters.update(kwargs)
        return clone

    # this should only be called once
    def order(self, field):
        clone = self._clone()
        if not clone._ordering:
            clone._ordering = []
        clone._ordering.append(field)
        return clone

    def exclude(self, **kwargs):
        pass

    def count(self):
        pass

    def create(self, **kwargs):
        instance = self.model_class(**kwargs)
        instance.save()
        return instance

    def get(self, **kwargs):
        pass

    def exists(self):
        pass

    def all(self):
        return self._clone()

    ###################
    # PRIVATE METHODS #
    ###################

    def _get_item_with_id(self, id):
        key = self.model_class._key[id]
        if self.db.exists(key):
            kwargs = self.db.hgetall(key)
            instance = self.model_class(**kwargs)
            instance._id = str(id)
            return instance
        else:
            return None

    def _build_key_from_filter_item(self, index, value):
        return self.model_class._key[index][_encode_key(value)]

    def _clone(self):
        klass = self.__class__
        c = klass(self.model_class)
        if self._filters:
            c._filters = self._filters
        if self._ordering:
            c._ordering = self._ordering
        return c


##########
# ERRORS #
##########
class ValidationError(StandardError):
    pass

class MissingID(StandardError):
    pass

class AttributeNotIndexed(StandardError):
    pass

class Attribute(object):
    def __init__(self,
                 name=None,
                 indexed=True,
                 required=False):
        self.name = name
        self.indexed = indexed
        self.required = required

    def __get__(self, instance, owner):
        try:
            return getattr(instance, '_' + self.name)
        except AttributeError:
            return None

    def __set__(self, instance, value):
        setattr(instance, '_' + self.name, value)

    def typecast_for_read(self, value):
        return value

    def typecast_for_storage(self, value):
        return str(value)


def _initialize_attributes(model_class, name, bases, attrs):
    """Initialize the attributes of the model."""
    model_class._attributes = {}
    for k, v in attrs.iteritems():
        if isinstance(v, Attribute):
            model_class._attributes[k] = v
            v.name = v.name or k

def _initialize_indices(model_class, name, bases, attrs):
    model_class._indices = []
    for k, v in attrs.iteritems():
        if isinstance(v, Attribute) and v.indexed:
            model_class._indices.append(k)

    if model_class._meta['indices']:
        model_class._indices.extend(model_class._meta['indices'])

def _initialize_key(model_class, name):
    model_class._key = Key(name)

def _initialize_db(model_class):
    model_class._db = model_class._meta['db'] or _get_client()

def _initialize_manager(model_class):
    model_class.objects = ManagerDescriptor(Manager(model_class))

def _encode_key(s):
    return base64.b64encode(s).replace("\n", "")

class ModelOptions(object):
    def __init__(self, meta):
        self.meta = meta

    def get_field(self, field_name):
        if self.meta is None:
            return None
        try:
            return self.meta.__dict__[field_name]
        except KeyError:
            return None
    __getitem__ = get_field


class ModelBase(type):
    def __init__(cls, name, bases, attrs):
        super(ModelBase, cls).__init__(name, bases, attrs)
        cls._meta = ModelOptions(attrs.pop('Meta', None))
        _initialize_attributes(cls, name, bases, attrs)
        _initialize_indices(cls, name, bases, attrs)
        _initialize_key(cls, name)
        _initialize_db(cls)
        _initialize_manager(cls)


class Model(object):
    __metaclass__ = ModelBase

    def __init__(self, **kwargs):
        for att in self.attributes.values():
            if att.name in kwargs:
                att.__set__(self, kwargs[att.name])

    def clean_fields(self):
        pass

    def clean(self):
        """Override this. in the model"""
        pass

    def save(self):
        if self.is_new():
            self._initialize_id()
        self._create_membership()
        self._update_indices()
        h = {}
        for k, v in self.attributes.iteritems():
            h[k] = v.typecast_for_storage(getattr(self, k))
        for index in self.indices:
            v = getattr(self, index)
            if callable(v):
                v = v()
            h[index] = str(v)
        self.db.hmset(self.key(), h)

    def _initialize_id(self):
        self.id = str(self.db.incr(self._key['id']))

    def key(self):
        return self._key[self.id]

    def delete(self):
        del self.db[self.key()]

    def _create_membership(self):
        Set(self._key['all']).add(self.id)

    def _delete_membership(self):
        Set(self._key['all']).remove(self.id)

    def _update_indices(self):
        self._delete_from_indices()
        self._add_to_indices()

    def _add_to_indices(self):
        s = Set(self.key()['_indices'])
        pipe = s.db.pipeline()
        for att in self.indices:
            self._add_to_index(att, pipe=pipe)
        pipe.execute()

    def _add_to_index(self, att, val=None, pipe=None):
        index = self._index_key_for(att, val)
        pipe.sadd(index, self.id)
        pipe.sadd(self.key()['_indices'], index)

    def _delete_from_indices(self):
        s = Set(self.key()['_indices'])
        pipe = s.db.pipeline()
        for index in s.members:
            pipe.srem(index, self.id)
        pipe.delete(s.key)
        pipe.execute()

    @property
    def id(self):
        if not hasattr(self, '_id'):
            raise MissingID
        return self._id

    @id.setter
    def id(self, val):
        self._id = str(val)

    @property
    def attributes(cls):
        """Return the attributes of the model."""
        return dict(cls._attributes)

    @property
    def indices(cls):
        return cls._indices

    @property
    def db(cls):
        return cls._db

    def _index_key_for(self, att, value=None):
        if value is None:
            value = getattr(self, att)
            if callable(value):
                value = str(value())
        return self._key[att][_encode_key(value)]

    def is_new(self):
        return not hasattr(self, '_id')

    def __hash__(self):
        return hash(self.key())

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.key() == other.key()

    def __ne__(self, other):
        return not self.__eq__(other)

