import unittest

from accounts.authentication import authenticate
from accounts.directory import lookup_profile
from accounts.registration import register
from accounts.store import AccountStore


class AccountIdentityTests(unittest.TestCase):
    def setUp(self):
        self.store = AccountStore()

    def test_registration_preserves_display_name(self):
        profile = register(self.store, "  Alice.Dev  ", "a@example.com", "secret")
        self.assertEqual(profile.username, "Alice.Dev")

    def test_login_ignores_case_and_whitespace(self):
        register(self.store, "Alice.Dev", "a@example.com", "secret")
        profile = authenticate(self.store, "  ALICE.dev ", "secret")
        self.assertIsNotNone(profile)
        self.assertEqual(profile.username, "Alice.Dev")

    def test_directory_lookup_uses_same_identity(self):
        register(self.store, "Alice.Dev", "a@example.com", "secret")
        self.assertIsNotNone(lookup_profile(self.store, " alice.DEV "))

    def test_unicode_casefold_and_duplicate_detection(self):
        register(self.store, "Straße", "one@example.com", "secret")
        self.assertIsNotNone(authenticate(self.store, "STRASSE", "secret"))
        with self.assertRaises(ValueError):
            register(self.store, " strasse ", "two@example.com", "secret")


if __name__ == "__main__":
    unittest.main()
