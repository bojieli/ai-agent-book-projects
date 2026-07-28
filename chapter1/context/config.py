"""
Configuration module for Context-Aware Agent
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def _reasoning_safe_temperature(model, requested=1.0):
    """Reasoning models (Kimi K3, GPT-5, ...) only accept temperature=1.
    Return 1 for those; otherwise the requested value so non-reasoning
    providers (Doubao, DeepSeek, older Moonshot) are unchanged."""
    m = str(model or "").lower().replace("/", "-")
    return 1 if ("kimi-k3" in m or "gpt-5" in m) else requested


def map_model_to_openrouter(model: str) -> str:
    """Map a bare model id to an OpenRouter model id.
    - ids already containing '/' -> left as-is
    - gpt-*/o1-*/o3-*/o4-* -> 'openai/<id>'
    - claude-* -> anthropic Claude (opus/sonnet/haiku)
    - deepseek-* -> deepseek/<id> (OpenRouter hosts official DeepSeek ids)
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
    if ml.startswith("deepseek"):
        # OpenRouter hosts deepseek/deepseek-v4-flash, deepseek-chat, etc.
        return "deepseek/" + m
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
        "No API key found. Set a provider key "
        "(SILICONFLOW_API_KEY/ARK_API_KEY/MOONSHOT_API_KEY/DEEPSEEK_API_KEY/ZHIPU_API_KEY) or "
        "OPENROUTER_API_KEY (universal fallback)."
    )


class Config:
    """Configuration settings for the agent"""
    
    # Provider Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "doubao").lower()
    
    # API Configuration
    SILICONFLOW_API_KEY: str = os.getenv("SILICONFLOW_API_KEY", "")
    SILICONFLOW_BASE_URL: str = "https://api.siliconflow.cn/v1"
    
    ARK_API_KEY: str = os.getenv("ARK_API_KEY", "")
    ARK_BASE_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    
    MOONSHOT_API_KEY: str = os.getenv("MOONSHOT_API_KEY", "")
    MOONSHOT_BASE_URL: str = "https://api.moonshot.cn/v1"

    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv(
        "DEEPSEEK_BASE_URL", "https://api.deepseek.com"
    )

    ZHIPU_API_KEY: str = os.getenv("ZHIPU_API_KEY", "")
    ZHIPU_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"
    
    # Model Configuration (defaults based on provider)
    MODEL_NAME: str = os.getenv("MODEL_NAME", "")  # Will be set based on provider if not specified
    MODEL_TEMPERATURE: float = float(os.getenv("MODEL_TEMPERATURE", "0.3"))
    MODEL_MAX_TOKENS: int = int(os.getenv("MODEL_MAX_TOKENS", "1000"))
    
    # Agent Configuration
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "10"))
    ENABLE_REASONING: bool = os.getenv("ENABLE_REASONING", "true").lower() == "true"
    
    # Test Configuration
    TEST_PDF_URL: str = os.getenv(
        "TEST_PDF_URL",
        "https://www.berkshirehathaway.com/qtrly/1stqtr23.pdf"
    )
    
    # Currency Configuration (Example rates - in production use real API)
    EXCHANGE_RATES = {
        "USD": 1.0,
        "EUR": 0.92,
        "GBP": 0.79,
        "JPY": 149.50,
        "CNY": 7.24,
        "CAD": 1.36,
        "AUD": 1.53,
        "CHF": 0.88,
        "INR": 83.12,
        "SGD": 1.34
    }
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")
    LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    
    # File paths
    RESULTS_DIR: str = "results"
    TEST_PDFS_DIR: str = "test_pdfs"
    
    @classmethod
    def get_api_key(cls, provider: str = None) -> str:
        """
        Get API key for the specified provider
        
        Args:
            provider: Provider name (defaults to LLM_PROVIDER)
            
        Returns:
            API key for the provider
        """
        provider = provider or cls.LLM_PROVIDER
        provider = provider.lower()
        
        if provider == "siliconflow":
            return cls.SILICONFLOW_API_KEY
        elif provider == "doubao":
            return cls.ARK_API_KEY
        elif provider == "kimi" or provider == "moonshot":
            return cls.MOONSHOT_API_KEY
        elif provider == "deepseek":
            return cls.DEEPSEEK_API_KEY
        elif provider == "zhipu":
            return cls.ZHIPU_API_KEY
        else:
            return ""
    
    @classmethod
    def get_default_model(cls, provider: str = None) -> str:
        """
        Get default model for the specified provider
        
        Args:
            provider: Provider name (defaults to LLM_PROVIDER)
            
        Returns:
            Default model name for the provider
        """
        provider = provider or cls.LLM_PROVIDER
        provider = provider.lower()
        
        if cls.MODEL_NAME:
            return cls.MODEL_NAME
        
        if provider == "siliconflow":
            return "Qwen/Qwen3.5-397B-A17B"
        elif provider == "doubao":
            return "doubao-seed-1-6-thinking-250715"
        elif provider == "kimi" or provider == "moonshot":
            return "kimi-k3"
        elif provider == "deepseek":
            # V4 Flash: tool calling + thinking mode (legacy deepseek-chat /
            # deepseek-reasoner aliases are deprecated 2026-07-24).
            return "deepseek-v4-flash"
        elif provider == "zhipu":
            return "glm-5.2"
        else:
            return ""
    
    @classmethod
    def validate(cls, provider: str = None) -> bool:
        """
        Validate required configuration
        
        Args:
            provider: Provider to validate (defaults to LLM_PROVIDER)
        
        Returns:
            True if configuration is valid
        """
        provider = provider or cls.LLM_PROVIDER
        api_key = cls.get_api_key(provider)
        
        if not api_key:
            if provider == "siliconflow":
                print("ERROR: SILICONFLOW_API_KEY is not set")
            elif provider == "doubao":
                print("ERROR: ARK_API_KEY is not set")
            elif provider == "kimi" or provider == "moonshot":
                print("ERROR: MOONSHOT_API_KEY is not set")
            elif provider == "deepseek":
                print("ERROR: DEEPSEEK_API_KEY is not set")
            elif provider == "zhipu":
                print("ERROR: ZHIPU_API_KEY is not set")
            else:
                print(f"ERROR: No API key configured for provider: {provider}")
            
            print("Please set it in .env file or as environment variable")
            return False
        
        return True
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories if they don't exist"""
        os.makedirs(cls.RESULTS_DIR, exist_ok=True)
        os.makedirs(cls.TEST_PDFS_DIR, exist_ok=True)
    
    @classmethod
    def get_model_config(cls) -> dict:
        """
        Get model configuration as dictionary
        
        Returns:
            Model configuration dict
        """
        return {
            "model": cls.MODEL_NAME,
            "temperature": _reasoning_safe_temperature(cls.MODEL_NAME, cls.MODEL_TEMPERATURE),
            "max_tokens": cls.MODEL_MAX_TOKENS
        }
    
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
        print(f"API Key Set: {'Yes' if cls.SILICONFLOW_API_KEY else 'No'}")
        print(f"Log Level: {cls.LOG_LEVEL}")
        print("="*50 + "\n")
