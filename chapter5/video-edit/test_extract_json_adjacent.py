"""_extract_json must accept the first object when another object follows."""

import pytest

from agents import _extract_json


def test_adjacent_json_objects_returns_first():
    assert _extract_json('{"a":1}{"b":2}') == {"a": 1}


def test_prose_with_two_objects_returns_first():
    assert _extract_json('note {"a":1} mid {"b":2}') == {"a": 1}


def test_single_object_unchanged():
    assert _extract_json('prefix {"ok": true, "n": 3} suffix') == {"ok": True, "n": 3}


def test_no_object_raises():
    with pytest.raises(ValueError, match="未能从回复中解析 JSON"):
        _extract_json("no braces here")
