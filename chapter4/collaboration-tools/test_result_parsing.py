"""Tests for MCP result parsing."""

import unittest

from result_parsing import parse_mapping


class ParseMappingTests(unittest.TestCase):
    def test_parses_python_mapping_literal(self):
        text = (
            "{'success': True, 'timer_id': 'abc', "
            "'metadata': {'attempt': None, 'tags': ['demo']}}"
        )

        self.assertEqual(
            parse_mapping(text),
            {
                "success": True,
                "timer_id": "abc",
                "metadata": {"attempt": None, "tags": ["demo"]},
            },
        )

    def test_keeps_expression_like_text_as_data(self):
        expression = "__import__('os').system('echo unexpected')"

        self.assertEqual(
            parse_mapping(repr({"message": expression})),
            {"message": expression},
        )

    def test_rejects_expression(self):
        with self.assertRaisesRegex(ValueError, "dictionary literal"):
            parse_mapping("__import__('builtins').dict(executed=True)")

    def test_rejects_non_mapping_literal(self):
        with self.assertRaisesRegex(ValueError, "dictionary literal"):
            parse_mapping("['not', 'a', 'mapping']")


if __name__ == "__main__":
    unittest.main()
