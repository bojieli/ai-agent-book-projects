"""The provider registry: which backends exist and what they are called.

This module is pure data plus lookup. Adding a provider means adding one entry
to :data:`PROVIDERS` and nothing else -- chapter CLIs build their
``--provider`` choices from :data:`SUPPORTED_PROVIDERS`, so a new entry becomes
selectable without touching any argparse code.

Resolution *policy* -- which provider wins, when to fall back -- lives in
:mod:`agentbook.providers.resolution`, not here.
"""

from __future__ import annotations

from .models import Provider
from .openrouter import OPENROUTER_BASE_URL, OPENROUTER_DEFAULT_MODEL

__all__ = [
    "PROVIDERS",
    "SUPPORTED_PROVIDERS",
    "canonical_provider",
    "lookup",
    "supported_providers",
]

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
        # Resells many vendors' models, so ids must be namespaced.
        namespaces_models=True,
    ),
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

# Provider names used interchangeably in the chapters, mapped to canonical ones.
_ALIASES = {"moonshot": "kimi", "ark": "doubao", "google": "gemini"}

# Every accepted name, canonical plus aliases. Chapter CLIs use this for their
# --provider choices so a new registry entry is immediately selectable instead
# of being rejected by argparse.
#
# Computed once at import: PROVIDERS is a module-level table edited in source,
# not registered at runtime. Anything mutating PROVIDERS after import (tests
# do, to exercise hypothetical providers) must read supported_providers()
# instead, which recomputes.
SUPPORTED_PROVIDERS: tuple[str, ...] = tuple(sorted(set(PROVIDERS) | set(_ALIASES)))


def supported_providers() -> tuple[str, ...]:
    """Return every accepted provider name, canonical plus aliases.

    Prefer the :data:`SUPPORTED_PROVIDERS` constant unless
    :data:`PROVIDERS` may have been modified since import.

    Returns:
        Sorted provider names and aliases, recomputed from the live table.
    """
    return tuple(sorted(set(PROVIDERS) | set(_ALIASES)))


def canonical_provider(provider: str) -> str:
    """Normalise a provider name, resolving aliases.

    Args:
        provider: A provider name or alias, e.g. ``"moonshot"`` or ``"Kimi"``.
            Case and surrounding whitespace are ignored. ``None`` is tolerated.

    Returns:
        The canonical name, e.g. ``"kimi"``. Names that are not known aliases
        are returned lowercased but otherwise unchanged, so callers can still
        look them up and get a sensible error for genuinely unknown providers.
    """
    key = (provider or "").strip().lower()
    return _ALIASES.get(key, key)


def lookup(provider: str) -> Provider:
    """Find the :class:`~agentbook.providers.models.Provider` for a name.

    Args:
        provider: A provider name or alias.

    Returns:
        The registered provider specification.

    Raises:
        ValueError: If the name matches no registry entry or alias. The message
            lists the supported names.
    """
    key = canonical_provider(provider)
    if key not in PROVIDERS:
        supported = ", ".join(sorted(PROVIDERS))
        raise ValueError(f"Unsupported provider: {provider!r}. Supported: {supported}")
    return PROVIDERS[key]
