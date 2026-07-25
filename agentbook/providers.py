"""Single source of truth for LLM provider resolution.

Every chapter experiment talks to an OpenAI-compatible endpoint. What differs
per provider is only the base URL, the default model id, and which environment
variable holds the key -- so all of that lives here instead of being repeated
in each experiment.

Typical use::

    from agentbook.providers import resolve_backend

    backend = resolve_backend("kimi")
    client = OpenAI(api_key=backend.api_key, base_url=backend.base_url)
    ...
    client.chat.completions.create(model=backend.model, ...)

Adding a provider is one entry in ``PROVIDERS`` below.

Free / zero-cost options:

* ``ollama``   -- runs models on your own machine, no API key, no cost.
* ``openrouter`` with a ``:free`` model id, e.g.::

      OPENROUTER_API_KEY=sk-or-v1-...
      OPENROUTER_MODEL=google/gemma-4-31b-it:free

  The model runs on OpenRouter's servers, so a modest laptop is fine.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

__all__ = [
    "PROVIDERS",
    "SUPPORTED_PROVIDERS",
    "Backend",
    "Provider",
    "canonical_provider",
    "map_model_to_openrouter",
    "resolve_backend",
    "resolve_llm_backend",
]

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_DEFAULT_MODEL = "openai/gpt-5.6-luna"


@dataclass(frozen=True)
class Provider:
    """Static description of an OpenAI-compatible backend."""

    name: str
    base_url: str
    default_model: str
    # Environment variables holding the API key, tried in order. The first
    # non-empty one wins; later entries exist for backwards compatibility.
    key_vars: tuple[str, ...] = ()
    # Base URL can be overridden per deployment (self-hosted, regional, ...).
    base_url_var: str | None = None
    # Local runtimes accept any placeholder key, so a missing key is not an error.
    requires_key: bool = True

    def api_key(self) -> str:
        for var in self.key_vars:
            value = os.getenv(var, "").strip()
            if value:
                return value
        return ""

    def resolved_base_url(self) -> str:
        if self.base_url_var:
            return os.getenv(self.base_url_var, "").strip() or self.base_url
        return self.base_url


# --- the registry -----------------------------------------------------------
#
# Adding a provider means adding one entry here; nothing else changes.

PROVIDERS: dict[str, Provider] = {
    "siliconflow": Provider(
        name="siliconflow",
        base_url="https://api.siliconflow.cn/v1",
        default_model="Qwen/Qwen3.5-397B-A17B",
        key_vars=("SILICONFLOW_API_KEY",),
    ),
    "doubao": Provider(
        name="doubao",
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        default_model="doubao-seed-1-6-thinking-250715",
        key_vars=("ARK_API_KEY",),
    ),
    "kimi": Provider(
        name="kimi",
        base_url="https://api.moonshot.cn/v1",
        default_model="kimi-k3",
        # KIMI_API_KEY kept for backwards compatibility.
        key_vars=("MOONSHOT_API_KEY", "KIMI_API_KEY"),
        base_url_var="KIMI_BASE_URL",
    ),
    "deepseek": Provider(
        name="deepseek",
        base_url="https://api.deepseek.com",
        # V4 Flash is OpenAI-compatible with tool calling + thinking mode.
        # Legacy deepseek-chat / deepseek-reasoner aliases deprecated 2026-07-24.
        default_model="deepseek-v4-flash",
        key_vars=("DEEPSEEK_API_KEY",),
        base_url_var="DEEPSEEK_BASE_URL",
    ),
    "zhipu": Provider(
        name="zhipu",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        default_model="glm-5.2",
        key_vars=("ZHIPU_API_KEY",),
    ),
    "openrouter": Provider(
        name="openrouter",
        base_url=OPENROUTER_BASE_URL,
        default_model=OPENROUTER_DEFAULT_MODEL,
        key_vars=("OPENROUTER_API_KEY",),
        base_url_var="OPENROUTER_BASE_URL",
    ),
    # --- added by the shared registry ---
    "openai": Provider(
        name="openai",
        base_url="https://api.openai.com/v1",
        default_model="gpt-4o",
        key_vars=("OPENAI_API_KEY",),
        base_url_var="OPENAI_BASE_URL",
    ),
    "gemini": Provider(
        name="gemini",
        # Google exposes an OpenAI-compatible endpoint; the free tier is
        # generous enough for most chapter experiments.
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        default_model="gemini-2.5-flash",
        key_vars=("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    ),
    "ollama": Provider(
        name="ollama",
        base_url="http://localhost:11434/v1",
        default_model="qwen3:8b",
        # Ollama ignores the key but the OpenAI client requires a non-empty one.
        key_vars=("OLLAMA_API_KEY",),
        base_url_var="OLLAMA_BASE_URL",
        requires_key=False,
    ),
}

# Aliases for provider names used interchangeably in the chapters.
_ALIASES = {"moonshot": "kimi", "ark": "doubao", "google": "gemini"}

# Every accepted name, canonical plus aliases. Chapter CLIs use this for their
# --provider choices so a new registry entry is immediately selectable instead
# of being rejected by argparse.
SUPPORTED_PROVIDERS: tuple[str, ...] = tuple(sorted(set(PROVIDERS) | set(_ALIASES)))


def canonical_provider(provider: str) -> str:
    """Normalise a provider name, resolving aliases (``moonshot`` -> ``kimi``).

    Returns the name unchanged when it is not a known alias, so callers can
    still look it up and get a KeyError for genuinely unknown providers.
    """
    key = (provider or "").strip().lower()
    return _ALIASES.get(key, key)


def _lookup(provider: str) -> Provider:
    key = canonical_provider(provider)
    if key not in PROVIDERS:
        supported = ", ".join(sorted(PROVIDERS))
        raise ValueError(f"Unsupported provider: {provider!r}. Supported: {supported}")
    return PROVIDERS[key]


def map_model_to_openrouter(model: str) -> str:
    """Map a bare model id to an OpenRouter model id.

    - ids already containing '/' are left as-is (already OpenRouter form)
    - gpt-*/o1-*/o3-*/o4-* -> ``openai/<id>``
    - claude-*             -> the matching Anthropic id
    - kimi-*               -> ``moonshotai/kimi-k2.6`` (kimi-k3 is not hosted)
    - deepseek-*           -> ``deepseek/<id>``
    - anything else falls back to ``OPENROUTER_MODEL``, since native ids such as
      doubao-* and glm-* are not reliably available on OpenRouter.
    """
    m = (model or "").strip()
    if "/" in m:
        return m
    ml = m.lower()
    if ml.startswith(("gpt-", "o1-", "o3-", "o4-")):
        return "openai/" + m
    if ml.startswith("claude-"):
        if "sonnet" in ml:
            return "anthropic/claude-sonnet-4.6"
        if "haiku" in ml:
            return "anthropic/claude-haiku-4.5"
        return "anthropic/claude-opus-4.8"
    if ml.startswith("kimi"):
        return "moonshotai/kimi-k2.6"
    if ml.startswith("deepseek"):
        return "deepseek/" + m
    return os.getenv("OPENROUTER_MODEL", OPENROUTER_DEFAULT_MODEL)


@dataclass(frozen=True)
class Backend:
    """A resolved, ready-to-use OpenAI-compatible endpoint."""

    api_key: str
    base_url: str
    model: str
    provider: str
    using_openrouter: bool

    def __iter__(self):
        """Unpack as ``(api_key, base_url, model, using_openrouter)``."""
        return iter((self.api_key, self.base_url, self.model, self.using_openrouter))


def resolve_backend(
    provider: str,
    model: str | None = None,
    api_key: str | None = None,
) -> Backend:
    """Resolve a provider name into a usable backend.

    Resolution order:

    1. ``gpt-5*`` ids route through OpenRouter when a key is available, because
       the direct OpenAI API requires org verification for them.
    2. If the provider's own key is set (or the provider needs none, e.g.
       Ollama), use the provider directly.
    3. Otherwise fall back to OpenRouter, mapping the model id.
    4. Otherwise raise, naming the variables that would fix it.
    """
    spec = _lookup(provider)
    resolved_model = model or spec.default_model
    key = (api_key or "").strip() or spec.api_key()
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    openrouter_url = os.getenv("OPENROUTER_BASE_URL", "").strip() or OPENROUTER_BASE_URL

    def via_openrouter() -> Backend:
        return Backend(
            api_key=openrouter_key,
            base_url=openrouter_url,
            model=map_model_to_openrouter(resolved_model),
            provider=spec.name,
            using_openrouter=True,
        )

    # gpt-5.x needs OpenAI org verification on the direct API; prefer OpenRouter.
    if openrouter_key and resolved_model.lower().startswith("gpt-5") and spec.name != "openai":
        return via_openrouter()

    if key or not spec.requires_key:
        # Selecting OpenRouter directly still needs namespaced model ids, so a
        # bare override like "gpt-4o" or "claude-sonnet-4" is mapped the same way
        # as it would be on the fallback path.
        direct_model = (
            map_model_to_openrouter(resolved_model)
            if spec.name == "openrouter"
            else resolved_model
        )
        return Backend(
            # Local runtimes still need a non-empty placeholder for the client.
            api_key=key or "ollama",
            base_url=spec.resolved_base_url(),
            model=direct_model,
            provider=spec.name,
            using_openrouter=spec.name == "openrouter",
        )

    if openrouter_key:
        return via_openrouter()

    wanted = " / ".join(spec.key_vars) or "(none)"
    raise ValueError(
        f"No API key found for provider {spec.name!r}. Set {wanted}, "
        "or OPENROUTER_API_KEY as a universal fallback. "
        "For a zero-cost setup use provider 'ollama' (local, no key) or "
        "OPENROUTER_MODEL with a ':free' model id."
    )


def resolve_llm_backend(primary_key, primary_base_url, model):
    """Backwards-compatible shim for the previous per-chapter helper.

    Kept so existing experiment code keeps working unchanged. Prefer
    :func:`resolve_backend`, which knows the provider registry and therefore
    reports far better errors.

    Returns ``(api_key, base_url, model, using_openrouter)``.
    """
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    openrouter_url = os.getenv("OPENROUTER_BASE_URL", "").strip() or OPENROUTER_BASE_URL

    if openrouter_key and str(model or "").lower().startswith("gpt-5"):
        return openrouter_key, openrouter_url, map_model_to_openrouter(model), True
    if primary_key:
        return primary_key, primary_base_url, model, False
    if openrouter_key:
        return openrouter_key, openrouter_url, map_model_to_openrouter(model), True
    raise ValueError(
        "No API key found. Set a provider key (SILICONFLOW_API_KEY / ARK_API_KEY / "
        "MOONSHOT_API_KEY / DEEPSEEK_API_KEY / ZHIPU_API_KEY / OPENAI_API_KEY / "
        "GEMINI_API_KEY) or OPENROUTER_API_KEY (universal fallback). "
        "For a zero-cost setup use provider 'ollama' or a ':free' OpenRouter model."
    )
