#!/usr/bin/env python3
"""Regression tests for dispatch() in demo.py.

Bug: the agentic loop parses tool-call arguments with a JSONDecodeError
fallback to {} and then calls dispatch() with no try/except. dispatch()
used to do args["name"] / args["payload"] etc., so any malformed or
incomplete LLM tool call crashed the whole run with KeyError. Fixed to
return "[error] ..." strings that the agent can recover from.
"""

import os
from pathlib import Path

from demo import dispatch, scan_skill_catalog

OUT = Path("/tmp/test_dispatch_out.pptx")


def test_missing_name_returns_error_not_keyerror():
    catalog = scan_skill_catalog()
    # {} is exactly what the JSONDecodeError fallback in run_agent produces
    result = dispatch(catalog, "read_skill", {}, OUT)
    assert result.startswith("[error]")
    assert "name" in result


def test_missing_payload_returns_error_not_keyerror():
    catalog = scan_skill_catalog()
    result = dispatch(catalog, "run_skill_script",
                      {"name": "pptx", "script": "generate_pptx.py"}, OUT)
    assert result.startswith("[error]")
    assert "payload" in result


def test_unknown_tool_still_returns_error():
    catalog = scan_skill_catalog()
    result = dispatch(catalog, "no_such_tool", {}, OUT)
    assert result.startswith("[error]")


def test_valid_read_skill_still_works():
    catalog = scan_skill_catalog()
    result = dispatch(catalog, "read_skill", {"name": "pptx"}, OUT)
    assert not result.startswith("[error]")
    assert len(result) > 0


def test_run_skill_script_rejects_absolute_path(tmp_path):
    """run_skill_script executes the file, so it must stay inside scripts/."""
    outside = tmp_path / "evil.py"
    outside.write_text("raise AssertionError('executed out-of-tree script')")
    catalog = scan_skill_catalog()
    result = dispatch(catalog, "run_skill_script",
                      {"name": "pptx", "script": str(outside), "payload": "{}"}, OUT)
    assert result.startswith("[error]")


def test_run_skill_script_rejects_parent_traversal(tmp_path):
    outside = tmp_path / "evil.py"
    outside.write_text("raise AssertionError('executed out-of-tree script')")
    catalog = scan_skill_catalog()
    scripts_dir = (catalog["pptx"]["dir"] / "scripts").resolve()
    rel = os.path.relpath(outside, scripts_dir)
    result = dispatch(catalog, "run_skill_script",
                      {"name": "pptx", "script": rel, "payload": "{}"}, OUT)
    assert result.startswith("[error]")
