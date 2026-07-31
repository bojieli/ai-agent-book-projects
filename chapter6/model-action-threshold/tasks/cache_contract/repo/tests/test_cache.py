import unittest

from cachelib import Cache


class CacheContractTests(unittest.TestCase):
    def test_negative_lookup_is_loaded_once(self):
        cache = Cache()
        calls = []

        def loader(key):
            calls.append(key)
            return None

        self.assertIsNone(cache.get_or_load("missing", loader))
        self.assertIsNone(cache.get_or_load("missing", loader))
        self.assertEqual(calls, ["missing"])

    def test_custom_default_still_distinguishes_missing_from_none(self):
        cache = Cache()
        marker = object()
        self.assertIs(cache.get("unknown", marker), marker)
        cache.put("known-none", None)
        self.assertIsNone(cache.get("known-none", marker))

    def test_falsey_values_are_cached(self):
        cache = Cache()
        calls = []

        def loader(key):
            calls.append(key)
            return 0

        self.assertEqual(cache.get_or_load("zero", loader), 0)
        self.assertEqual(cache.get_or_load("zero", loader), 0)
        self.assertEqual(calls, ["zero"])


if __name__ == "__main__":
    unittest.main()
