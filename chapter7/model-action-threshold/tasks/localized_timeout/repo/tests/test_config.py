import unittest

from app.config import DEFAULT_TIMEOUT, resolve_timeout


class ResolveTimeoutTests(unittest.TestCase):
    def test_explicit_value_wins_over_environment(self):
        self.assertEqual(resolve_timeout(12, {"AGENT_TIMEOUT": "45"}), 12)

    def test_environment_is_used_without_explicit_value(self):
        self.assertEqual(resolve_timeout(None, {"AGENT_TIMEOUT": "45"}), 45)

    def test_invalid_values_use_default(self):
        self.assertEqual(resolve_timeout("nope", {}), DEFAULT_TIMEOUT)
        self.assertEqual(resolve_timeout(0, {}), DEFAULT_TIMEOUT)
        self.assertEqual(resolve_timeout(-2, {}), DEFAULT_TIMEOUT)


if __name__ == "__main__":
    unittest.main()
