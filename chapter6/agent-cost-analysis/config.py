"""
全局配置：模型与价格。

价格换算成本时使用「每百万 token 单价（美元）」。
默认值取自 OpenAI gpt-4o-mini 的公开定价（2024-2025）：
    - 输入        : $0.15  / 1M tokens
    - 缓存命中输入 : $0.075 / 1M tokens   （命中 prompt cache 的输入按 5 折计费）
    - 输出        : $0.60  / 1M tokens

注意：
1. 默认模型为 gpt-5.6-luna（当前廉价旗舰）。首选凭据是 OPENAI_API_KEY；若未设置，
   自动回退到 OPENROUTER_API_KEY 并把模型名映射成 OpenRouter id（gpt-* -> openai/*）。
   由于 gpt-5.x 直连 OpenAI 需要组织实名认证，只要 OPENROUTER_API_KEY 存在就优先走
   OpenRouter（见 make_client_and_model）。仍可用 COST_DEMO_MODEL / --model 切换任意模型。
2. OpenAI 的 prompt caching 是「自动」的：当请求前缀 >= 1024 token 且与近期请求
   命中相同前缀时，usage.prompt_tokens_details.cached_tokens 会大于 0，
   这部分 token 按缓存价（更便宜）计费。本项目正是用它来真实体现 KV-cache 的节省。
   （OpenRouter 转发 OpenAI 时同样在 prompt_tokens_details.cached_tokens 回传缓存命中。）
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

# 使用的模型（默认当前廉价旗舰 gpt-5.6-luna；可用 COST_DEMO_MODEL / --model 覆盖）
MODEL = os.environ.get("COST_DEMO_MODEL", "gpt-5.6-luna")

# OpenRouter 回退：无 OPENAI_API_KEY 时用 OPENROUTER_API_KEY 走 OpenAI 兼容端点。
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def _to_openrouter_model(model: str) -> str:
    """把模型名映射成 OpenRouter id：含 '/' 视为原生 id；gpt-* -> openai/*；
    claude-* -> anthropic/claude-opus-4.8；其余回退到 openai/gpt-5.6-luna。"""
    if "/" in model:
        return model
    if model.startswith("gpt-"):
        return "openai/" + model
    if model.startswith("claude-"):
        return "anthropic/claude-opus-4.8"
    return "openai/gpt-5.6-luna"


def make_client_and_model(model: str):
    """构造 OpenAI 兼容 client 并返回 (client, 实际调用的模型名)。

    回退策略（universal OpenRouter fallback）：
      - gpt-5.x 且存在 OPENROUTER_API_KEY -> 优先走 OpenRouter（直连需组织实名认证）；
      - 否则有 OPENAI_API_KEY -> 直连 OpenAI，模型名不变；
      - 否则有 OPENROUTER_API_KEY -> 走 OpenRouter，模型名按 _to_openrouter_model 映射；
      - 两者皆无 -> 抛出清晰错误。
    """
    from openai import OpenAI

    primary = os.environ.get("OPENAI_API_KEY", "").strip()
    orkey = os.environ.get("OPENROUTER_API_KEY", "").strip()
    prefer_openrouter = bool(orkey) and model.startswith("gpt-5")

    if not prefer_openrouter and primary:
        return OpenAI(timeout=60.0, max_retries=2), model
    if orkey:
        return (
            OpenAI(base_url=OPENROUTER_BASE_URL, api_key=orkey,
                   timeout=60.0, max_retries=2),
            _to_openrouter_model(model),
        )
    if primary:
        return OpenAI(timeout=60.0, max_retries=2), model
    raise RuntimeError(
        "缺少可用凭据：请设置 OPENAI_API_KEY（直连 OpenAI），或设置 "
        "OPENROUTER_API_KEY（自动回退到 OpenRouter）；或改用 --offline 离线复算（无需 key）。"
    )

# 每百万 token 的美元单价（默认 gpt-4o-mini）
PRICE_INPUT_PER_M = 0.15      # 普通输入
PRICE_CACHED_PER_M = 0.075    # 命中缓存的输入（gpt-4o-mini 缓存读取为输入价的 50%）
PRICE_OUTPUT_PER_M = 0.60     # 输出


@dataclass(frozen=True)
class Pricing:
    """一组每百万 token 的美元单价。"""
    input_per_m: float
    cached_per_m: float
    output_per_m: float

    def cost_usd(self, prompt_tokens: int, cached_tokens: int,
                 completion_tokens: int) -> float:
        """按 token 用量换算成本（美元）。

        prompt_tokens   : usage.prompt_tokens，包含了缓存命中的部分
        cached_tokens   : usage.prompt_tokens_details.cached_tokens，命中缓存的输入 token
        completion_tokens: usage.completion_tokens

        未命中缓存的输入 = prompt_tokens - cached_tokens，按普通输入价计费；
        命中缓存的输入按缓存价计费。
        """
        uncached_input = max(prompt_tokens - cached_tokens, 0)
        return (
            uncached_input / 1_000_000 * self.input_per_m
            + cached_tokens / 1_000_000 * self.cached_per_m
            + completion_tokens / 1_000_000 * self.output_per_m
        )


# 常见 OpenAI 模型的公开单价预设（每百万 token，美元），方便 CLI 用 --model 一键切换。
# 换更强的模型不影响 KV-cache 机制（仍要求稳定前缀 >= 1024 token）。
PRICING_PRESETS = {
    "gpt-4o-mini": Pricing(0.15, 0.075, 0.60),
    "gpt-4o":      Pricing(2.50, 1.25, 10.00),
    "gpt-4.1-mini": Pricing(0.40, 0.10, 1.60),
    "gpt-4.1":     Pricing(2.00, 0.50, 8.00),
}


def default_pricing() -> Pricing:
    """返回默认模型（config 中 MODEL）的单价；未知模型回退到模块级 PRICE_* 默认值。"""
    return PRICING_PRESETS.get(
        MODEL, Pricing(PRICE_INPUT_PER_M, PRICE_CACHED_PER_M, PRICE_OUTPUT_PER_M)
    )


def cost_usd(prompt_tokens: int, cached_tokens: int, completion_tokens: int,
             pricing: "Pricing | None" = None) -> float:
    """按 token 用量换算成本（美元）。默认用模块级单价，可传入自定义 Pricing。"""
    p = pricing or Pricing(PRICE_INPUT_PER_M, PRICE_CACHED_PER_M, PRICE_OUTPUT_PER_M)
    return p.cost_usd(prompt_tokens, cached_tokens, completion_tokens)
