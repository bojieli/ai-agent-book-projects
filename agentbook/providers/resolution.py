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

import os

from .models import Backend, Provider
from .openrouter import (
    OPENROUTER_DEFAULT_MODEL,
    ZERO_COST_HINT,
    map_model_to_openrouter,
    openrouter_base_url,
    openrouter_key,
)
from .registry import lookup

__all__ = ["resolve_backend"]

# Local runtimes ignore the key, but the OpenAI client rejects an empty one.
# Deliberately not a provider name: this is a credential value, and reusing a
# provider name here would make the two indistinguishable to callers that log
# or redact based on either.
_PLACEHOLDER_KEY = "not-needed"

# The universal fallback is one specific provider, not a category. Other
# aggregators may share its model-id format (see Provider.namespaces_models)
# but not its endpoint or its credentials.
_OPENROUTER = "openrouter"


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
            this function does not fall back to the environment. Empty values
            become a placeholder, since the OpenAI client rejects an empty key.
        provider: The provider that was originally requested. Recorded on the
            backend so callers can report what the user asked for.

    Returns:
        A backend pointing at OpenRouter with ``using_openrouter`` set.
    """
    return Backend(
        api_key=api_key or _PLACEHOLDER_KEY,
        base_url=openrouter_base_url(),
        # The caller asked for this model and is being rerouted for credential
        # reasons alone, so an unmapped id is sent as-is and rejected by name.
        # Substituting here would answer as a different vendor's model without
        # the reader ever learning theirs was unavailable.
        model=map_model_to_openrouter(
            (model or "").strip() or os.getenv("OPENROUTER_MODEL", "").strip() or OPENROUTER_DEFAULT_MODEL,
            substitute_unknown=not (model or "").strip(),
        ),
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
        "or OPENROUTER_API_KEY as a universal fallback. " + ZERO_COST_HINT
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
    model_clean = (model or "").strip()
    if model_clean:
        resolved_model = model_clean
    elif spec.name == _OPENROUTER:
        # The OpenRouter default honours OPENROUTER_MODEL — the env var this
        # package documents (see the module docstring / ZERO_COST_HINT) as the
        # ':free' zero-cost selector. Without this, the documented free recipe
        # silently resolves the paid OPENROUTER_DEFAULT_MODEL instead.
        resolved_model = os.getenv("OPENROUTER_MODEL", "").strip() or spec.default_model
    else:
        resolved_model = spec.default_model
    key = (api_key or "").strip() or spec.api_key()

    # Only OpenRouter's own credential can authenticate against OpenRouter. An
    # explicit key given for the openrouter provider is such a credential and
    # wins over the environment; any other provider's key -- including another
    # aggregator's -- belongs to that provider and is never forwarded here.
    explicit_openrouter_key = key if spec.name == _OPENROUTER else ""
    available_openrouter_key = explicit_openrouter_key or openrouter_key()

    # 1. gpt-5.x needs OpenAI org verification on the direct API.
    if available_openrouter_key and _needs_openrouter_for_gpt5(spec, resolved_model):
        return build_openrouter_backend(resolved_model, available_openrouter_key, spec.name)

    # 2. The provider's own credential, or a provider that needs none.
    if key or not spec.requires_key:
        return Backend(
            api_key=key or _PLACEHOLDER_KEY,
            base_url=spec.resolved_base_url(),
            # An aggregator resells many vendors' models and so expects
            # namespaced ids: a bare override like "gpt-4o" is mapped even when
            # talking to the aggregator directly. An id with no mapping cannot
            # be requested here at all, so a working default beats a certain
            # failure -- unlike the reroute path above.
            model=map_model_to_openrouter(resolved_model, substitute_unknown=True)
            if spec.namespaces_models
            else resolved_model,
            provider=spec.name,
            using_openrouter=spec.name == _OPENROUTER,
        )

    # 3. Universal fallback.
    if available_openrouter_key:
        return build_openrouter_backend(resolved_model, available_openrouter_key, spec.name)

    # 4. Nothing is configured.
    raise _missing_key_error(spec)
