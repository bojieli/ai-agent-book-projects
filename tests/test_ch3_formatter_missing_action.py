"""Regression test: format_memory_operations must handle missing or None 'action' key without KeyError or AttributeError."""
import os
import sys

sys.path.insert(0, os.path.abspath("chapter3/user-memory"))

from memory_operation_formatter import format_memory_operations


def test_format_memory_operations_handles_missing_action():
    ops = [{"content": "Important note text", "reason": "user request"}]
    result = format_memory_operations(ops)
    assert "UNKNOWN" in result or "❓" in result
    assert "Content: Important note text" in result


def test_format_memory_operations_handles_none_action():
    ops = [{"action": None, "content": "Another note text"}]
    result = format_memory_operations(ops)
    assert "UNKNOWN" in result or "❓" in result
    assert "Content: Another note text" in result
