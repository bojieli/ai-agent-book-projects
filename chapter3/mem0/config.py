"""Configuration module for Mem0 agent with Kimi K3 integration."""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def _reasoning_safe_temperature(model, requested=1.0):
    """Reasoning models (Kimi K3, GPT-5, ...) only accept temperature=1.
    Return 1 for those; otherwise the requested value so non-reasoning
    providers (Doubao, DeepSeek, older Moonshot) are unchanged."""
    m = str(model or "").lower().replace("/", "-")
    return 1 if ("kimi-k3" in m or "gpt-5" in m) else requested


def _openrouter_model_id(model) -> str:
    """Map a provider-native model name to an OpenRouter model id, used by the
    universal OpenRouter fallback. An explicit OPENROUTER_MODEL env var wins."""
    override = os.getenv("OPENROUTER_MODEL")
    if override:
        return override
    m = (model or "").strip()
    if not m:
        return "openai/gpt-4o"
    if "/" in m:
        return m  # already an OpenRouter-style id (e.g. openai/gpt-4o)
    ml = m.lower()
    if ml.startswith(("gpt-", "o1", "o3", "o4", "chatgpt")):
        return "openai/" + m
    if ml.startswith("claude-"):
        return "anthropic/claude-3.5-sonnet"
    if ml.startswith("kimi"):
        # kimi-k3 is not on OpenRouter; moonshotai/kimi-k2.5 is the closest hosted id.
        return "moonshotai/kimi-k2.5"
    # Provider-native ids (kimi-*/doubao-*/qwen/deepseek-*) not hosted on
    # OpenRouter under the same name -> a widely-available OpenAI chat model.
    return "openai/gpt-4o"


@dataclass
class KimiConfig:
    """Configuration for Kimi K3 model."""

    api_key: str = field(default_factory=lambda: os.getenv("KIMI_API_KEY", ""))
    model_name: str = field(default_factory=lambda: os.getenv("MODEL_NAME", "kimi-k3"))
    max_tokens: int = field(default_factory=lambda: int(os.getenv("MAX_TOKENS", "128000")))
    temperature: float = field(default_factory=lambda: float(os.getenv("TEMPERATURE", "0.7")))
    api_base: str = field(default_factory=lambda: os.getenv("KIMI_API_BASE", "https://api.moonshot.cn/v1"))

    def __post_init__(self):
        """Universal OpenRouter fallback for the chat LLM: when KIMI_API_KEY is
        absent but OPENROUTER_API_KEY is present, route the chat model (used by
        KimiK3Client and threaded into mem0's own LLM config) through OpenRouter.
        NB: mem0's embedder still uses OpenAI embeddings (OpenRouter has no
        embeddings endpoint), so OPENAI_API_KEY remains needed for memory add."""
        if not self.api_key and os.getenv("OPENROUTER_API_KEY"):
            self.api_key = os.getenv("OPENROUTER_API_KEY")
            self.api_base = "https://openrouter.ai/api/v1"
            self.model_name = _openrouter_model_id(self.model_name)

    def validate(self) -> bool:
        """Validate Kimi configuration."""
        if not self.api_key:
            raise ValueError("KIMI_API_KEY is required (or set OPENROUTER_API_KEY for the fallback)")
        if self.max_tokens <= 0 or self.max_tokens > 128000:
            raise ValueError("MAX_TOKENS must be between 1 and 128000")
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("TEMPERATURE must be between 0 and 2")
        return True


@dataclass
class Mem0Config:
    """Configuration for Mem0 memory system."""
    
    api_key: Optional[str] = field(default_factory=lambda: os.getenv("MEM0_API_KEY"))
    backend: str = field(default_factory=lambda: os.getenv("MEMORY_BACKEND", "local"))
    collection_name: str = field(default_factory=lambda: os.getenv("MEMORY_COLLECTION", "locomo_benchmark"))
    embedding_model: str = field(default_factory=lambda: os.getenv("MEMORY_EMBEDDING_MODEL", "text-embedding-3-small"))
    vector_store_config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize vector store configuration based on backend."""
        if self.backend == "local":
            # NB: mem0 >=1.0 validates the chroma config against a fixed field
            # set (collection_name/path/host/port/api_key/tenant/client). The
            # embedding model belongs to the top-level "embedder" block (set in
            # agent.py), NOT here — passing embedding_function raises a
            # MemoryConfig validation error.
            self.vector_store_config = {
                "provider": "chroma",
                "config": {
                    "collection_name": self.collection_name,
                    "path": "./data/chroma_db",
                }
            }
        elif self.backend == "cloud":
            if not self.api_key:
                raise ValueError("MEM0_API_KEY is required for cloud backend")
            self.vector_store_config = {
                "provider": "mem0_cloud",
                "config": {
                    "api_key": self.api_key,
                    "collection_name": self.collection_name
                }
            }
        else:
            raise ValueError(f"Invalid backend: {self.backend}. Must be 'local' or 'cloud'")
    
    def validate(self) -> bool:
        """Validate Mem0 configuration."""
        if self.backend not in ["local", "cloud"]:
            raise ValueError("MEMORY_BACKEND must be 'local' or 'cloud'")
        if self.backend == "cloud" and not self.api_key:
            raise ValueError("MEM0_API_KEY is required for cloud backend")
        return True


@dataclass
class LOCOMOConfig:
    """Configuration for LOCOMO benchmark."""
    
    data_path: Path = field(default_factory=lambda: Path(os.getenv("BENCHMARK_DATA_PATH", "./data/locomo")))
    max_sessions: int = field(default_factory=lambda: int(os.getenv("MAX_SESSIONS", "100")))
    max_agents: int = field(default_factory=lambda: int(os.getenv("MAX_AGENTS", "10")))
    context_window_size: int = field(default_factory=lambda: int(os.getenv("CONTEXT_WINDOW_SIZE", "128000")))
    evaluation_metrics: list = field(default_factory=lambda: [
        "consistency_score",
        "coherence_score",
        "memory_retention",
        "context_utilization",
        "response_relevance"
    ])
    
    def __post_init__(self):
        """Ensure data path exists."""
        self.data_path.mkdir(parents=True, exist_ok=True)
    
    def validate(self) -> bool:
        """Validate LOCOMO configuration."""
        if self.max_sessions <= 0:
            raise ValueError("MAX_SESSIONS must be positive")
        if self.max_agents <= 0:
            raise ValueError("MAX_AGENTS must be positive")
        if self.context_window_size <= 0:
            raise ValueError("CONTEXT_WINDOW_SIZE must be positive")
        return True


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    
    level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    file_path: Optional[Path] = field(default_factory=lambda: Path(os.getenv("LOG_FILE", "./logs/mem0_agent.log")) if os.getenv("LOG_FILE") else None)
    
    def __post_init__(self):
        """Ensure log directory exists."""
        if self.file_path:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class Config:
    """Main configuration class."""
    
    kimi: KimiConfig = field(default_factory=KimiConfig)
    mem0: Mem0Config = field(default_factory=Mem0Config)
    locomo: LOCOMOConfig = field(default_factory=LOCOMOConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    def validate(self) -> bool:
        """Validate all configurations."""
        self.kimi.validate()
        self.mem0.validate()
        self.locomo.validate()
        return True
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "kimi": {
                "model_name": self.kimi.model_name,
                "max_tokens": self.kimi.max_tokens,
                "temperature": _reasoning_safe_temperature(self.kimi.model_name, self.kimi.temperature),
                "api_base": self.kimi.api_base
            },
            "mem0": {
                "backend": self.mem0.backend,
                "collection_name": self.mem0.collection_name,
                "embedding_model": self.mem0.embedding_model
            },
            "locomo": {
                "data_path": str(self.locomo.data_path),
                "max_sessions": self.locomo.max_sessions,
                "max_agents": self.locomo.max_agents,
                "context_window_size": self.locomo.context_window_size,
                "evaluation_metrics": self.locomo.evaluation_metrics
            },
            "logging": {
                "level": self.logging.level,
                "file_path": str(self.logging.file_path) if self.logging.file_path else None
            }
        }


# Global configuration instance
config = Config.from_env()
