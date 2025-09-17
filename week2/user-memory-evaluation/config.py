"""Configuration module for User Memory Evaluation Framework."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration settings for the evaluation framework."""
    
    # Kimi API Settings (also accept MOONSHOT_API_KEY for compatibility)
    KIMI_API_KEY: str = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY", "")
    KIMI_BASE_URL: str = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
    KIMI_MODEL: str = os.getenv("KIMI_MODEL", "moonshot-v1-32k")
    
    # OpenAI API Settings (alternative)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    
    # Evaluation Settings
    DEFAULT_EVALUATOR: str = os.getenv("DEFAULT_EVALUATOR", "kimi")
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "60"))
    
    # Test Case Settings
    TEST_CASES_DIR: str = os.path.join(os.path.dirname(__file__), "test_cases")
    
    @classmethod
    def get_evaluator_config(cls, evaluator: Optional[str] = None) -> dict:
        """Get configuration for the specified evaluator."""
        evaluator = evaluator or cls.DEFAULT_EVALUATOR
        
        if evaluator == "kimi":
            if not cls.KIMI_API_KEY:
                raise ValueError("KIMI_API_KEY not configured. Please set it in .env file.")
            return {
                "api_key": cls.KIMI_API_KEY,
                "base_url": cls.KIMI_BASE_URL,
                "model": cls.KIMI_MODEL,
                "type": "kimi"
            }
        elif evaluator == "openai":
            if not cls.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not configured. Please set it in .env file.")
            return {
                "api_key": cls.OPENAI_API_KEY,
                "base_url": cls.OPENAI_BASE_URL,
                "model": cls.OPENAI_MODEL,
                "type": "openai"
            }
        else:
            raise ValueError(f"Unknown evaluator: {evaluator}. Supported: kimi, openai")
