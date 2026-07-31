"""Backwards-compatible shim for the pre-registry chapter helper.

Before the shared registry existed, three chapter experiments each carried
their own copy of ``resolve_llm_backend``. It is still imported by three
chapter modules and called by two of them, so it stays until all of them are
migrated:

* ``chapter1/web-search-agent/agent.py`` -- calls it
* ``chapter1/learning-from-experience/llm_agent.py`` -- calls it
* ``chapter1/context/config.py`` -- re-exports it for its own importers

Deleting this function therefore breaks ``chapter1/context`` at import time
even though that module never calls it.

It cannot simply delegate to :func:`~agentbook.providers.resolution.resolve_backend`:
callers pass a bare ``base_url`` with no provider name, which the registry has
no way to express. What it *can* share is the OpenRouter construction, so the
two code paths cannot drift apart on the part that matters.
"""

from __future__ import annotations

from .openrouter import ZERO_COST_HINT, openrouter_key
from .resolution import build_openrouter_backend

__all__ = ["resolve_llm_backend"]

_NO_KEY_MESSAGE = (
    "No API key found. Set a provider key (SILICONFLOW_API_KEY / ARK_API_KEY / "
    "MOONSHOT_API_KEY / DEEPSEEK_API_KEY / ZHIPU_API_KEY / OPENAI_API_KEY / "
    "GEMINI_API_KEY) or OPENROUTER_API_KEY (universal fallback). " + ZERO_COST_HINT
)


def resolve_llm_backend(
    primary_key: str | None,
    primary_base_url: str,
    model: str,
) -> tuple[str, str, str, bool]:
    """Resolve a backend from a loose key/URL pair, as the old helper did.

    Prefer :func:`~agentbook.providers.resolution.resolve_backend`, which knows
    the provider registry and therefore reports far better errors. This exists
    for call sites that only have a base URL and no provider name.

    Args:
        primary_key: The caller's own API key. Falsy values trigger the
            OpenRouter fallback.
        primary_base_url: Endpoint matching ``primary_key``.
        model: Requested model id. Mapped to an OpenRouter id when the request
            is rerouted, and passed through untouched otherwise.

    Returns:
        A plain ``(api_key, base_url, model, using_openrouter)`` tuple. Callers
        compare this against tuple literals, so it deliberately stays a tuple
        rather than becoming a :class:`~agentbook.providers.models.Backend`.

    Raises:
        ValueError: If neither ``primary_key`` nor ``OPENROUTER_API_KEY`` is
            set.
    """
    fallback_key = openrouter_key()

    # gpt-5.x needs OpenAI org verification on the direct API; prefer OpenRouter
    # even when the caller supplied their own key.
    if fallback_key and str(model or "").lower().startswith("gpt-5"):
        return tuple(build_openrouter_backend(model, fallback_key))

    if primary_key:
        return primary_key, primary_base_url, model, False

    if fallback_key:
        return tuple(build_openrouter_backend(model, fallback_key))

    raise ValueError(_NO_KEY_MESSAGE)
