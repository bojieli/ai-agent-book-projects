"""包装层 LLM 环境解析：为 GAIA 经验学习示例提供带 OpenRouter 兜底的配置。

本文件位于 gaia-experience 包装层，**不修改** 上游 AWorld fork。它把散落在各处的
`os.getenv("LLM_API_KEY"/"LLM_BASE_URL"/"LLM_MODEL_NAME")` 读取集中起来，并加入统一兜底：

- 有 LLM_API_KEY / OPENAI_API_KEY -> 直连（沿用 LLM_BASE_URL，可为空即 OpenAI 官方）
- 否则有 OPENROUTER_API_KEY        -> 走 OpenRouter（https://openrouter.ai/api/v1），
                                     并把模型名映射到 OpenRouter 命名：
      gpt-*    -> openai/gpt-*
      claude-* -> anthropic/claude-opus-4.8
      含 "/"   -> 原样透传
      其它     -> openai/gpt-5.6-luna

默认模型 gpt-5.6-luna。
"""

import os

DEFAULT_MODEL = "gpt-5.6-luna"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def to_openrouter_model(model: str) -> str:
    if not model:
        return "openai/gpt-5.6-luna"
    if "/" in model:
        return model
    if model.startswith("gpt-"):
        return "openai/" + model
    if model.startswith("claude-"):
        return "anthropic/claude-opus-4.8"
    return "openai/gpt-5.6-luna"


def resolve_llm(default_model: str = DEFAULT_MODEL, model_override: str = None) -> dict:
    """返回 AgentConfig 需要的 provider/model/base_url/api_key 四元组（含 OpenRouter 兜底）。

    model_override: 若显式给了模型名（如 config.yaml 或 CLI），优先用它。
    """
    provider = os.getenv("LLM_PROVIDER", "openai")
    model = model_override or os.getenv("LLM_MODEL_NAME", default_model)
    base_url = os.getenv("LLM_BASE_URL")
    api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")

    if not api_key and os.getenv("OPENROUTER_API_KEY"):
        api_key = os.getenv("OPENROUTER_API_KEY")
        base_url = base_url or OPENROUTER_BASE_URL
        model = to_openrouter_model(model)

    return {
        "llm_provider": provider,
        "llm_model_name": model,
        "llm_base_url": base_url,
        "llm_api_key": api_key,
    }
