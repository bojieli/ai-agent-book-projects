"""Tests for the shared provider registry.

Focus is behaviour parity with the three per-chapter copies this module
replaces, plus the resolution rules that are easy to regress.
"""

import pytest

from agentbook.providers import (
    PROVIDERS,
    SUPPORTED_PROVIDERS,
    map_model_to_openrouter,
    resolve_backend,
    resolve_llm_backend,
)

PROVIDER_KEY_VARS = [
    "SILICONFLOW_API_KEY",
    "ARK_API_KEY",
    "MOONSHOT_API_KEY",
    "KIMI_API_KEY",
    "DEEPSEEK_API_KEY",
    "ZHIPU_API_KEY",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "OLLAMA_API_KEY",
    "OPENROUTER_API_KEY",
    "OPENROUTER_MODEL",
    "OPENROUTER_BASE_URL",
    "DEEPSEEK_BASE_URL",
    "KIMI_BASE_URL",
    "OLLAMA_BASE_URL",
    "OPENAI_BASE_URL",
]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Start every test from a known-empty environment."""
    for var in PROVIDER_KEY_VARS:
        monkeypatch.delenv(var, raising=False)


# --- model mapping ----------------------------------------------------------


@pytest.mark.parametrize(
    "model,expected",
    [
        ("openai/gpt-4o", "openai/gpt-4o"),  # already an OpenRouter id
        ("gpt-4o", "openai/gpt-4o"),
        ("o1-preview", "openai/o1-preview"),
        ("claude-sonnet-4", "anthropic/claude-sonnet-4.6"),
        ("claude-haiku-4", "anthropic/claude-haiku-4.5"),
        ("claude-opus-4", "anthropic/claude-opus-4.8"),
        ("kimi-k3", "moonshotai/kimi-k2.6"),
        # Regression: two of the three original copies dropped deepseek ids to
        # the catch-all default instead of mapping them.
        ("deepseek-v4-flash", "deepseek/deepseek-v4-flash"),
    ],
)
def test_map_model_to_openrouter(model, expected):
    assert map_model_to_openrouter(model) == expected


def test_unknown_model_falls_back_to_openrouter_model_env(monkeypatch):
    monkeypatch.setenv("OPENROUTER_MODEL", "google/gemma-4-31b-it:free")
    assert map_model_to_openrouter("doubao-seed-1-6") == "google/gemma-4-31b-it:free"


# --- provider resolution ----------------------------------------------------


def test_direct_provider_key_is_used(monkeypatch):
    monkeypatch.setenv("MOONSHOT_API_KEY", "sk-moonshot")
    backend = resolve_backend("kimi")
    assert backend.api_key == "sk-moonshot"
    assert backend.base_url == "https://api.moonshot.cn/v1"
    assert backend.model == "kimi-k3"
    assert backend.using_openrouter is False


def test_legacy_kimi_key_still_accepted(monkeypatch):
    monkeypatch.setenv("KIMI_API_KEY", "sk-legacy")
    assert resolve_backend("kimi").api_key == "sk-legacy"


def test_moonshot_alias_resolves_to_kimi(monkeypatch):
    monkeypatch.setenv("MOONSHOT_API_KEY", "sk-x")
    assert resolve_backend("moonshot").provider == "kimi"


def test_falls_back_to_openrouter_when_provider_key_missing(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-1")
    backend = resolve_backend("kimi")
    assert backend.using_openrouter is True
    assert backend.base_url == "https://openrouter.ai/api/v1"
    assert backend.model == "moonshotai/kimi-k2.6"


def test_gpt5_prefers_openrouter_even_with_provider_key(monkeypatch):
    """gpt-5.x needs OpenAI org verification, so route it via OpenRouter."""
    monkeypatch.setenv("ARK_API_KEY", "sk-ark")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-2")
    backend = resolve_backend("doubao", model="gpt-5.6-luna")
    assert backend.using_openrouter is True
    assert backend.model == "openai/gpt-5.6-luna"


def test_explicit_openai_provider_is_not_hijacked_for_gpt5(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-3")
    backend = resolve_backend("openai", model="gpt-5.6-luna")
    assert backend.using_openrouter is False
    assert backend.base_url == "https://api.openai.com/v1"


def test_ollama_needs_no_key():
    backend = resolve_backend("ollama")
    assert backend.base_url == "http://localhost:11434/v1"
    assert backend.api_key  # non-empty placeholder for the OpenAI client
    assert backend.using_openrouter is False


def test_base_url_override(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://192.168.1.5:11434/v1")
    assert resolve_backend("ollama").base_url == "http://192.168.1.5:11434/v1"


def test_explicit_model_overrides_default(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-4")
    backend = resolve_backend("openrouter", model="google/gemma-4-31b-it:free")
    assert backend.model == "google/gemma-4-31b-it:free"


def test_missing_key_error_names_the_variables():
    with pytest.raises(ValueError) as exc:
        resolve_backend("kimi")
    message = str(exc.value)
    assert "MOONSHOT_API_KEY" in message
    assert "OPENROUTER_API_KEY" in message
    assert "ollama" in message  # points at the zero-cost path


def test_unknown_provider_lists_supported_ones():
    with pytest.raises(ValueError) as exc:
        resolve_backend("not-a-provider")
    assert "Supported:" in str(exc.value)


def test_backend_unpacks_like_the_old_tuple(monkeypatch):
    monkeypatch.setenv("MOONSHOT_API_KEY", "sk-m")
    api_key, base_url, model, using_openrouter = resolve_backend("kimi")
    assert (api_key, model, using_openrouter) == ("sk-m", "kimi-k3", False)
    assert base_url.startswith("https://")


# --- backwards-compatible shim ---------------------------------------------


def test_shim_prefers_primary_key():
    assert resolve_llm_backend("sk-primary", "https://example/v1", "kimi-k3") == (
        "sk-primary",
        "https://example/v1",
        "kimi-k3",
        False,
    )


def test_shim_falls_back_to_openrouter(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-5")
    key, base_url, model, using = resolve_llm_backend("", "https://example/v1", "kimi-k3")
    assert (key, using, model) == ("sk-or-5", True, "moonshotai/kimi-k2.6")
    assert base_url == "https://openrouter.ai/api/v1"


def test_shim_raises_without_any_key():
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        resolve_llm_backend("", "https://example/v1", "kimi-k3")


# --- registry invariants ----------------------------------------------------


def test_every_provider_has_key_vars_unless_local():
    for name, spec in PROVIDERS.items():
        if spec.requires_key:
            assert spec.key_vars, f"{name} requires a key but declares no env var"


def test_supported_providers_covers_registry_and_aliases():
    """Chapter CLIs build --provider choices from this, so a new registry entry
    must be selectable without touching argparse."""
    for name in PROVIDERS:
        assert name in SUPPORTED_PROVIDERS
    for alias in ("moonshot", "ark", "google"):
        assert alias in SUPPORTED_PROVIDERS
    assert "ollama" in SUPPORTED_PROVIDERS
    assert "openai" in SUPPORTED_PROVIDERS
    assert "gemini" in SUPPORTED_PROVIDERS


def test_fallback_key_is_not_reusable_as_a_provider_key(monkeypatch):
    """A resolved fallback backend carries the OpenRouter key, not the
    provider's own. Callers that re-resolve must pass an empty key instead,
    or an OpenRouter key gets sent to the provider's endpoint."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-fallback")
    fallback = resolve_backend("gemini")
    assert fallback.using_openrouter is True
    assert fallback.api_key == "sk-or-fallback"

    # Re-resolving with that key would wrongly treat it as Gemini's own.
    wrong = resolve_backend("gemini", api_key=fallback.api_key)
    assert wrong.using_openrouter is False
    assert wrong.base_url.startswith("https://generativelanguage")

    # Passing an empty key keeps the fallback intact.
    right = resolve_backend("gemini", api_key="")
    assert right.using_openrouter is True
    assert right.base_url == "https://openrouter.ai/api/v1"


@pytest.mark.parametrize(
    "override,expected",
    [
        ("gpt-4o", "openai/gpt-4o"),
        ("claude-sonnet-4", "anthropic/claude-sonnet-4.6"),
        ("deepseek-v4-flash", "deepseek/deepseek-v4-flash"),
        # Already namespaced ids pass through untouched.
        ("google/gemma-4-26b-a4b-it:free", "google/gemma-4-26b-a4b-it:free"),
    ],
)
def test_direct_openrouter_maps_bare_model_ids(monkeypatch, override, expected):
    """Selecting openrouter directly still needs namespaced ids, so a bare
    override is mapped the same way as on the fallback path."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-direct")
    assert resolve_backend("openrouter", model=override).model == expected


def test_keyless_provider_resolves_without_any_key():
    """Config.validate and similar callers must not treat a keyless provider
    as unconfigured -- ollama needs no key at all."""
    backend = resolve_backend("ollama")
    assert backend.provider == "ollama"
    assert PROVIDERS["ollama"].requires_key is False
    # No key set anywhere, yet resolution succeeds rather than raising.
    assert PROVIDERS["ollama"].api_key() == ""
