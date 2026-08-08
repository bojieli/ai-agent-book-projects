import unittest

from customer_service_env import _derive_claims_and_promises


class TestDeriveClaimsPromisesNullResult(unittest.TestCase):
    def test_derive_claims_and_promises_tolerates_non_dict_result(self):
        """Contract: _derive_claims_and_promises handles tool calls with None or non-dict result fields.

        Locks out AttributeError when tool_calls entries contain None, primitive, or missing result values.
        """
        messages = [{"role": "assistant", "content": "Your refund is completed", "turn": 2}]
        tool_calls = [
            {"name": "refund_order", "turn": 1, "result": None},
            {"name": "refund_order", "turn": 1, "result": "error: timeout"},
        ]
        claims, promises = _derive_claims_and_promises(messages, tool_calls)
        self.assertEqual(1, len(claims))
        self.assertEqual("", claims[0]["supported_by"])
        self.assertEqual(1, len(promises))


if __name__ == "__main__":
    unittest.main()
