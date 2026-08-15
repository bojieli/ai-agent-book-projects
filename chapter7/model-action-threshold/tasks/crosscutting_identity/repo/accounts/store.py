class AccountStore:
    def __init__(self):
        self._profiles = {}

    def save(self, key, profile):
        if key in self._profiles:
            raise ValueError("username already exists")
        self._profiles[key] = profile

    def find(self, key):
        return self._profiles.get(key)
