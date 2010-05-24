import time
from datetime import datetime
from redisco.containers import List

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
            val = instance.db.hget(instance.key(), self.name)
            if val is not None:
                val = self.typecast_for_read(val)
            self.__set__(instance, val)
            return val

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
            return datetime.fromtimestamp(float(value))
        except TypeError, ValueError:
            return None

    def typecast_for_storage(self, value):
        if not isinstance(value, datetime):
            raise TypeError("%s should be datetime object, and not a %s" %
                    (self.name, type(value)))
        if value is None:
            return None
        return "%d.%d" % (time.mktime(value.timetuple()),  value.microsecond)


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
            key = instance.key()[self.name]
            val = List(key).members
            if val is not None:
                val = [self.value_type()(v) for v in val]
            self.__set__(instance, val)
            return val

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

