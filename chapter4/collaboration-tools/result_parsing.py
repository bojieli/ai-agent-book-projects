"""Helpers for parsing text returned by collaboration tools."""

import ast
from typing import Any


def parse_mapping(text: str) -> dict[str, Any]:
    """Parse a Python dictionary literal without evaluating expressions."""
    try:
        parsed = ast.literal_eval(text)
    except (SyntaxError, ValueError) as exc:
        raise ValueError("MCP tool result must be a dictionary literal") from exc

    if not isinstance(parsed, dict):
        raise ValueError("MCP tool result must be a dictionary literal")

    return parsed
