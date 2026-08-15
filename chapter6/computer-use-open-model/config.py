"""Configuration for the provider-neutral Computer Use companion."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from os import environ as process_environ
from urllib.parse import urlparse

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "qwen/qwen3-vl-32b-instruct"


class ConfigError(ValueError):
    """Raised when the endpoint configuration cannot run the experiment."""


@dataclass(frozen=True)
class ModelEndpoint:
    """A redaction-safe description plus the secret used by the API client."""

    api_key: str
    api_key_env: str
    base_url: str
    model: str
    schema_mode: str

    def public_dict(self) -> dict[str, str]:
        return {
            "api_protocol": "openai-compatible-chat-completions",
            "api_key_env": self.api_key_env,
            "base_url": self.base_url,
            "requested_model": self.model,
            "schema_mode": self.schema_mode,
        }


def _nonempty(values: Mapping[str, str], name: str) -> str | None:
    value = values.get(name, "").strip()
    return value or None


def resolve_endpoint(values: Mapping[str, str] | None = None) -> ModelEndpoint:
    """Resolve an open-model endpoint without coupling it to one API vendor.

    ``OPEN_MODEL_*`` is the portable interface. ``OPENROUTER_API_KEY`` is
    accepted as a convenience because the documented reference route uses it.
    A local vLLM/SGLang server can set ``OPEN_MODEL_API_KEY=local``.
    """

    source = process_environ if values is None else values
    api_key = _nonempty(source, "OPEN_MODEL_API_KEY")
    api_key_env = "OPEN_MODEL_API_KEY"
    if api_key is None:
        api_key = _nonempty(source, "OPENROUTER_API_KEY")
        api_key_env = "OPENROUTER_API_KEY"
    if api_key is None:
        raise ConfigError(
            "Set OPEN_MODEL_API_KEY for an OpenAI-compatible endpoint, or "
            "OPENROUTER_API_KEY for the documented Qwen3-VL route."
        )

    base_url = _nonempty(source, "OPEN_MODEL_BASE_URL") or DEFAULT_BASE_URL
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ConfigError("OPEN_MODEL_BASE_URL must be an absolute http(s) URL")

    model = _nonempty(source, "OPEN_MODEL_MODEL") or DEFAULT_MODEL
    schema_mode = (_nonempty(source, "OPEN_MODEL_SCHEMA_MODE") or "native").lower()
    if schema_mode not in {"native", "prompt"}:
        raise ConfigError("OPEN_MODEL_SCHEMA_MODE must be 'native' or 'prompt'")

    return ModelEndpoint(
        api_key=api_key,
        api_key_env=api_key_env,
        base_url=base_url.rstrip("/"),
        model=model,
        schema_mode=schema_mode,
    )
