class Cache:
    def __init__(self):
        self._values = {}

    def get(self, key, default=None):
        return self._values.get(key, default)

    def put(self, key, value):
        self._values[key] = value

    def get_or_load(self, key, loader):
        cached = self.get(key)
        if cached is not None:
            return cached
        value = loader(key)
        self.put(key, value)
        return value
