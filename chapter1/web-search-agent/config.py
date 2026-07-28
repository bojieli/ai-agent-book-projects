"""
配置文件 - Kimi API 配置
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


def map_model_to_openrouter(model: str) -> str:
    """Map a bare model id to an OpenRouter model id.
    - ids already containing '/' -> left as-is
    - gpt-*/o1-*/o3-*/o4-* -> 'openai/<id>'
    - claude-* -> anthropic Claude (opus/sonnet/haiku)
    - other native ids (kimi-*, doubao-*, ...) are NOT reliably on OpenRouter,
      so fall back to OPENROUTER_MODEL or a safe default that always works.
    """
    m = (model or "").strip()
    if "/" in m:
        return m
    ml = m.lower()
    if ml.startswith(("gpt-", "o1-", "o3-", "o4-")):
        return "openai/" + m
    if ml.startswith("claude-"):
        if "sonnet" in ml:
            return "anthropic/claude-sonnet-4.6"
        if "haiku" in ml:
            return "anthropic/claude-haiku-4.5"
        return "anthropic/claude-opus-4.8"
    if ml.startswith("kimi"):
        # kimi-k3 is not on OpenRouter; moonshotai/kimi-k2.6 is the closest hosted id.
        return "moonshotai/kimi-k2.6"
    return os.getenv("OPENROUTER_MODEL", "openai/gpt-5.6-luna")


def resolve_llm_backend(primary_key: str, primary_base_url: str, model: str):
    """Universal OpenRouter fallback for LLM backend resolution.

    Returns (api_key, base_url, model, using_openrouter).
    - If the primary provider key is present, behavior is unchanged.
    - Else if OPENROUTER_API_KEY is present, route through OpenRouter and map
      the model id to an OpenRouter id.
    - Else raise a clear error listing the accepted keys.
    """
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    # gpt-5.x (incl. gpt-5.6*) needs OpenAI org-verification on the direct API;
    # when an OpenRouter key is present, prefer routing these ids through it.
    if openrouter_key and str(model or "").lower().startswith("gpt-5"):
        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        return openrouter_key, base_url, map_model_to_openrouter(model), True
    if primary_key:
        return primary_key, primary_base_url, model, False
    if openrouter_key:
        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        return openrouter_key, base_url, map_model_to_openrouter(model), True
    raise ValueError(
        "No API key found. Set MOONSHOT_API_KEY / KIMI_API_KEY (primary) or "
        "OPENROUTER_API_KEY (universal fallback)."
    )


class Config:
    """配置类"""
    
    # Kimi API 配置
    MOONSHOT_API_KEY: str = os.getenv("MOONSHOT_API_KEY", "")
    # 向后兼容：如果没有 MOONSHOT_API_KEY，尝试使用 KIMI_API_KEY
    if not MOONSHOT_API_KEY:
        MOONSHOT_API_KEY = os.getenv("KIMI_API_KEY", "")
    
    KIMI_BASE_URL: str = "https://api.moonshot.cn/v1"
    
    # 模型配置
    DEFAULT_MODEL: str = "kimi-k3"  # 使用最新的 Kimi K3 模型

    # 搜索配置
    MAX_SEARCH_ITERATIONS: int = 5  # 最大搜索迭代次数（与 agent 默认值保持一致）
    SEARCH_TIMEOUT: int = 30  # 搜索超时时间（秒）
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def validate(cls) -> bool:
        """
        验证配置是否有效
        
        Returns:
            bool: 配置是否有效
        """
        if not cls.MOONSHOT_API_KEY:
            print("错误: 未设置 MOONSHOT_API_KEY 环境变量")
            print("请设置环境变量: export MOONSHOT_API_KEY='your-api-key'")
            print("(或者使用旧的环境变量名: export KIMI_API_KEY='your-api-key')")
            return False
        return True
    
    @classmethod
    def get_api_key(cls, api_key: Optional[str] = None) -> str:
        """
        获取 API Key
        
        Args:
            api_key: 可选的 API key，如果提供则使用，否则从环境变量获取
            
        Returns:
            API key
        """
        if api_key:
            return api_key
        return cls.MOONSHOT_API_KEY
