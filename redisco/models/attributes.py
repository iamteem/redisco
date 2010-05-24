import time
from datetime import datetime, date
from redisco.containers import List
from exceptions import FieldValidationError

__all__ = ['Attribute', 'ListField', 'DateTimeField',
        'DateField', 'ReferenceField', 'IntegerField',
        'FloatField']

class Attribute(object):
    def __init__(self,
                 name=None,
                 indexed=True,
                 required=False,
                 validator=None):
        self.name = name
        self.indexed = indexed
        self.required = required
        self.validator = validator

    def __get__(self, instance, owner):
        try:
            return getattr(instance, '_' + self.name)
        except AttributeError:
            if not instance.is_new():
                val = instance.db.hget(instance.key(), self.name)
                if val is not None:
                    val = self.typecast_for_read(val)
                self.__set__(instance, val)
                return val
            else:
                self.__set__(instance, None)
                return None


    def __set__(self, instance, value):
        setattr(instance, '_' + self.name, value)

    def typecast_for_read(self, value):
        return value

    def typecast_for_storage(self, value):
        return str(value)
    
    def value_type(self):
        return str

    def validate(self, instance):
        val = getattr(instance, self.name)
        errors = []
        # type_validation
        if val and not isinstance(val, self.value_type()):
            errors.append((self.name, 'bad type',))
        # validate first standard stuff
        if self.required:
            if val is None or not str(val).strip():
                errors.append((self.name, 'required'))
        # validate using validator
        if self.validator:
            r = self.validator(val)
            if r:
                errors.extend(r)
        if errors:
            raise FieldValidationError(errors)

class IntegerField(Attribute):
    def typecast_for_read(self, value):
        return int(value)

    def typecast_for_storage(self, value):
        if value is None:
            return "0"
        return str(value)

    def value_type(self):
        return int


class FloatField(Attribute):
    def typecast_for_read(self, value):
        return float(value)

    def typecast_for_storage(self, value):
        if value is None:
            return "0"
        return str(value)

    def value_type(self):
        return float

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

    def value_type(self):
        return datetime


class DateField(Attribute):

    def __init__(self, auto_now=False, auto_now_add=False, **kwargs):
        super(DateField, self).__init__(**kwargs)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add

    def typecast_for_read(self, value):
        try:
            return date.fromtimestamp(float(value))
        except TypeError, ValueError:
            return None

    def typecast_for_storage(self, value):
        if not isinstance(value, date):
            raise TypeError("%s should be date object, and not a %s" %
                    (self.name, type(value)))
        if value is None:
            return None
        return "%f" % time.mktime(value.timetuple())

    def value_type(self):
        return date


class ListField(object):
    def __init__(self, target_type,
                 name=None,
                 indexed=True,
                 required=False,
                 validator=None):
        self._target_type = target_type
        self.name = name
        self.indexed = indexed
        self.required = required
        self.validator = validator

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

    def validate(self, instance):
        val = getattr(instance, self.name)
        errors = []

        if val:
            for item in val:
                if not isinstance(item, self._target_type):
                    errors.append((self.name, 'bad type in list'))

        # validate first standard stuff
        if self.required:
            if not val:
                errors.append((self.name, 'required'))
        # validate using validator
        if self.validator:
            r = self.validator(val)
            if r:
                errors.extend(r)
        if errors:
            raise FieldValidationError(errors)


class ReferenceField(object):
    def __init__(self,
                 target_type,
                 name=None,
                 attname=None,
                 indexed=True,
                 required=True,
                 related_name=None,
                 validator=None):
        self._target_type = target_type
        self.name = name
        self.indexed = indexed
        self.required = required
        self._attname = attname
        self._related_name = related_name
        self.validator = validator

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

    def validate(self, instance):
        val = getattr(instance, self.name)
        errors = []

        if val:
            if not isinstance(val, self._target_type):
                errors.append((self.name, 'bad type for reference'))

        # validate first standard stuff
        if self.required:
            if not val:
                errors.append((self.name, 'required'))
        # validate using validator
        if self.validator:
            r = self.validator(val)
            if r:
                errors.extend(r)
        if errors:
            raise FieldValidationError(errors)
