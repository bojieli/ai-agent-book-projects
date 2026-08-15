def authenticate(store, username, password):
    profile = store.find(username.strip())
    if profile is None or profile.password != password:
        return None
    return profile
