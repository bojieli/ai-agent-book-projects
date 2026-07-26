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


def openrouter_base_url() -> str:
    """Return the OpenRouter endpoint, honouring an environment override.

    Returns:
        The value of ``OPENROUTER_BASE_URL`` if set and non-empty, otherwise
        the default public endpoint.
    """
    return os.getenv("OPENROUTER_BASE_URL", "").strip() or OPENROUTER_BASE_URL


def map_model_to_openrouter(model: str) -> str:
    """Map a bare model id to the equivalent OpenRouter model id.

    Mapping rules, applied in order:

    * ids already containing ``/`` are returned unchanged (already OpenRouter form)
    * ``gpt-*`` / ``o1-*`` / ``o3-*`` / ``o4-*`` become ``openai/<id>``
    * ``claude-*`` becomes the matching Anthropic id
    * ``kimi-*`` becomes ``moonshotai/kimi-k2.6`` (kimi-k3 is not hosted)
    * ``deepseek-*`` becomes ``deepseek/<id>``

    Args:
        model: A bare or already-namespaced model id. ``None`` and ``""`` are
            tolerated and fall through to the default.

    Returns:
        An OpenRouter-valid model id. Ids with no known mapping -- native ones
        such as ``doubao-*`` and ``glm-*``, which OpenRouter does not reliably
        host -- fall back to ``OPENROUTER_MODEL`` or the package default.
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
