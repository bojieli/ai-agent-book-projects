"""Tests for the shared provider registry.

Focus is behaviour parity with the three per-chapter copies this module
replaces, plus the resolution rules that are easy to regress.
"""

import dataclasses

import pytest

from agentbook.providers import (
    OPENROUTER_DEFAULT_MODEL,
    PROVIDERS,
    SUPPORTED_PROVIDERS,
    Provider,
    is_openrouter_key,
    map_model_to_openrouter,
    resolve_backend,
    resolve_llm_backend,
)
from agentbook.providers.registry import supported_providers
from agentbook.providers.resolution import build_openrouter_backend

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
        ("qwen-2.5-72b-instruct", "qwen/qwen-2.5-72b-instruct"),
        ("qwen2.5-coder-32b", "qwen/qwen2.5-coder-32b"),
    ],
)
def test_map_model_to_openrouter(model, expected):
    assert map_model_to_openrouter(model) == expected


def test_unknown_model_falls_back_to_openrouter_model_env(monkeypatch):
    """Substituting a working default is opt-in, for callers that cannot send
    an unmapped id at all."""
    monkeypatch.setenv("OPENROUTER_MODEL", "google/gemma-4-31b-it:free")
    mapped = map_model_to_openrouter("doubao-seed-1-6", substitute_unknown=True)
    assert mapped == "google/gemma-4-31b-it:free"



def test_unknown_model_falls_back_to_default_when_openrouter_model_env_is_empty(monkeypatch):
    """Empty or whitespace OPENROUTER_MODEL must fall back to the package default.

    Locks out regression where OPENROUTER_MODEL set to empty string or whitespace
    bypassed OPENROUTER_DEFAULT_MODEL when substitute_unknown is True.
    """
    monkeypatch.setenv("OPENROUTER_MODEL", "   ")
    mapped = map_model_to_openrouter("doubao-seed-1-6", substitute_unknown=True)
    assert mapped == OPENROUTER_DEFAULT_MODEL

def test_unknown_model_is_returned_unchanged_by_default(monkeypatch):
    """The default keeps the reader's model id, so an unhosted one is rejected
    by name rather than silently answered by a different vendor's model."""
    monkeypatch.setenv("OPENROUTER_MODEL", "google/gemma-4-31b-it:free")
    assert map_model_to_openrouter("doubao-seed-1-6") == "doubao-seed-1-6"


# --- provider resolution ----------------------------------------------------


def test_direct_provider_key_is_used(monkeypatch):
    monkeypatch.setenv("MOONSHOT_API_KEY", "test-moonshot-key")
    backend = resolve_backend("kimi")
    assert backend.api_key == "test-moonshot-key"
    assert backend.base_url == "https://api.moonshot.cn/v1"
    assert backend.model == "kimi-k3"
    assert backend.using_openrouter is False


def test_legacy_kimi_key_still_accepted(monkeypatch):
    monkeypatch.setenv("KIMI_API_KEY", "test-legacy-key")
    assert resolve_backend("kimi").api_key == "test-legacy-key"


def test_moonshot_alias_resolves_to_kimi(monkeypatch):
    monkeypatch.setenv("MOONSHOT_API_KEY", "test-moonshot-key")
    assert resolve_backend("moonshot").provider == "kimi"


def test_falls_back_to_openrouter_when_provider_key_missing(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key-1")
    backend = resolve_backend("kimi")
    assert backend.using_openrouter is True
    assert backend.base_url == "https://openrouter.ai/api/v1"
    assert backend.model == "moonshotai/kimi-k2.6"


def test_gpt5_prefers_openrouter_even_with_provider_key(monkeypatch):
    """gpt-5.x needs OpenAI org verification, so route it via OpenRouter."""
    monkeypatch.setenv("ARK_API_KEY", "test-ark-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key-2")
    backend = resolve_backend("doubao", model="gpt-5.6-luna")
    assert backend.using_openrouter is True
    assert backend.model == "openai/gpt-5.6-luna"


def test_explicit_openai_provider_is_not_hijacked_for_gpt5(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key-3")
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
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key-4")
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
    monkeypatch.setenv("MOONSHOT_API_KEY", "test-moonshot-key")
    api_key, base_url, model, using_openrouter = resolve_backend("kimi")
    assert (api_key, model, using_openrouter) == ("test-moonshot-key", "kimi-k3", False)
    assert base_url.startswith("https://")


# --- backwards-compatible shim ---------------------------------------------


def test_shim_prefers_primary_key():
    assert resolve_llm_backend("test-primary-key", "https://example/v1", "kimi-k3") == (
        "test-primary-key",
        "https://example/v1",
        "kimi-k3",
        False,
    )


def test_shim_falls_back_to_openrouter(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key-5")
    key, base_url, model, using = resolve_llm_backend("", "https://example/v1", "kimi-k3")
    assert (key, using, model) == ("test-openrouter-key-5", True, "moonshotai/kimi-k2.6")
    assert base_url == "https://openrouter.ai/api/v1"


def test_shim_falls_back_to_openrouter_default_model_when_model_is_none(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key-6")
    key, base_url, model, using = resolve_llm_backend("", "https://example/v1", None)
    assert (key, using, model) == ("test-openrouter-key-6", True, OPENROUTER_DEFAULT_MODEL)
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
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-fallback-key")
    fallback = resolve_backend("gemini")
    assert fallback.using_openrouter is True
    assert fallback.api_key == "test-openrouter-fallback-key"

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
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-direct-key")
    assert resolve_backend("openrouter", model=override).model == expected


def test_keyless_provider_resolves_without_any_key():
    """Config.validate and similar callers must not treat a keyless provider
    as unconfigured -- ollama needs no key at all."""
    backend = resolve_backend("ollama")
    assert backend.provider == "ollama"
    assert PROVIDERS["ollama"].requires_key is False
    # No key set anywhere, yet resolution succeeds rather than raising.
    assert PROVIDERS["ollama"].api_key() == ""


def test_explicit_openrouter_key_wins_over_env_for_gpt5(monkeypatch):
    """An explicit key for the openrouter provider is an OpenRouter credential,
    so it must not be silently replaced by OPENROUTER_API_KEY."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-env-key")
    backend = resolve_backend("openrouter", model="gpt-5.6-luna", api_key="test-explicit-key")
    assert backend.using_openrouter is True
    assert backend.api_key == "test-explicit-key"


def test_explicit_openrouter_key_works_without_env(monkeypatch):
    backend = resolve_backend("openrouter", model="gpt-5.6-luna", api_key="test-only-key")
    assert backend.api_key == "test-only-key"
    assert backend.model == "openai/gpt-5.6-luna"


def test_other_providers_key_is_not_forwarded_to_openrouter(monkeypatch):
    """A doubao key is not an OpenRouter credential; the gpt-5 reroute must use
    the OpenRouter key, never the provider's own."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-env-key")
    backend = resolve_backend("doubao", model="gpt-5.6-luna", api_key="test-ark-explicit-key")
    assert backend.using_openrouter is True
    assert backend.api_key == "test-openrouter-env-key"


# --- extensibility: a registry-only edit must be sufficient -----------------
#
# registry.py promises that adding a provider means adding one entry and
# nothing else. These pin that promise for the cases that previously needed an
# edit to the resolver as well.


@pytest.fixture
def register_provider(monkeypatch):
    """Register a temporary provider, removed again after the test.

    Returns:
        A callable taking a name plus ``Provider`` field overrides, based on
        the ``openrouter`` entry.
    """

    def _register(name: str, **overrides) -> Provider:
        spec = dataclasses.replace(PROVIDERS["openrouter"], name=name, **overrides)
        monkeypatch.setitem(PROVIDERS, name, spec)
        return spec

    return _register


def test_second_aggregator_namespaces_models(register_provider):
    """A new aggregator must map bare model ids without touching resolution.py.

    Before ``namespaces_models`` existed this was gated on the literal provider
    name, so any other aggregator silently sent un-namespaced ids and 404'd at
    request time rather than failing in config.
    """
    register_provider(
        "together",
        base_url="https://api.together.xyz/v1",
        key_vars=("TOGETHER_API_KEY",),
        namespaces_models=True,
    )
    backend = resolve_backend("together", model="gpt-4o", api_key="test-together-key")
    assert backend.model == "openai/gpt-4o"
    # The explicit key belongs to that aggregator, so it must be honoured...
    assert backend.api_key == "test-together-key"
    # ...and sent to that aggregator. Sharing OpenRouter's id format must not
    # drag along OpenRouter's endpoint, or the credential goes to the wrong host.
    assert backend.base_url == "https://api.together.xyz/v1"
    assert backend.using_openrouter is False


def test_other_aggregator_key_is_not_treated_as_an_openrouter_key(register_provider):
    """A non-OpenRouter aggregator's key must not enable the gpt-5 reroute.

    ``namespaces_models`` describes id formatting, not credential
    compatibility: routing a Together key to OpenRouter fails authentication.
    """
    register_provider(
        "together",
        base_url="https://api.together.xyz/v1",
        key_vars=("TOGETHER_API_KEY",),
        namespaces_models=True,
    )
    backend = resolve_backend("together", model="gpt-5.6-luna", api_key="test-together-key")
    assert backend.using_openrouter is False
    assert backend.base_url == "https://api.together.xyz/v1"
    assert backend.api_key == "test-together-key"


def test_openrouter_still_routes_gpt5_with_an_explicit_key(monkeypatch):
    """The real OpenRouter provider keeps its explicit-key gpt-5 behaviour."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    backend = resolve_backend("openrouter", model="gpt-5.6-luna", api_key="test-openrouter-key")
    assert backend.using_openrouter is True
    assert backend.api_key == "test-openrouter-key"
    assert backend.model == "openai/gpt-5.6-luna"


def test_single_vendor_provider_does_not_namespace_models(register_provider):
    """The converse: a non-aggregator must receive the id it was given."""
    register_provider(
        "vendorx",
        base_url="https://api.vendorx.test/v1",
        key_vars=("VENDORX_API_KEY",),
        namespaces_models=False,
    )
    backend = resolve_backend("vendorx", model="gpt-4o", api_key="test-vendorx-key")
    assert backend.model == "gpt-4o"


def test_keyless_aggregator_still_gets_a_placeholder_key(register_provider):
    """Every backend needs a non-empty key: the OpenAI client rejects ``""``.

    The aggregator branch used to skip the placeholder fallback, so a keyless
    aggregator resolved to an empty credential.
    """
    register_provider("keyless_agg", requires_key=False, key_vars=(), namespaces_models=True)
    assert resolve_backend("keyless_agg", model="gpt-4o").api_key


def test_openrouter_backend_never_carries_an_empty_key():
    """The OpenRouter builder must apply the placeholder too.

    Covers ``build_openrouter_backend`` directly: the test above now reaches
    the plain-provider branch instead, so without this the builder's own
    fallback is unguarded -- deleting it breaks no test even though the path
    is reachable via a keyless provider that routes to OpenRouter.
    """
    assert build_openrouter_backend("gpt-4o", "").api_key
    assert build_openrouter_backend("gpt-4o", "test-real-key").api_key == "test-real-key"


def test_reroute_keeps_an_unmapped_model_id(monkeypatch):
    """Falling back for credential reasons must not change which model runs.

    A reader who named a native model and has only an OpenRouter key should see
    that model rejected, not silently answered by whatever OPENROUTER_MODEL
    happens to be -- the request would otherwise succeed against a different
    vendor entirely.
    """
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-env-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "google/gemma-4-31b-it:free")
    backend = resolve_backend("doubao", model="doubao-seed-1-6")
    assert backend.using_openrouter is True
    assert backend.model == "doubao-seed-1-6"


def test_aggregator_substitutes_an_unmapped_model_id(register_provider, monkeypatch):
    """The namespacing path keeps substituting: a bare unmapped id cannot be
    requested from an aggregator at all, so a working default beats a certain
    404."""
    monkeypatch.setenv("OPENROUTER_MODEL", "google/gemma-4-31b-it:free")
    register_provider(
        "together",
        base_url="https://api.together.xyz/v1",
        key_vars=("TOGETHER_API_KEY",),
        namespaces_models=True,
    )
    backend = resolve_backend("together", model="doubao-seed-1-6", api_key="test-together-key")
    assert backend.model == "google/gemma-4-31b-it:free"


@pytest.mark.parametrize(
    "api_key,expected",
    [
        ("sk-or-v1-abc", True),
        ("  sk-or-v1-abc  ", True),
        ("sk-proj-abc", False),
        ("test-moonshot-key", False),
        ("", False),
        (None, False),
    ],
)
def test_is_openrouter_key(api_key, expected):
    assert is_openrouter_key(api_key) is expected


def test_is_openrouter_key_does_not_influence_resolution(monkeypatch):
    """Attribution is for callers choosing a provider, not for the resolver.

    ``api_key`` means "this provider's credential"; honouring the prefix here
    would override the caller and contradict
    ``test_fallback_key_is_not_reusable_as_a_provider_key``.
    """
    backend = resolve_backend("kimi", model="kimi-k2.6", api_key="sk-or-v1-abc")
    assert backend.using_openrouter is False
    assert backend.base_url == "https://api.moonshot.cn/v1"


def test_supported_providers_helper_sees_late_registrations(register_provider):
    """``SUPPORTED_PROVIDERS`` is an import-time snapshot; the helper is live."""
    register_provider("latecomer", key_vars=("LATE_API_KEY",))
    assert "latecomer" not in SUPPORTED_PROVIDERS
    assert "latecomer" in supported_providers()


def test_placeholder_key_is_not_a_provider_name():
    """The placeholder credential must not be mistakable for an identity.

    It was once the string ``"ollama"``, making ``backend.api_key`` equal to
    ``backend.provider`` and indistinguishable from a real user-set key.
    """
    backend = resolve_backend("ollama")
    assert backend.api_key
    assert backend.api_key != backend.provider
    assert backend.api_key not in PROVIDERS


def test_openrouter_default_model_honours_openrouter_model_env(monkeypatch):
    """resolve_backend("openrouter") with no explicit model must use
    OPENROUTER_MODEL (the documented ':free' zero-cost selector), not the paid
    OPENROUTER_DEFAULT_MODEL."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "google/gemma-4-31b-it:free")
    backend = resolve_backend("openrouter")
    assert backend.using_openrouter is True
    assert backend.model == "google/gemma-4-31b-it:free"


def test_openrouter_explicit_model_still_wins_over_env(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "google/gemma-4-31b-it:free")
    backend = resolve_backend("openrouter", model="gpt-4o")
    assert backend.model == "openai/gpt-4o"
