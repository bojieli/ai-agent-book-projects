"""Offline contract tests for the Xquik X post search tool."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import cli
import xquik_tools


class FakeResponse:
    def __init__(
        self,
        status_code: int,
        payload: Any,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}

    def json(self) -> Any:
        return self._payload


def _decoded(result) -> dict[str, Any]:
    return json.loads(result.text)


def _install_client(monkeypatch, response: FakeResponse) -> dict[str, Any]:
    observed: dict[str, Any] = {}

    class FakeClient:
        def __init__(self, **kwargs: Any) -> None:
            observed["client"] = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def get(self, url: str, **kwargs: Any) -> FakeResponse:
            observed["url"] = url
            observed.update(kwargs)
            return response

    monkeypatch.setattr(xquik_tools.httpx, "AsyncClient", FakeClient)
    return observed


def test_search_x_posts_uses_bounded_read_contract(monkeypatch):
    api_key = "xq_test_secret"
    monkeypatch.setenv("XQUIK_API_KEY", api_key)
    observed = _install_client(
        monkeypatch,
        FakeResponse(
            200,
            {
                "tweets": [
                    {
                        "id": "1900000000000000000",
                        "text": "Agent tooling release",
                        "author": {"username": "example"},
                    }
                ],
                "has_next_page": True,
                "next_cursor": "opaque-cursor",
            },
        ),
    )

    result = asyncio.run(
        xquik_tools.search_x_posts(
            "agent tooling",
            limit=25,
            cursor="next-page",
            query_type="Latest",
        )
    )
    payload = _decoded(result)

    assert observed["url"] == xquik_tools.XQUIK_SEARCH_URL
    assert observed["params"] == {
        "q": "agent tooling",
        "limit": 25,
        "queryType": "Latest",
        "cursor": "next-page",
    }
    assert observed["headers"]["x-api-key"] == api_key
    assert observed["headers"]["xquik-api-contract"] == xquik_tools.XQUIK_CONTRACT
    assert observed["client"] == {"timeout": 30.0, "follow_redirects": False}
    assert payload["success"] is True
    assert payload["message"]["count"] == 1
    assert payload["message"]["next_cursor"] == "opaque-cursor"
    assert payload["metadata"]["content_is_untrusted"] is True
    assert api_key not in result.text


def test_search_x_posts_requires_environment_credential(monkeypatch):
    monkeypatch.delenv("XQUIK_API_KEY", raising=False)

    class UnexpectedClient:
        def __init__(self, **_kwargs: Any) -> None:
            raise AssertionError("network client must not start without credentials")

    monkeypatch.setattr(xquik_tools.httpx, "AsyncClient", UnexpectedClient)
    payload = _decoded(asyncio.run(xquik_tools.search_x_posts("agent tooling")))

    assert payload["success"] is False
    assert payload["metadata"]["error_type"] == "missing_credentials"


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"query": "  "}, "Search query cannot be empty."),
        ({"query": "agents", "limit": 0}, "Limit must be between 1 and 100."),
        ({"query": "agents", "limit": 101}, "Limit must be between 1 and 100."),
        ({"query": "agents", "query_type": "Popular"}, "Query type must be Latest or Top."),
    ],
)
def test_search_x_posts_rejects_invalid_inputs(monkeypatch, kwargs, message):
    monkeypatch.setenv("XQUIK_API_KEY", "xq_test_secret")
    payload = _decoded(asyncio.run(xquik_tools.search_x_posts(**kwargs)))

    assert payload["success"] is False
    assert payload["message"] == message
    assert payload["metadata"]["error_type"] == "invalid_parameters"


def test_search_x_posts_preserves_structured_provider_error(monkeypatch):
    api_key = "xq_test_secret"
    monkeypatch.setenv("XQUIK_API_KEY", api_key)
    _install_client(
        monkeypatch,
        FakeResponse(
            402,
            {
                "error": {
                    "code": "insufficient_credits",
                    "message": "Insufficient credits. Top up first.",
                }
            },
        ),
    )

    result = asyncio.run(xquik_tools.search_x_posts("agent tooling"))
    payload = _decoded(result)

    assert payload["success"] is False
    assert payload["message"] == "Insufficient credits. Top up first."
    assert payload["metadata"]["status_code"] == 402
    assert payload["metadata"]["error_code"] == "insufficient_credits"
    assert api_key not in result.text


def test_search_x_posts_fails_closed_on_invalid_pagination(monkeypatch):
    monkeypatch.setenv("XQUIK_API_KEY", "xq_test_secret")
    _install_client(
        monkeypatch,
        FakeResponse(
            200,
            {
                "tweets": [],
                "has_next_page": "yes",
                "next_cursor": ["not", "opaque"],
            },
        ),
    )

    payload = _decoded(asyncio.run(xquik_tools.search_x_posts("agent tooling")))

    assert payload["success"] is False
    assert payload["metadata"]["error_type"] == "invalid_response"


def test_cli_exposes_xquik_search_as_metered_public_data():
    tool = cli.TOOLS_BY_NAME["xquik_search_posts"]

    assert tool.category == "public"
    assert tool.module == "xquik_tools"
    assert tool.func == "search_x_posts"
    assert "XQUIK_API_KEY" in tool.note
    assert "计费" in tool.note
