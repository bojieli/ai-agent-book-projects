"""Focused validation for Experiment 4-3 desktop/mobile execution tools."""

from __future__ import annotations

import asyncio

from extended_tools import ExtendedTools


def test_virtual_desktop_rejects_non_https() -> None:
    result = asyncio.run(ExtendedTools().virtual_desktop_execute(
        "http://example.com", "unused.png"))
    assert result == {"success": False, "error": "Only HTTPS URLs are allowed"}


def test_virtual_mobile_rejects_unsafe_container_name() -> None:
    result = asyncio.run(ExtendedTools().virtual_mobile_execute(
        "container; touch escaped", "unused.png"))
    assert result == {"success": False, "error": "Invalid Docker container name"}
