"""
配置文件 - Kimi API 配置
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from dotenv import load_dotenv

# Read the nearest .env, searching upward from the working directory, so a
# single file at the repository root serves every chapter.
load_dotenv()


# Provider resolution lives in the shared agentbook package so every chapter
# stays consistent; see agentbook/providers.py. The fallback keeps this
# experiment runnable from a checkout where agentbook is not installed.
try:
    from agentbook.providers import (
        SUPPORTED_PROVIDERS,
        map_model_to_openrouter,
        resolve_backend,
        resolve_llm_backend,
    )
except ImportError:  # pragma: no cover - exercised only without the package
    import sys as _sys

    _sys.path.insert(
        0, str(__import__("pathlib").Path(__file__).resolve().parents[2])
    )
    from agentbook.providers import (
        SUPPORTED_PROVIDERS,
        map_model_to_openrouter,
        resolve_backend,
        resolve_llm_backend,
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
    SEARCH_TIMEOUT: float = float(os.getenv("SEARCH_TIMEOUT", "30"))
    
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
