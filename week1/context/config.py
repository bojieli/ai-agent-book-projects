"""
Configuration module for Context-Aware Agent
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


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
            return "Qwen/Qwen3-235B-A22B-Thinking-2507"
        elif provider == "doubao":
            return "doubao-seed-1-6-thinking-250715"
        elif provider == "kimi" or provider == "moonshot":
            return "kimi-k2-0905-preview"
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
            "temperature": cls.MODEL_TEMPERATURE,
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
