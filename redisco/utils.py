class DictWithDefault(dict):

    def __init__(self, default=None, *args, **kwargs):
        self.default = default
        dict.__init__(self , *args, **kwargs)

    def __getitem__(self, key):
        if not self.has_key(key):
            if self.default is None:
                pass
            elif callable(self.default):
                self.default(self, key)
            else:
                self.__setitem__(key, self.default)
        return super(DictWithDefault, self).__getitem__(key)
