"""Universal OpenRouter fallback for the collaboration tools' LLM clients.

Every LLM entry point in this experiment (sub-agent runs, intelligence tools,
browser-use) speaks the OpenAI-compatible API. This helper centralizes the
credential resolution so that:

  1. When OPENAI_API_KEY is present, behavior is unchanged (direct OpenAI, or a
     custom OPENAI_BASE_URL / OPENAI_MODEL if the user set them).
  2. When OPENAI_API_KEY is absent but OPENROUTER_API_KEY is present, requests
     transparently route through OpenRouter (base_url=https://openrouter.ai/api/v1)
     with the model id mapped to provider/model form.
  3. When neither is set, callers can detect "offline" and fall back to their
     deterministic mock paths (no fabricated model output).
"""

import os
from typing import Optional, Tuple

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def map_model_for_openrouter(model: str) -> str:
    """Map a plain model id onto OpenRouter's `provider/model` form.

    Ids already containing "/" pass through unchanged; gpt-*/o1-*/o3-*/o4-*
    become openai/…; claude-* becomes anthropic/claude-opus-4.8.
    """
    if "/" in model:
        return model
    m = model.lower()
    if m.startswith(("gpt-", "o1-", "o3-", "o4-")):
        return f"openai/{model}"
    if m.startswith("claude-"):
        return "anthropic/claude-opus-4.8"
    if m.startswith("kimi"):
        return "moonshotai/kimi-k2.6"
    return model


def has_llm() -> bool:
    """True when at least one usable LLM credential is configured."""
    return bool(os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
                or os.getenv("MOONSHOT_API_KEY") or os.getenv("KIMI_API_KEY")
                or os.getenv("DASHSCOPE_API_KEY"))


def resolve_llm(default_model: str = "gpt-5.6-luna") -> Tuple[str, Optional[str], str]:
    """Resolve (api_key, base_url, model), applying the OpenRouter fallback.

    Raises RuntimeError listing the accepted keys when neither credential is set.
    """
    model = os.getenv("OPENAI_MODEL", default_model)

    provider = os.getenv("COLLAB_PROVIDER", "").lower()
    if provider in {"dashscope", "qwen", "bailian"}:
        dashscope_key = os.getenv("DASHSCOPE_API_KEY")
        if not dashscope_key:
            raise RuntimeError("COLLAB_PROVIDER=dashscope requires DASHSCOPE_API_KEY")
        return (
            dashscope_key,
            os.getenv(
                "DASHSCOPE_BASE_URL",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            ),
            os.getenv("OPENAI_MODEL", "qwen3.7-plus"),
        )
    if provider == "moonshot":
        moonshot_key = os.getenv("MOONSHOT_API_KEY") or os.getenv("KIMI_API_KEY")
        if not moonshot_key:
            raise RuntimeError("COLLAB_PROVIDER=moonshot requires MOONSHOT_API_KEY or KIMI_API_KEY")
        return moonshot_key, "https://api.moonshot.cn/v1", os.getenv("OPENAI_MODEL", "kimi-k3")

    or_key = os.getenv("OPENROUTER_API_KEY")
    # gpt-5.x (incl. gpt-5.6*) needs OpenAI org-verification on the direct API;
    # when an OpenRouter key is present, prefer routing these ids through it.
    if or_key and model.lower().startswith("gpt-5"):
        return or_key, "https://openrouter.ai/api/v1", map_model_for_openrouter(model)

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key, os.getenv("OPENAI_BASE_URL"), model

    if or_key:
        return or_key, "https://openrouter.ai/api/v1", map_model_for_openrouter(model)

    raise RuntimeError(
        "No LLM key configured. Set OPENAI_API_KEY, DASHSCOPE_API_KEY, OPENROUTER_API_KEY, or MOONSHOT_API_KEY "
        "(universal fallback)."
    )
