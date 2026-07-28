"""Unit tests for model mapping and provider selection."""

import pytest

from config import map_model_to_openrouter, resolve_llm_backend


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        ("openai/gpt-5.6-luna", "openai/gpt-5.6-luna"),
        ("gpt-5.6-luna", "openai/gpt-5.6-luna"),
        ("o3-mini", "openai/o3-mini"),
        ("claude-sonnet-4.6", "anthropic/claude-sonnet-4.6"),
        ("claude-haiku-4.5", "anthropic/claude-haiku-4.5"),
        ("claude-opus-4.8", "anthropic/claude-opus-4.8"),
        ("kimi-k3", "moonshotai/kimi-k2.6"),
    ],
)
def test_map_model_to_openrouter(model, expected):
    assert map_model_to_openrouter(model) == expected


def test_unknown_model_uses_configured_openrouter_default(monkeypatch):
    monkeypatch.setenv("OPENROUTER_MODEL", "vendor/fallback-model")

    assert map_model_to_openrouter("unknown-model") == "vendor/fallback-model"


def test_primary_provider_is_preserved_when_its_key_exists():
    assert resolve_llm_backend(
        "moonshot-key", "https://moonshot.test/v1", "kimi-k3"
    ) == (
        "moonshot-key",
        "https://moonshot.test/v1",
        "kimi-k3",
        False,
    )


def test_openrouter_is_used_when_primary_key_is_missing(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")
    monkeypatch.setenv("OPENROUTER_BASE_URL", "https://openrouter.test/v1")

    assert resolve_llm_backend(None, "https://moonshot.test/v1", "kimi-k3") == (
        "openrouter-key",
        "https://openrouter.test/v1",
        "moonshotai/kimi-k2.6",
        True,
    )


def test_gpt5_prefers_openrouter_when_both_keys_exist(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")

    resolved = resolve_llm_backend(
        "primary-key", "https://primary.test/v1", "gpt-5.6-luna"
    )

    assert resolved == (
        "openrouter-key",
        "https://openrouter.ai/api/v1",
        "openai/gpt-5.6-luna",
        True,
    )


def test_provider_resolution_requires_a_key():
    with pytest.raises(ValueError, match="No API key found"):
        resolve_llm_backend(None, "https://moonshot.test/v1", "kimi-k3")
