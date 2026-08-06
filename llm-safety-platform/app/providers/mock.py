"""Mock ModelProvider — echoes sanitized prompt for Phase 0."""

from __future__ import annotations

from typing import Any


class MockModelProvider:
    id = "mock-llm"

    def chat(self, messages: list[dict[str, str]], **_: Any) -> str:
        last = messages[-1]["content"] if messages else ""
        return f"MOCK_REPLY: {last[:500]}"
