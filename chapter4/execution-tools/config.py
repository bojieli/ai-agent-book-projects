"""Configuration management for the execution tools MCP server."""

import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def _env_int(name: str, default: int) -> int:
    """Read an integer env var; fall back to default (with a warning) if malformed."""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        print(f"Warning: invalid {name}={raw!r} (must be an integer); using default {default}",
              file=sys.stderr)
        return default


def _env_float(name: str, default: float) -> float:
    """Read a float env var; fall back to default (with a warning) if malformed."""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        print(f"Warning: invalid {name}={raw!r} (must be a number); using default {default}",
              file=sys.stderr)
        return default


class Config:
    """Configuration for the MCP server."""
    
    # LLM Configuration
    PROVIDER: str = os.getenv("PROVIDER", "kimi")
    
    # API Keys
    DASHSCOPE_API_KEY: Optional[str] = os.getenv("DASHSCOPE_API_KEY")
    SILICONFLOW_API_KEY: Optional[str] = os.getenv("SILICONFLOW_API_KEY")
    DOUBAO_API_KEY: Optional[str] = os.getenv("DOUBAO_API_KEY")
    KIMI_API_KEY: Optional[str] = os.getenv("KIMI_API_KEY")
    MOONSHOT_API_KEY: Optional[str] = os.getenv("MOONSHOT_API_KEY")
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    DASHSCOPE_BASE_URL: str = os.getenv(
        "DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    
    # Model names (optional, defaults to provider defaults)
    MODEL: Optional[str] = os.getenv("MODEL")
    
    # Model parameters
    TEMPERATURE: float = _env_float("TEMPERATURE", 0.7)
    MAX_TOKENS: int = _env_int("MAX_TOKENS", 4096)
    
    # External Services
    GOOGLE_CALENDAR_CREDENTIALS_FILE: str = os.getenv(
        "GOOGLE_CALENDAR_CREDENTIALS_FILE", 
        "credentials.json"
    )
    GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN")
    
    # Safety Settings
    REQUIRE_APPROVAL_FOR_DANGEROUS_OPS: bool = (
        os.getenv("REQUIRE_APPROVAL_FOR_DANGEROUS_OPS", "true").lower() == "true"
    )
    AUTO_SUMMARIZE_COMPLEX_OUTPUT: bool = (
        os.getenv("AUTO_SUMMARIZE_COMPLEX_OUTPUT", "true").lower() == "true"
    )
    AUTO_VERIFY_CODE: bool = (
        os.getenv("AUTO_VERIFY_CODE", "true").lower() == "true"
    )
    MAX_OUTPUT_LENGTH: int = _env_int("MAX_OUTPUT_LENGTH", 1000)
    
    # Workspace Configuration
    WORKSPACE_DIR: Path = Path(os.getenv("WORKSPACE_DIR", os.getcwd()))
    
    @classmethod
    def get_api_key(cls, provider: str) -> Optional[str]:
        """Get API key for the specified provider."""
        provider = provider.lower()
        provider = {"qwen": "dashscope", "bailian": "dashscope"}.get(provider, provider)
        if provider == "dashscope":
            return cls.DASHSCOPE_API_KEY
        elif provider == "siliconflow":
            return cls.SILICONFLOW_API_KEY
        elif provider == "doubao":
            return cls.DOUBAO_API_KEY
        elif provider in ["kimi", "moonshot"]:
            return cls.KIMI_API_KEY or cls.MOONSHOT_API_KEY
        elif provider == "openrouter":
            return cls.OPENROUTER_API_KEY
        return None
    
    @classmethod
    def effective_provider(cls) -> str:
        """Resolve the provider actually used, applying the OpenRouter fallback.

        Preserves default behavior when the configured provider's key is
        present. Otherwise, if an OPENROUTER_API_KEY is available, transparently
        fall back to 'openrouter' so the tools still run with only that key set.
        """
        provider = cls.PROVIDER.lower()
        provider = {"qwen": "dashscope", "bailian": "dashscope"}.get(provider, provider)
        if cls.get_api_key(provider):
            return provider
        if cls.OPENROUTER_API_KEY:
            return "openrouter"
        return provider

    @classmethod
    def validate(cls) -> None:
        """Validate the configuration."""
        provider = cls.effective_provider()
        api_key = cls.get_api_key(provider)

        if not api_key:
            raise ValueError(
                f"API key required for provider '{cls.PROVIDER.lower()}'. "
                f"Set one of {cls.PROVIDER.upper()}_API_KEY or OPENROUTER_API_KEY "
                f"(universal fallback)."
            )

    @classmethod
    def get_llm_config(cls) -> dict:
        """Get LLM configuration based on provider."""
        provider = cls.effective_provider()
        api_key = cls.get_api_key(provider)

        if not api_key:
            raise ValueError(
                f"API key not found for provider '{cls.PROVIDER.lower()}'. "
                f"Set {cls.PROVIDER.upper()}_API_KEY or OPENROUTER_API_KEY."
            )
        
        if provider == "dashscope":
            return {
                "provider": "dashscope",
                "api_key": api_key,
                "base_url": cls.DASHSCOPE_BASE_URL,
                "model": cls.MODEL or "qwen3.7-plus"
            }
        elif provider == "siliconflow":
            return {
                "provider": "siliconflow",
                "api_key": api_key,
                "base_url": "https://api.siliconflow.cn/v1",
                "model": cls.MODEL or "Qwen/Qwen3-235B-A22B-Thinking-2507"
            }
        elif provider == "doubao":
            return {
                "provider": "doubao",
                "api_key": api_key,
                "base_url": "https://ark.cn-beijing.volces.com/api/v3",
                "model": cls.MODEL or "doubao-seed-1-6-thinking-250715"
            }
        elif provider in ["kimi", "moonshot"]:
            return {
                "provider": "kimi",
                "api_key": api_key,
                "base_url": "https://api.moonshot.cn/v1",
                "model": cls.MODEL or "kimi-k3"
            }
        elif provider == "openrouter":
            return {
                "provider": "openrouter",
                "api_key": api_key,
                "base_url": "https://openrouter.ai/api/v1",
                "model": cls.MODEL or "google/gemini-3.5-flash"
            }
        else:
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Use 'dashscope'/'qwen'/'bailian', 'siliconflow', 'doubao', 'kimi', 'moonshot', or 'openrouter'"
            )


# Note: configuration is validated lazily when the LLM is actually used
# (see LLMHelper), so that execution tools which do not require an LLM
# (file write, code run, terminal) can be used offline without an API key.
