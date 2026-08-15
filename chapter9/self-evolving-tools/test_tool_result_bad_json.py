"""Regression: malformed __TOOL_RESULT__ JSON must not raise JSONDecodeError."""
import tempfile
from pathlib import Path

from tool_manager import ToolLibrary


def test_malformed_tool_result_returns_error_dict():
    lib = ToolLibrary(library_dir=Path(tempfile.mkdtemp()))
    # Tool prints a broken marker line, then would have returned ok — driver still emits marker from wrapper.
    # Inject via code that prints a bad marker before the wrapper's print by overriding run to print bad then return.
    code = (
        "def run(**kwargs):\n"
        "    print('__TOOL_RESULT__{not-json')\n"
        "    return {'ok': True}\n"
    )
    rec = {"name": "t", "description": "d", "parameters": {"type": "object", "properties": {}}, "code": code}
    out = lib._run_record(rec, {})
    assert isinstance(out, dict)
    assert out.get("success") is False
    assert "invalid result marker" in out.get("error", "")


def test_valid_tool_result_still_succeeds():
    lib = ToolLibrary(library_dir=Path(tempfile.mkdtemp()))
    code = "def run(**kwargs):\n    return {'ok': True}\n"
    rec = {"name": "t", "description": "d", "parameters": {"type": "object", "properties": {}}, "code": code}
    out = lib._run_record(rec, {})
    assert out.get("success") is True
    assert out.get("result") == {"ok": True}
