import pytest
from memory_operation_formatter import format_memory_operations


def test_format_memory_operations_includes_memory_id_when_content_present():
    operations = [
        {
            "action": "update",
            "memory_id": "mem_101",
            "content": "User prefers dark mode.",
            "reason": "User updated preference",
        }
    ]
    result = format_memory_operations(operations)
    assert "Memory ID: mem_101" in result
    assert "Content: User prefers dark mode." in result
