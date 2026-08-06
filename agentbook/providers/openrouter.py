"""OpenRouter endpoint constants and model-id mapping.

OpenRouter is the universal fallback: it speaks the OpenAI protocol and hosts
models from many vendors, so any chapter can run against it with a single key.
The catch is that it namespaces model ids (``openai/gpt-4o`` rather than
``gpt-4o``), which is what :func:`map_model_to_openrouter` translates.

Everything OpenRouter-specific lives here, so a change to its ids or endpoint
touches exactly one module.
"""

from __future__ import annotations

import os

__all__ = [
    "OPENROUTER_BASE_URL",
    "OPENROUTER_DEFAULT_MODEL",
    "ZERO_COST_HINT",
    "is_openrouter_key",
    "map_model_to_openrouter",
    "openrouter_base_url",
    "openrouter_key",
]

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_DEFAULT_MODEL = "openai/gpt-5.6-luna"

# Appended to every "no key configured" error so the way out of the problem is
# stated once rather than copied into each message.
ZERO_COST_HINT = (
    "For a zero-cost setup use provider 'ollama' (local, no key) or "
    "OPENROUTER_MODEL with a ':free' model id."
)


def openrouter_key() -> str:
    """Read the OpenRouter API key from the environment.

    Returns:
        The value of ``OPENROUTER_API_KEY``, stripped, or ``""`` when unset.
    """
    return os.getenv("OPENROUTER_API_KEY", "").strip()


def is_openrouter_key(api_key: str) -> bool:
    """Report whether a credential looks like an OpenRouter key.

    OpenRouter issues keys under the ``sk-or-`` prefix, so a key the reader
    pasted can usually be attributed without asking them which service it came
    from. This is a naming convention rather than a guarantee, which bounds
    where the answer may be used.

    Intended for callers that accept a key of unknown origin -- a CLI taking
    ``--api-key``, say -- and must pick which provider to resolve. It is
    deliberately *not* used by :func:`~agentbook.providers.resolve_backend`,
    whose ``api_key`` argument means "this provider's credential"; inferring
    routing from the value there would silently override the caller and send a
    provider's key to the wrong host when a prefix collides.

    Args:
        api_key: A credential of unknown origin. ``None`` and ``""`` are
            tolerated and report ``False``.

    Returns:
        ``True`` if the key carries OpenRouter's prefix.
    """
    return (api_key or "").strip().startswith("sk-or-")


def openrouter_base_url() -> str:
    """Return the OpenRouter endpoint, honouring an environment override.

    Returns:
        The value of ``OPENROUTER_BASE_URL`` if set and non-empty, otherwise
        the default public endpoint.
    """
    return os.getenv("OPENROUTER_BASE_URL", "").strip() or OPENROUTER_BASE_URL


def map_model_to_openrouter(model: str, *, substitute_unknown: bool = False) -> str:
    """Map a bare model id to the equivalent OpenRouter model id.

    Mapping rules, applied in order:

    * ids already containing ``/`` are returned unchanged (already OpenRouter form)
    * ``gpt-*`` / ``o1-*`` / ``o3-*`` / ``o4-*`` become ``openai/<id>``
    * ``claude-*`` becomes the matching Anthropic id
    * ``kimi-*`` becomes ``moonshotai/kimi-k2.6`` (kimi-k3 is not hosted)
    * ``deepseek-*`` becomes ``deepseek/<id>``
    * ``qwen-*`` / ``qwen2*`` / ``qwen3*`` becomes ``qwen/<id>``
    What to do with an unmapped id -- a native one such as ``doubao-*`` or
    ``glm-*``, which OpenRouter does not reliably host -- depends on why the
    caller is mapping, so it is the caller's decision rather than a fixed rule
    here. Talking to an aggregator that *requires* a namespaced id, a working
    default beats a request that cannot succeed. Rerouting a request the reader
    already aimed at a named model, silently answering as a different vendor's
    model is worse than failing.

    Args:
        model: A bare or already-namespaced model id. ``None`` and ``""`` are
            tolerated.
        substitute_unknown: When ``True``, an unmapped id becomes
            ``OPENROUTER_MODEL`` or the package default. When ``False`` it is
            returned unchanged, to be rejected by OpenRouter under the name the
            reader actually asked for.

    Returns:
        An OpenRouter model id, or the unchanged input for an unmapped id when
        ``substitute_unknown`` is ``False``.
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
    if ml.startswith("qwen"):
        return "qwen/" + m
    if substitute_unknown:
        return os.getenv("OPENROUTER_MODEL", "").strip() or OPENROUTER_DEFAULT_MODEL
    return m
