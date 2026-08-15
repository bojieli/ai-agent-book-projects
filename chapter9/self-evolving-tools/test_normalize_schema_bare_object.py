"""normalize_schema must keep bare {"type":"object"} as an empty-object schema while preserving extra metadata."""

from tool_manager import normalize_schema


def test_bare_object_type_stays_empty_properties():
    assert normalize_schema({"type": "object"}) == {
        "type": "object",
        "properties": {},
    }


def test_object_with_required_keeps_required_not_as_property():
    assert normalize_schema({"type": "object", "required": []}) == {
        "type": "object",
        "properties": {},
        "required": [],
    }


def test_object_with_properties_unchanged():
    schema = {
        "type": "object",
        "properties": {"x": {"type": "string"}},
        "required": ["x"],
    }
    assert normalize_schema(schema) == schema


def test_properties_only_still_gets_object_type():
    assert normalize_schema({"properties": {"y": {"type": "number"}}}) == {
        "type": "object",
        "properties": {"y": {"type": "number"}},
    }


def test_plain_property_map_still_wrapped():
    assert normalize_schema({"z": {"type": "boolean"}}) == {
        "type": "object",
        "properties": {"z": {"type": "boolean"}},
    }


def test_object_retains_extra_metadata():
    schema = {
        "type": "object",
        "description": "Tool parameters",
        "additionalProperties": False,
        "$defs": {"Item": {"type": "string"}},
    }
    expected = {
        "type": "object",
        "properties": {},
        "description": "Tool parameters",
        "additionalProperties": False,
        "$defs": {"Item": {"type": "string"}},
    }
    assert normalize_schema(schema) == expected
