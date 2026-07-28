"""Shared pytest fixtures for the web search agent test suite."""

import json
import socket
from types import SimpleNamespace

import pytest

PROVIDER_ENV_VARS = (
    "MOONSHOT_API_KEY",
    "KIMI_API_KEY",
    "OPENROUTER_API_KEY",
    "OPENROUTER_BASE_URL",
    "OPENROUTER_MODEL",
)


@pytest.fixture(autouse=True)
def isolate_provider_environment(monkeypatch):
    """Keep developer credentials and provider overrides out of every test."""
    for variable in PROVIDER_ENV_VARS:
        monkeypatch.delenv(variable, raising=False)


@pytest.fixture(autouse=True)
def block_external_network(monkeypatch):
    """Fail fast if a unit test accidentally attempts a network connection."""

    def deny_network(*args, **kwargs):
        raise AssertionError("Unit tests must not access the external network")

    monkeypatch.setattr(socket, "create_connection", deny_network)
    monkeypatch.setattr(socket, "getaddrinfo", deny_network)
    monkeypatch.setattr(socket.socket, "connect", deny_network)
    monkeypatch.setattr(socket.socket, "connect_ex", deny_network)


@pytest.fixture
def make_tool_call():
    """Build a minimal SDK-shaped tool-call object for mocked model replies."""

    def factory(
        *,
        name="$web_search",
        arguments=None,
        call_id="call-1",
    ):
        payload = arguments if arguments is not None else {"query": "example"}
        return SimpleNamespace(
            id=call_id,
            function=SimpleNamespace(
                name=name,
                arguments=json.dumps(payload, ensure_ascii=False),
            ),
        )

    return factory


@pytest.fixture
def make_choice():
    """Build a minimal SDK-shaped chat choice for deterministic Agent tests."""

    def factory(
        *,
        finish_reason="stop",
        content="",
        reasoning_content=None,
        tool_calls=None,
    ):
        return SimpleNamespace(
            finish_reason=finish_reason,
            message=SimpleNamespace(
                content=content,
                reasoning_content=reasoning_content,
                tool_calls=list(tool_calls or []),
            ),
        )

    return factory
