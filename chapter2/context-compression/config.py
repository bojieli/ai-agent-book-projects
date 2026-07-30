"""
Configuration module for Context Compression Experiment
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration settings for the context compression experiment"""
    
    # API Configuration
    MOONSHOT_API_KEY: str = os.getenv("MOONSHOT_API_KEY", "")
    MOONSHOT_BASE_URL: str = "https://api.moonshot.cn/v1"

    # Universal fallback: 当 MOONSHOT_API_KEY 缺失但设置了 OPENROUTER_API_KEY 时，
    # 自动改走 OpenRouter（kimi-* 模型名映射为 moonshotai/kimi-k2）。
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    
    SERPER_API_KEY: str = os.getenv("SERPER_API_KEY", "")
    SERPER_BASE_URL: str = "https://google.serper.dev"
    
    # Model Configuration
    MODEL_NAME: str = os.getenv("MODEL_NAME", "kimi-k3")
    MODEL_TEMPERATURE: float = float(os.getenv("MODEL_TEMPERATURE", "0.3"))
    MODEL_MAX_TOKENS: int = int(os.getenv("MODEL_MAX_TOKENS", "8192"))
    
    # Agent Configuration
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "50"))
    ENABLE_VERBOSE: bool = os.getenv("ENABLE_VERBOSE", "false").lower() == "true"
    
    # Compression Configuration
    MAX_WEBPAGE_LENGTH: int = int(os.getenv("MAX_WEBPAGE_LENGTH", "50000"))
    SUMMARY_MAX_TOKENS: int = int(os.getenv("SUMMARY_MAX_TOKENS", "500"))
    
    # Context Window Configuration
    CONTEXT_WINDOW_SIZE: int = 128000  # 128K context budget for the compression demo (K3 supports up to 1M)
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    
    # File paths
    RESULTS_DIR: str = "results"
    CACHE_DIR: str = "cache"
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate required configuration
        
        Returns:
            True if configuration is valid
        """
        if not cls.MOONSHOT_API_KEY and not cls.OPENROUTER_API_KEY:
            print("ERROR: neither MOONSHOT_API_KEY nor OPENROUTER_API_KEY is set")
            print("Please set MOONSHOT_API_KEY (primary) or OPENROUTER_API_KEY "
                  "(universal fallback) in .env or as an environment variable")
            return False
        
        if not cls.SERPER_API_KEY:
            print("WARNING: SERPER_API_KEY is not set")
            print("Web search functionality will be limited")
            print("Get a free API key at: https://serper.dev")
        
        return True
    
    @classmethod
    def resolve_llm(cls):
        """Return ``(api_key, base_url, model)`` honoring the MOONSHOT->OpenRouter fallback.

        Computed at call time so a runtime override of ``Config.MODEL_NAME``
        (e.g. via ``--model``) is respected.

        端点、接受的 key 变量与模型名映射由 agentbook 的 provider 注册表统一
        维护。此处保持三元组返回值：调用方按 3 个字段解包，测试也按这个形状
        打桩。
        """
        from agentbook.providers import resolve_backend

        backend = resolve_backend("kimi", model=cls.MODEL_NAME)
        return backend.api_key, backend.base_url, backend.model

    @classmethod
    def create_directories(cls):
        """Create necessary directories if they don't exist"""
        os.makedirs(cls.RESULTS_DIR, exist_ok=True)
        os.makedirs(cls.CACHE_DIR, exist_ok=True)
    
    @classmethod
    def print_config(cls):
        """Print current configuration (hiding sensitive data)"""
        print("\n" + "="*50)
        print("CONFIGURATION")
        print("="*50)
        print(f"Model: {cls.MODEL_NAME}")
        print(f"Temperature: {cls.MODEL_TEMPERATURE}")
        print(f"Max Tokens: {cls.MODEL_MAX_TOKENS}")
        print(f"Max Iterations: {cls.MAX_ITERATIONS}")
        print(f"Context Window: {cls.CONTEXT_WINDOW_SIZE:,} tokens")
        print(f"Max Webpage Length: {cls.MAX_WEBPAGE_LENGTH:,} chars")
        print(f"Summary Max Tokens: {cls.SUMMARY_MAX_TOKENS}")
        print(f"Kimi API Key Set: {'Yes' if cls.MOONSHOT_API_KEY else 'No'}")
        print(f"Serper API Key Set: {'Yes' if cls.SERPER_API_KEY else 'No'}")
        print("="*50 + "\n")
