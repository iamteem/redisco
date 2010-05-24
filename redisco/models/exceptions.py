##########
# ERRORS #
##########
class ValidationError(StandardError):
    pass

class MissingID(StandardError):
    pass

class AttributeNotIndexed(StandardError):
    pass
