"""Dataclasses describing providers and resolved backends.

This module is the leaf of the package's dependency graph: it defines the two
value types the rest of the package builds on, and imports nothing from its
siblings.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

__all__ = ["Backend", "Provider"]


@dataclass(frozen=True)
class Provider:
    """Static description of an OpenAI-compatible backend.

    Attributes:
        name: Canonical provider name, e.g. ``"kimi"``.
        base_url: Default API endpoint, used when no override is set.
        default_model: Model id used when the caller does not pick one.
        key_vars: Environment variables holding the API key, tried in order.
            The first non-empty one wins; later entries exist for backwards
            compatibility.
        base_url_var: Environment variable overriding ``base_url``, for
            self-hosted or regional deployments. ``None`` if not overridable.
        requires_key: Whether a missing key is an error. Local runtimes such as
            Ollama accept any placeholder, so they set this to ``False``.
        namespaces_models: Whether this backend expects vendor-namespaced model
            ids such as ``openai/gpt-4o`` rather than bare ones. True for
            aggregators that resell many vendors' models; a bare id given to
            one of these is mapped before the request goes out.

            This describes *model-id formatting only*. It says nothing about
            which endpoint to call or whose credentials are valid -- an
            aggregator sharing OpenRouter's id format still has its own
            ``base_url`` and its own key, and is never routed through
            OpenRouter on that basis.
    """

    name: str
    base_url: str
    default_model: str
    key_vars: tuple[str, ...] = ()
    base_url_var: str | None = None
    requires_key: bool = True
    namespaces_models: bool = False

    def api_key(self) -> str:
        """Read this provider's API key from the environment.

        Returns:
            The first non-empty value among ``key_vars``, stripped of
            surrounding whitespace, or ``""`` when none is set.
        """
        for var in self.key_vars:
            value = os.getenv(var, "").strip()
            if value:
                return value
        return ""

    def resolved_base_url(self) -> str:
        """Return the endpoint to call, honouring any environment override.

        Returns:
            The value of ``base_url_var`` if that variable is set and non-empty,
            otherwise the built-in ``base_url``.
        """
        if self.base_url_var:
            return os.getenv(self.base_url_var, "").strip() or self.base_url
        return self.base_url


@dataclass(frozen=True)
class Backend:
    """A resolved, ready-to-use OpenAI-compatible endpoint.

    Attributes:
        api_key: Credential for ``base_url``. Never empty -- local runtimes get
            a placeholder, because the OpenAI client rejects an empty key.
        base_url: The endpoint to send requests to.
        model: Model id valid at ``base_url``. Note this may differ from the
            requested id when the request was rerouted through OpenRouter.
        provider: The provider that was requested, after alias resolution.
        using_openrouter: Whether the request is going through OpenRouter
            rather than the provider's own API.
    """

    api_key: str
    base_url: str
    model: str
    provider: str
    using_openrouter: bool

    def __iter__(self):
        """Unpack as the 4-tuple the pre-registry chapter helpers returned.

        Returns:
            An iterator over ``api_key``, ``base_url``, ``model`` and
            ``using_openrouter``, in that order.
        """
        return iter((self.api_key, self.base_url, self.model, self.using_openrouter))
