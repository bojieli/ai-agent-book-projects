"""Universal OpenRouter fallback helper (Chapter 2 experiments).

Goal: every experiment keeps working when the direct provider key is missing
but ``OPENROUTER_API_KEY`` is present. Default behavior is fully preserved:

  * If a primary provider key is present -> use the primary provider unchanged.
  * Else if ``OPENROUTER_API_KEY`` is present -> route through OpenRouter
    (base_url=https://openrouter.ai/api/v1) and translate the model id.
  * Else raise a clear error listing every accepted key.

Model translation (only applied when the OpenRouter fallback is active):
  * ids already containing "/" are passed through unchanged;
  * gpt-* / o1* / o3* / o4* / chatgpt* -> "openai/<id>";
  * claude-*                            -> "anthropic/claude-opus-4.8";
  * kimi-*                              -> "moonshotai/kimi-k2.6";
  * anything else                       -> passed through unchanged.
"""

import os

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def is_openrouter_key(api_key):
    """OpenRouter keys reliably start with ``sk-or-``."""
    return bool(api_key) and api_key.startswith("sk-or-")


def map_model_to_openrouter(model):
    """Translate a bare provider model id into an OpenRouter-qualified id."""
    if not model or "/" in model:
        return model
    low = model.lower()
    if low.startswith(("gpt-", "gpt5", "o1", "o3", "o4", "chatgpt")):
        return "openai/" + model
    if low.startswith("claude"):
        return "anthropic/claude-opus-4.8"
    if low.startswith("kimi"):
        return "moonshotai/kimi-k2.6"
    return model


def resolve_llm(model=None, primary_keys=("OPENAI_API_KEY",), primary_base_url=None):
    """Resolve ``(api_key, base_url, model)`` honoring the primary->OpenRouter fallback.

    Args:
        model: requested model id (may be remapped when the fallback activates).
        primary_keys: env var names checked in order for the primary provider.
        primary_base_url: base_url used when a primary key is found
            (``None`` means the OpenAI SDK default / official endpoint).
    """
    or_key = os.getenv("OPENROUTER_API_KEY")
    # gpt-5.x (incl. gpt-5.6*) needs OpenAI org-verification on the direct API;
    # when an OpenRouter key is present, prefer routing these ids through it.
    if or_key and model and model.lower().startswith("gpt-5"):
        return or_key, OPENROUTER_BASE_URL, map_model_to_openrouter(model)
    for env in primary_keys:
        key = os.getenv(env)
        if key:
            return key, primary_base_url, model
    if or_key:
        return or_key, OPENROUTER_BASE_URL, map_model_to_openrouter(model)
    accepted = ", ".join(list(primary_keys) + ["OPENROUTER_API_KEY"])
    raise RuntimeError(
        "No LLM API key found. Set one of the primary keys or the universal "
        "fallback. Accepted keys: " + accepted + ". See env.example."
    )
