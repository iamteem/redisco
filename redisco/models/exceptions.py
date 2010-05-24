##########
# ERRORS #
##########
class ValidationError(StandardError):
    pass

class MissingID(StandardError):
    pass

class AttributeNotIndexed(StandardError):
    pass

class FieldValidationError(StandardError):

    def __init__(self, errors, *args, **kwargs):
        super(FieldValidationError, self).__init__(*args, **kwargs)
        self._errors = errors

    @property
    def errors(self):
        return self._errors
