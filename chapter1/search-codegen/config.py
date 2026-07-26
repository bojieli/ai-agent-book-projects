"""
Configuration for GPT-5 Native Tools Agent
"""

import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for GPT-5 Agent"""
    
    # API Configuration
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    
    # Model Configuration
    MODEL_NAME: str = os.getenv("MODEL_NAME", "openai/gpt-5.6-sol")
    
    # Request Configuration
    DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.3"))
    DEFAULT_MAX_TOKENS: Optional[int] = int(os.getenv("DEFAULT_MAX_TOKENS", "4000")) if os.getenv("DEFAULT_MAX_TOKENS") else None
    DEFAULT_TOOL_CHOICE: str = os.getenv("DEFAULT_TOOL_CHOICE", "auto")
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Rate Limiting (requests per minute)
    RATE_LIMIT_RPM: int = int(os.getenv("RATE_LIMIT_RPM", "20"))
    
    # Retry Configuration
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY: float = float(os.getenv("RETRY_DELAY", "1.0"))
    
    # Tool-specific Configuration
    WEB_SEARCH_MAX_RESULTS: int = int(os.getenv("WEB_SEARCH_MAX_RESULTS", "5"))
    CODE_INTERPRETER_TIMEOUT: int = int(os.getenv("CODE_INTERPRETER_TIMEOUT", "30"))
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate the configuration
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if not cls.OPENROUTER_API_KEY:
            print("Error: OPENROUTER_API_KEY is not set")
            return False
        
        if not cls.OPENROUTER_API_KEY.startswith("sk-or-"):
            print("Warning: OPENROUTER_API_KEY does not look like an OpenRouter key")
        
        return True
    
    @classmethod
    def display(cls):
        """Display current configuration (hiding sensitive data)"""
        print("=== GPT-5 Agent Configuration ===")
        print(f"API Base URL: {cls.OPENROUTER_BASE_URL}")
        print(f"Model: {cls.MODEL_NAME}")
        print(f"API Key: {'*' * 20 + cls.OPENROUTER_API_KEY[-4:] if cls.OPENROUTER_API_KEY else 'NOT SET'}")
        print(f"Temperature: {cls.DEFAULT_TEMPERATURE}")
        print(f"Max Tokens: {cls.DEFAULT_MAX_TOKENS}")
        print(f"Tool Choice: {cls.DEFAULT_TOOL_CHOICE}")
        print(f"Rate Limit: {cls.RATE_LIMIT_RPM} RPM")
        print("================================")


# Convenience function for quick configuration check
def check_config() -> bool:
    """
    Quick configuration check
    
    Returns:
        True if configuration is valid
    """
    return Config.validate()
