"""Resolution policy: turning a provider name into a usable backend.

This module owns the *rules* -- which credential wins, when to reroute through
OpenRouter, what to do when nothing is configured. The registry owns the data
those rules operate on.

The precedence chain is deliberately expressed as one readable sequence in
:func:`resolve_backend`, because the order of its steps is the entire
behaviour: swapping two of them silently changes which endpoint a chapter
talks to.
"""

from __future__ import annotations

from .models import Backend, Provider
from .openrouter import (
    map_model_to_openrouter,
    openrouter_base_url,
    openrouter_key,
)
from .registry import lookup

__all__ = ["build_openrouter_backend", "resolve_backend"]

# Local runtimes ignore the key, but the OpenAI client rejects an empty one.
_PLACEHOLDER_KEY = "ollama"


def build_openrouter_backend(
    model: str,
    api_key: str,
    provider: str = "openrouter",
) -> Backend:
    """Build a backend that routes through OpenRouter.

    Shared by :func:`resolve_backend` and the legacy shim in
    :mod:`agentbook.providers.legacy` so the two cannot drift apart.

    Args:
        model: The requested model id; mapped to its OpenRouter equivalent.
        api_key: The OpenRouter credential to use. Must already be resolved --
            this function does not fall back to the environment.
        provider: The provider that was originally requested. Recorded on the
            backend so callers can report what the user asked for.

    Returns:
        A backend pointing at OpenRouter with ``using_openrouter`` set.
    """
    return Backend(
        api_key=api_key,
        base_url=openrouter_base_url(),
        model=map_model_to_openrouter(model),
        provider=provider,
        using_openrouter=True,
    )


def _needs_openrouter_for_gpt5(spec: Provider, model: str) -> bool:
    """Report whether a gpt-5 request must be rerouted through OpenRouter.

    The direct OpenAI API requires organisation verification for gpt-5.x, which
    most readers will not have. Routing via OpenRouter avoids that -- except
    when the reader explicitly selected the ``openai`` provider, in which case
    honouring their choice matters more.

    Args:
        spec: The provider that was requested.
        model: The resolved model id.

    Returns:
        ``True`` if the request should be rerouted.
    """
    return model.lower().startswith("gpt-5") and spec.name != "openai"


def _missing_key_error(spec: Provider) -> ValueError:
    """Build the error raised when no credential can be found.

    Args:
        spec: The provider that could not be configured.

    Returns:
        A ``ValueError`` naming the variables that would fix the problem and
        pointing at the zero-cost options.
    """
    wanted = " / ".join(spec.key_vars) or "(none)"
    return ValueError(
        f"No API key found for provider {spec.name!r}. Set {wanted}, "
        "or OPENROUTER_API_KEY as a universal fallback. "
        "For a zero-cost setup use provider 'ollama' (local, no key) or "
        "OPENROUTER_MODEL with a ':free' model id."
    )


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

    Args:
        provider: Provider name or alias, e.g. ``"kimi"`` or ``"moonshot"``.
        model: Model id overriding the provider's default.
        api_key: Credential overriding the environment. For the ``openrouter``
            provider this is treated as an OpenRouter key; for any other
            provider it belongs to that provider and is never forwarded to
            OpenRouter.

    Returns:
        A ready-to-use :class:`~agentbook.providers.models.Backend`.

    Raises:
        ValueError: If the provider is unknown, or if it requires a key and
            neither its own variables nor ``OPENROUTER_API_KEY`` are set.
    """
    spec = lookup(provider)
    resolved_model = model or spec.default_model
    key = (api_key or "").strip() or spec.api_key()

    # An explicit key for the openrouter provider is an OpenRouter credential,
    # so it wins over the environment. For any other provider the explicit key
    # belongs to that provider and must not be forwarded to OpenRouter.
    explicit_openrouter_key = key if spec.name == "openrouter" else ""
    available_openrouter_key = explicit_openrouter_key or openrouter_key()

    # 1. gpt-5.x needs OpenAI org verification on the direct API.
    if available_openrouter_key and _needs_openrouter_for_gpt5(spec, resolved_model):
        return build_openrouter_backend(resolved_model, available_openrouter_key, spec.name)

    # 2. The provider's own credential, or a provider that needs none.
    if key or not spec.requires_key:
        # Selecting OpenRouter directly still needs namespaced model ids, so a
        # bare override like "gpt-4o" is mapped the same way as on the fallback
        # path.
        if spec.name == "openrouter":
            return build_openrouter_backend(resolved_model, key, spec.name)
        return Backend(
            api_key=key or _PLACEHOLDER_KEY,
            base_url=spec.resolved_base_url(),
            model=resolved_model,
            provider=spec.name,
            using_openrouter=False,
        )

    # 3. Universal fallback.
    if available_openrouter_key:
        return build_openrouter_backend(resolved_model, available_openrouter_key, spec.name)

    # 4. Nothing is configured.
    raise _missing_key_error(spec)
