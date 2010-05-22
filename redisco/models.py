import base64
from datetime import datetime
from connection import _get_client
from containers import Set, List
from key import Key

############
# Managers #
############

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
        self._limit = None
        self._offset = None

    #################
    # MAGIC METHODS #
    #################

    def __getitem__(self, index):
        l = list(self._set)
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
        return len(self._set)

    def __contains__(self, val):
        return val in self.members


    ##########################################
    # METHODS THAT RETURN A SET OF INSTANCES #
    ##########################################

    @property
    def members(self):
        return map(lambda id: self._get_item_with_id(id), self._set.members)

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

    def limit(self, n, offset=0):
        clone = self._clone()
        clone._limit = n
        clone._offset = offset
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

    @property
    def _set(self):
        s = Set(self.key)
        if self._filters:
            s = self._add_set_filter(s)
        s = self._order(s.key)
        return s

    def _add_set_filter(self, s):
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
        return Set(new_set_key)

    def _order(self, skey):
        if self._ordering:
            return self._set_with_ordering(skey)
        else:
            return self._set_without_ordering(skey)

    def _set_with_ordering(self, skey):
        num, start = self._get_limit_and_offset()
        old_set_key = skey
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
                         start=start,
                         num=num,
                         desc=desc)
            return List(new_set_key)

    def _set_without_ordering(self, skey):
        # sort by id
        num, start = self._get_limit_and_offset()
        old_set_key = skey
        new_set_key = "%s#" % old_set_key
        self.db.sort(old_set_key,
                     store=new_set_key,
                     start=start,
                     num=num)
        return List(new_set_key)

    def _get_limit_and_offset(self):
        if (self._limit is not None and self._offset is None) or \
                (self._limit is None and self._offset is not None):
                    raise "Limit and offset must be specified"

        if self._limit is None:
            return (None, None)
        else:
            return (self._limit, self._offset)

    def _get_item_with_id(self, id):
        key = self.model_class._key[id]
        if self.db.exists(key):
            kwargs = self.db.hgetall(key)
            kattributes = self.model_class._attributes
            for att, value in kwargs.iteritems():
                if att in kattributes:
                    kwargs[att] = (kattributes[att]
                            .typecast_for_read(value))

            # load lists
            latts = self.model_class._lists
            for li in latts:
                rl = List(key[li])
                kwargs[li] = rl.members

            # create new instance
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
        c._limit = self._limit
        c._offset = self._offset
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
    
    def value_type(self):
        return str

class IntegerField(Attribute):
    def typecast_for_read(self, value):
        return int(value)

    def typecast_for_storage(self, value):
        if value is None:
            return "0"
        return str(value)

    def value_type(self):
        return int


class DateTimeField(Attribute):

    def __init__(self, auto_now=False, auto_now_add=False, **kwargs):
        super(DateTimeField, self).__init__(**kwargs)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add

    def typecast_for_read(self, value):
        try:
            da = value.split('.')
            if len(da) == 1:
                return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            else:
                return datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
        except TypeError, ValueError:
            return None

    def typecast_for_storage(self, value):
        if not isinstance(value, datetime):
            raise TypeError("%s should be datetime object, and not a %s" %
                    (self.name, type(value)))
        if value is None:
            return None
        return str(value)


class ListField(object):
    def __init__(self, target_type,
                 name=None,
                 indexed=True,
                 required=False):
        self._target_type = target_type
        self.name = name
        self.indexed = indexed

    def __get__(self, instance, owner):
        try:
            return getattr(instance, '_' + self.name)
        except AttributeError:
            return None

    def __set__(self, instance, value):
        setattr(instance, '_' + self.name, value)

    def value_type(self):
        return self._target_type

class ReferenceField(object):
    def __init__(self,
                 target_type,
                 name=None,
                 attname=None,
                 indexed=True,
                 required=True,
                 related_name=None):
        self._target_type = target_type
        self.name = name
        self.indexed = indexed
        self.required = required
        self._attname = attname
        self._related_name = related_name

    def __set__(self, instance, value):
        if not isinstance(value, self._target_type) and \
                value is not None:
            raise TypeError
        setattr(instance, self.attname, value.id)

    def __get__(self, instance, owner):
        try:
            if not hasattr(self, '_' + self.name):
                o = self._target_type.objects.get_by_id(
                                    getattr(instance, self.attname))
                setattr(self, '_' + self.name, o)
            return getattr(self, '_' + self.name)
        except AttributeError:
            return None

    def value_type(self):
        return self._target_type

    @property
    def attname(self):
        if self._attname is None:
            self._attname = self.name + '_id'
        return self._attname

    @property
    def related_name(self):
        return self._related_name 


##############################
# Model Class Initialization #
##############################

def _initialize_attributes(model_class, name, bases, attrs):
    """Initialize the attributes of the model."""
    model_class._attributes = {}
    for k, v in attrs.iteritems():
        if isinstance(v, Attribute):
            model_class._attributes[k] = v
            v.name = v.name or k

def _initialize_referenced(model_class, attribute):
    # this should be a descriptor
    def _related_objects(self):
        return (model_class.objects
                .filter(**{attribute.attname: self.id}))

    related_name = (attribute.related_name or
            model_class.__name__.lower() + '_set')
    setattr(attribute._target_type, related_name,
            property(_related_objects))

def _initialize_lists(model_class, name, bases, attrs):
    model_class._lists = {}
    for k, v in attrs.iteritems():
        if isinstance(v, ListField):
            model_class._lists[k] = v
            v.name = v.name or k

def _initialize_references(model_class, name, bases, attrs):
    model_class._references = {}
    h = {}
    for k, v in attrs.iteritems():
        if isinstance(v, ReferenceField):
            model_class._references[k] = v
            v.name = v.name or k
            att = Attribute(name=v.attname)
            h[v.attname] = att
            setattr(model_class, v.attname, att)
            _initialize_referenced(model_class, v)
    attrs.update(h)

def _initialize_indices(model_class, name, bases, attrs):
    model_class._indices = []
    for k, v in attrs.iteritems():
        if isinstance(v, Attribute) and v.indexed:
            model_class._indices.append(k)
        elif isinstance(v, ListField) and v.indexed:
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
        _initialize_references(cls, name, bases, attrs)
        _initialize_attributes(cls, name, bases, attrs)
        _initialize_lists(cls, name, bases, attrs)
        _initialize_indices(cls, name, bases, attrs)
        _initialize_key(cls, name)
        _initialize_db(cls)
        _initialize_manager(cls)

class Model(object):
    __metaclass__ = ModelBase

    def __init__(self, **kwargs):
        attrs = self.attributes.values() + self.lists.values() \
                + self.references.values()
        for att in attrs:
            if att.name in kwargs:
                att.__set__(self, kwargs[att.name])

    def clean_fields(self):
        pass

    def clean(self):
        """Override this. in the model"""
        pass

    def save(self):
        _new = self.is_new()
        if _new:
            self._initialize_id()
        self._create_membership()
        self._update_indices()
        h = {}
        # attributes
        for k, v in self.attributes.iteritems():
            if isinstance(v, DateTimeField):
                if v.auto_now:
                    setattr(self, k, datetime.now())
                if v.auto_now_add and _new:
                    setattr(self, k, datetime.now())
            h[k] = v.typecast_for_storage(getattr(self, k))
        # indices
        for index in self.indices:
            if index not in self.lists and index not in self.attributes:
                v = getattr(self, index)
                if callable(v):
                    v = v()
                h[index] = str(v)
        if h:
            self.db.hmset(self.key(), h)

        # lists
        for k, v in self.lists.iteritems():
            l = List(self.key()[k])
            l.clear()
            values = getattr(self, k)
            if values:
                l.extend(values)

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
        """
        Adds the base64 encoded values of the indices.
        """
        pipe = self.db.pipeline()
        for att in self.indices:
            self._add_to_index(att, pipe=pipe)
        pipe.execute()

    def _add_to_index(self, att, val=None, pipe=None):
        """
        Adds the id to the index.

        This also adds to the _indices set of the object.
        """
        index = self._index_key_for(att)
        if index is None or not index:
            return
        if isinstance(index, list):
            for i in index:
                pipe.sadd(i, self.id)
                pipe.sadd(self.key()['_indices'], i)
        else:
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
    def lists(cls):
        """Return the lists of the model."""
        return dict(cls._lists)

    @property
    def indices(cls):
        return cls._indices

    @property
    def references(cls):
        return cls._references

    @property
    def db(cls):
        return cls._db

    def _index_key_for(self, att, value=None):
        if value is None:
            value = getattr(self, att)
            if callable(value):
                value = value()
        if att not in self.lists:
            if value is not None:
                return self._key[att][_encode_key(str(value))]
            else:
                return None
        else:
            l = getattr(self, att)
            if l:
                return [self._key[att][_encode_key(str(e))] for e in l]
            else:
                return None

    def is_new(self):
        return not hasattr(self, '_id')

    def __hash__(self):
        return hash(self.key())

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.key() == other.key()

    def __ne__(self, other):
        return not self.__eq__(other)

