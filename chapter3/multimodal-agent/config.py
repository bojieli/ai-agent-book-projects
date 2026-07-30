"""
Configuration for Multimodal Agent
Supports multiple providers and extraction modes
"""
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

load_dotenv()


def _openrouter_model_id(model) -> str:
    """Map a provider-native model name to an OpenRouter model id, used by the
    universal OpenRouter fallback. An explicit OPENROUTER_MODEL env var wins.
    Vision-capable default (gpt-5.6-luna) so image analysis still works."""
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
    if ml.startswith("gemini"):
        return "google/" + m  # e.g. gemini-3.5-flash -> google/gemini-3.5-flash
    # Provider-native ids (doubao-*/qwen/...) -> a widely-available vision model.
    return "openai/gpt-5.6-luna"


class ExtractionMode(Enum):
    """Modes for multimodal content extraction"""
    NATIVE = "native"  # Use model's native multimodal capabilities
    EXTRACT_TO_TEXT = "extract_to_text"  # Convert multimodal to text first
    

class Provider(Enum):
    """Supported model providers"""
    GEMINI = "gemini"
    OPENAI = "openai"
    DOUBAO = "doubao"
    

@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    provider: Provider
    model_name: str
    api_key: str
    base_url: Optional[str] = None
    supports_native_multimodal: bool = True
    

class Config:
    """Main configuration class for multimodal agent"""
    
    def __init__(self):
        # Load API keys from environment.
        # 兼容常见别名：Gemini 官方 SDK 用 GEMINI_API_KEY，旧文档用 GOOGLE_API_KEY，两者都接受；
        # 豆包/方舟(Ark)的 Key 环境变量常见为 DOUBAO_API_KEY 或 ARK_API_KEY。
        self.gemini_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.doubao_api_key = os.getenv("DOUBAO_API_KEY") or os.getenv("ARK_API_KEY", "")

        # Universal OpenRouter fallback: when a model's own provider key is
        # missing but OPENROUTER_API_KEY is present, route that model through
        # OpenRouter's OpenAI-compatible endpoint.
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.openrouter_base_url = "https://openrouter.ai/api/v1"
        
        # Model configurations
        self.models = {
            "gemini-3.5-flash": ModelConfig(
                provider=Provider.GEMINI,
                model_name="gemini-3.5-flash",
                api_key=self.gemini_api_key,
                supports_native_multimodal=True
            ),
            "gpt-5": ModelConfig(
                provider=Provider.OPENAI,
                model_name="gpt-5",
                api_key=self.openai_api_key,
                supports_native_multimodal=True
            ),
            "gpt-5.6-luna": ModelConfig(
                provider=Provider.OPENAI,
                model_name="gpt-5.6-luna",
                api_key=self.openai_api_key,
                supports_native_multimodal=True
            ),
            "doubao-1.6": ModelConfig(
                provider=Provider.DOUBAO,
                model_name=os.getenv("ARK_MODEL", "doubao-seed-1-6-250615"),
                api_key=self.doubao_api_key,
                base_url="https://ark.cn-beijing.volces.com/api/v3",
                supports_native_multimodal=True
            )
        }
        
        # Default settings
        self.default_model = os.getenv("MULTIMODAL_MODEL", "doubao-1.6")
        self.default_mode = ExtractionMode.NATIVE
        self.enable_multimodal_tools = False
        
        # File size limits (in MB)
        self.max_pdf_size_mb = 20
        self.max_image_size_mb = 20
        self.max_audio_size_mb = 25
        
        # Whisper settings for audio transcription
        self.whisper_model = "whisper-1"
        
        # Temperature settings
        self.temperature = 0.7
        self.max_tokens = 4096
        
    def get_model_config(self, model_name: str) -> ModelConfig:
        """Get configuration for a specific model"""
        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}")
        return self.models[model_name]
        
    def validate_api_keys(self) -> Dict[str, bool]:
        """Check which API keys are configured"""
        return {
            "gemini": bool(self.gemini_api_key),
            "openai": bool(self.openai_api_key),
            "doubao": bool(self.doubao_api_key),
            "openrouter": bool(self.openrouter_api_key)
        }

    def has_provider_key(self, provider: 'Provider') -> bool:
        """Whether the direct API key for a provider is configured."""
        if provider == Provider.OPENAI:
            return bool(self.openai_api_key)
        if provider == Provider.DOUBAO:
            return bool(self.doubao_api_key)
        if provider == Provider.GEMINI:
            return bool(self.gemini_api_key)
        return False

    def use_openrouter(self, provider: 'Provider') -> bool:
        """True when a model's own provider key is missing but OpenRouter is
        available -> the call should be routed through OpenRouter."""
        return (not self.has_provider_key(provider)) and bool(self.openrouter_api_key)

    def openai_client_args(self, model_config: 'ModelConfig'):
        """Return (client_kwargs, model_name) for an OpenAI-compatible call,
        applying the universal OpenRouter fallback when needed."""
        provider = model_config.provider
        _m = (model_config.model_name or "").lower()
        _prefer_or = bool(self.openrouter_api_key) and _m.startswith("gpt-5")  # 直连 gpt-5.6 需组织实名，优先 OpenRouter
        if _prefer_or or self.use_openrouter(provider):
            return (
                {"api_key": self.openrouter_api_key, "base_url": self.openrouter_base_url},
                _openrouter_model_id(model_config.model_name),
            )
        if provider == Provider.DOUBAO:
            return {"api_key": self.doubao_api_key, "base_url": model_config.base_url}, model_config.model_name
        # OPENAI (and any GEMINI forced through the OpenAI-compatible path)
        return {"api_key": self.openai_api_key}, model_config.model_name
