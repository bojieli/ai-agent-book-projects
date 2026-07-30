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

Adding a provider is one entry in :data:`PROVIDERS`, in
:mod:`~agentbook.providers.registry`.

Free / zero-cost options:

* ``ollama``   -- runs models on your own machine, no API key, no cost.
* ``openrouter`` with a ``:free`` model id, e.g.::

      OPENROUTER_API_KEY=your-openrouter-api-key
      OPENROUTER_MODEL=google/gemma-4-31b-it:free

  The model runs on OpenRouter's servers, so a modest laptop is fine.

Package layout, in dependency order -- each module imports only from those
above it:

* :mod:`~agentbook.providers.models` -- the ``Provider`` and ``Backend`` types
* :mod:`~agentbook.providers.openrouter` -- OpenRouter constants and model mapping
* :mod:`~agentbook.providers.registry` -- the provider table and name lookup
* :mod:`~agentbook.providers.resolution` -- the precedence rules
* :mod:`~agentbook.providers.legacy` -- the pre-registry compatibility shim

This module re-exports the full public surface, so importing from
``agentbook.providers`` directly is the supported way to use the package.
"""

from __future__ import annotations

from .legacy import resolve_llm_backend
from .models import Backend, Provider
from .openrouter import (
    OPENROUTER_BASE_URL,
    OPENROUTER_DEFAULT_MODEL,
    is_openrouter_key,
    map_model_to_openrouter,
)
from .registry import PROVIDERS, SUPPORTED_PROVIDERS, canonical_provider
from .resolution import resolve_backend

__all__ = [
    "OPENROUTER_BASE_URL",
    "OPENROUTER_DEFAULT_MODEL",
    "PROVIDERS",
    "SUPPORTED_PROVIDERS",
    "Backend",
    "Provider",
    "canonical_provider",
    "is_openrouter_key",
    "map_model_to_openrouter",
    "resolve_backend",
    "resolve_llm_backend",
]
