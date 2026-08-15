from accounts.models import Profile


def register(store, username, email, password):
    display_name = username.strip()
    key = display_name.lower()
    profile = Profile(display_name, email, password)
    store.save(key, profile)
    return profile
