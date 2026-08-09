"""
全局配置：加载环境变量、提供 OpenAI 客户端与默认模型名。

只依赖官方 OpenAI SDK，读取 OPENAI_API_KEY。
默认模型 gpt-5.6-luna（便宜、够用于因子发现、结构化抽取与文案生成）。
"""
import os

from openai import OpenAI

try:
    # 可选：如果安装了 python-dotenv，则自动加载同目录 .env
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv 是可选依赖
    pass

def _openrouter_model_id(model) -> str:
    """将供应商原生模型名映射为 OpenRouter 模型 id（通用 OpenRouter 回退用）。
    显式的 OPENROUTER_MODEL 环境变量优先。"""
    override = os.getenv("OPENROUTER_MODEL")
    if override:
        return override
    m = (model or "").strip()
    if not m:
        return "openai/gpt-5.6-luna"
    if "/" in m:
        return m
    ml = m.lower()
    if ml.startswith(("gpt-", "o1", "o3", "o4", "chatgpt")):
        return "openai/" + m
    if ml.startswith("claude-"):
        return "anthropic/claude-opus-4.8"
    if ml.startswith("kimi"):
        # kimi-k3 is not on OpenRouter; moonshotai/kimi-k2.6 is the closest hosted id.
        return "moonshotai/kimi-k2.6"
    return "openai/gpt-5.6-luna"


# Provider: OpenAI by default; DashScope/Qwen/Bailian are OpenAI-compatible.
PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
PROVIDER = {"qwen": "dashscope", "bailian": "dashscope"}.get(PROVIDER, PROVIDER)
# 默认模型，可用环境变量覆盖
MODEL = os.getenv(
    "DASHSCOPE_MODEL" if PROVIDER == "dashscope" else "OPENAI_MODEL",
    "qwen3.7-plus" if PROVIDER == "dashscope" else "gpt-5.6-luna",
)

# 通用 OpenRouter 回退：若没有 OPENAI_API_KEY 但设置了 OPENROUTER_API_KEY，
# 则把聊天模型路由到 OpenRouter，并把模型名映射为 OpenRouter 的 id。
_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
_DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
_OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# gpt-5.x（含 gpt-5.6*）在 OpenAI 直连 API 上需要组织实名认证；只要设置了
# OPENROUTER_API_KEY，就优先把这类 id 走 OpenRouter。
_PREFER_OPENROUTER = bool(_OPENROUTER_API_KEY) and MODEL.lower().startswith("gpt-5")
_PRIMARY_API_KEY = _DASHSCOPE_API_KEY if PROVIDER == "dashscope" else _OPENAI_API_KEY
_USE_OPENROUTER = _PREFER_OPENROUTER or ((not _PRIMARY_API_KEY) and bool(_OPENROUTER_API_KEY))
if _USE_OPENROUTER:
    MODEL = _openrouter_model_id(MODEL)


def get_client() -> OpenAI:
    """返回一个配置好的 OpenAI 客户端。

    优先使用官方端点（读取 OPENAI_API_KEY）；若缺失则在存在 OPENROUTER_API_KEY 时
    回退到 OpenRouter（OpenAI 兼容端点）。"""
    # timeout + 自动重试：发现/抽取阶段要连续发几十次请求，单次瞬时错误
    # （网络抖动 / 限流 / 5xx）不应中断整条流水线。
    if _PRIMARY_API_KEY and not _PREFER_OPENROUTER:
        if PROVIDER == "dashscope":
            return OpenAI(
                api_key=_DASHSCOPE_API_KEY,
                base_url=os.getenv(
                    "DASHSCOPE_BASE_URL",
                    "https://dashscope.aliyuncs.com/compatible-mode/v1",
                ),
                timeout=60.0,
                max_retries=5,
            )
        return OpenAI(api_key=_OPENAI_API_KEY, timeout=60.0, max_retries=5)
    if _OPENROUTER_API_KEY:
        return OpenAI(
            api_key=_OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            timeout=60.0,
            max_retries=5,
        )
    raise RuntimeError(
        "未找到所选 provider 的 API Key，请设置 OPENAI_API_KEY、DASHSCOPE_API_KEY "
        "或 OPENROUTER_API_KEY。"
    )
