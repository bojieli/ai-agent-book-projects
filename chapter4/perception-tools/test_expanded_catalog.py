"""Offline contract checks for the real-backed 126-tool perception catalog."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import tiktoken

SRC = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC))

import expanded_catalog  # noqa: E402
import main  # noqa: E402


def _schemas() -> list[dict]:
    tools = asyncio.run(main.mcp.list_tools())
    return [tool.model_dump(by_alias=True, exclude_none=True, mode="json")
            for tool in tools]


def test_catalog_has_126_unique_complete_schemas_over_50k_tokens():
    schemas = _schemas()
    names = {schema["name"] for schema in schemas}
    rendered = "\n".join(json.dumps(schema, ensure_ascii=False, indent=2)
                         for schema in schemas)
    assert len(schemas) == len(names) == 126
    assert len(expanded_catalog.EXPANDED_SPECS) == 70
    assert len(expanded_catalog.EXISTING_TOOL_CONTRACTS) == 56
    assert len(tiktoken.get_encoding("o200k_base").encode(rendered)) > 50_000
    assert {
        "web_search", "code_interpreter", "yfinance_quote", "search_news",
        "arxiv_search", "arxiv_download", "github_list_contributors",
    } <= names
    assert all("success" in schema["description"].lower()
               and "failure" in schema["description"].lower()
               for schema in schemas)


def test_expanded_parameter_descriptions_are_tool_specific():
    schemas = {schema["name"]: schema for schema in _schemas()}
    for spec in expanded_catalog.EXPANDED_SPECS:
        properties = schemas[spec.name]["inputSchema"]["properties"]
        assert spec.name in properties["query"]["description"]
        assert spec.name in properties["options_json"]["description"]


def test_code_interpreter_nonzero_exit_fails_closed():
    spec = next(spec for spec in expanded_catalog.EXPANDED_SPECS
                if spec.name == "code_interpreter")
    receipt = asyncio.run(expanded_catalog.execute_expanded_tool(
        spec, 'raise RuntimeError("expected")', '{"timeout": 5}'
    ))
    assert receipt["success"] is False
    assert receipt["error_type"] == "ProcessExecutionError"
    assert receipt["data"]["returncode"] != 0
    assert "RuntimeError" in receipt["data"]["stderr"]
