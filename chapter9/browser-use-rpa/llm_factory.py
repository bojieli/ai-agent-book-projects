"""包装层 LLM 工厂：为 browser-use 示例统一提供带 OpenRouter 兜底的模型客户端。

本文件位于 RPA 包装层，**不修改** 上游 browser-use fork。它按环境变量决定用哪家：
- gemini-* 模型            -> ChatGoogle（走 GOOGLE_API_KEY）
- 有 OPENAI_API_KEY        -> 直连 OpenAI
- 否则有 OPENROUTER_API_KEY -> 走 OpenRouter，并把模型名映射到 OpenRouter 命名：
      gpt-*    -> openai/gpt-*
      claude-* -> anthropic/claude-opus-4.8
      含 "/"   -> 原样透传
      其它     -> openai/gpt-5.6-luna

默认模型 gpt-5.6-luna。
"""

import os

from browser_use import ChatOpenAI, ChatGoogle

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


def make_llm(model: str = None):
    """按环境变量构造 LLM 客户端（OpenAI 直连优先，缺 Key 时 OpenRouter 兜底）。"""
    model = model or DEFAULT_MODEL
    if model.startswith("gemini"):
        return ChatGoogle(model=model)
    if os.getenv("OPENAI_API_KEY"):
        return ChatOpenAI(model=model)
    if os.getenv("OPENROUTER_API_KEY"):
        return ChatOpenAI(
            model=to_openrouter_model(model),
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url=OPENROUTER_BASE_URL,
        )
    raise RuntimeError(
        "未检测到 OPENAI_API_KEY 或 OPENROUTER_API_KEY，请在 .env 中配置其一"
        "（OpenRouter 可作为统一兜底）。"
    )
