"""Configuration for Agentic RAG User Memory Evaluation System"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def _reasoning_safe_temperature(model, requested=1.0):
    """Reasoning models (Kimi K3, GPT-5, ...) only accept temperature=1.
    Return 1 for those; otherwise the requested value so non-reasoning
    providers (Doubao, DeepSeek, older Moonshot) are unchanged."""
    m = str(model or "").lower().replace("/", "-")
    return 1 if ("kimi-k3" in m or "gpt-5" in m) else requested


def _openrouter_model_id(model: Optional[str]) -> str:
    """Map a provider-native model name to an OpenRouter model id, used by the
    universal OpenRouter fallback. An explicit OPENROUTER_MODEL env var wins."""
    override = os.getenv("OPENROUTER_MODEL")
    if override:
        return override
    m = (model or "").strip()
    if not m:
        return "openai/gpt-5.6-luna"
    if "/" in m:
        return m  # already an OpenRouter-style id (e.g. openai/gpt-5.6-luna)
    ml = m.lower()
    if ml.startswith(("gpt-", "o1", "o3", "o4", "chatgpt")):
        return "openai/" + m
    if ml.startswith("claude-"):
        return "anthropic/claude-opus-4.8"
    if ml.startswith("kimi"):
        # kimi-k3 is not on OpenRouter; moonshotai/kimi-k2.6 is the closest hosted id.
        return "moonshotai/kimi-k2.6"
    # Provider-native ids (kimi-*/doubao-*/qwen/deepseek-*) not hosted on
    # OpenRouter under the same name -> a widely-available OpenAI chat model.
    return "openai/gpt-5.6-luna"


class Provider(str, Enum):
    """Supported LLM providers"""
    DASHSCOPE = "dashscope"  # Alibaba Cloud Model Studio / Bailian (Qwen)
    SILICONFLOW = "siliconflow"
    DOUBAO = "doubao"
    KIMI = "kimi"
    MOONSHOT = "moonshot"
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    GROQ = "groq"
    TOGETHER = "together"
    DEEPSEEK = "deepseek"


class IndexMode(str, Enum):
    """Indexing modes for conversation chunks"""
    DENSE = "dense"  # Dense embedding only
    SPARSE = "sparse"  # Sparse embedding only (BM25)
    HYBRID = "hybrid"  # Both dense and sparse


class ChunkingStrategy(str, Enum):
    """Strategies for chunking conversations"""
    FIXED_ROUNDS = "fixed_rounds"  # Fixed number of rounds per chunk
    SEMANTIC = "semantic"  # Semantic boundaries
    TIME_BASED = "time_based"  # Based on timestamp gaps


@dataclass
class LLMConfig:
    """LLM configuration"""
    provider: str = "kimi"  # Default provider
    model: Optional[str] = None  # Will use provider defaults if not specified
    api_key: Optional[str] = None  # Will read from env if not provided
    temperature: float = 0.7
    max_tokens: int = 2048
    stream: bool = True
    
    # Provider-specific defaults
    PROVIDER_DEFAULTS = {
        "dashscope": {
            "model": "qwen3.7-plus",
            "base_url": os.getenv(
                "DASHSCOPE_BASE_URL",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            ),
        },
        "siliconflow": {
            "model": "Qwen/Qwen3-235B-A22B-Thinking-2507",
            "base_url": "https://api.siliconflow.cn/v1"
        },
        "doubao": {
            "model": "doubao-seed-1-6-thinking-250715",
            "base_url": "https://ark.cn-beijing.volces.com/api/v3"
        },
        "kimi": {
            "model": "kimi-k3",
            "base_url": "https://api.moonshot.cn/v1"
        },
        "moonshot": {
            "model": "kimi-k3",
            "base_url": "https://api.moonshot.cn/v1"
        },
        "openrouter": {
            "model": "openai/gpt-5.6-luna",
            "base_url": "https://openrouter.ai/api/v1"
        },
        "openai": {
            "model": "gpt-5.6-luna",
            "base_url": "https://api.openai.com/v1"
        },
        "groq": {
            "model": "llama-3.3-70b-versatile",
            "base_url": "https://api.groq.com/openai/v1"
        },
        "together": {
            "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "base_url": "https://api.together.xyz"
        },
        "deepseek": {
            "model": "deepseek-reasoner",
            "base_url": "https://api.deepseek.com/v1"
        }
    }
    
    def get_client_config(self) -> tuple[Dict[str, Any], str]:
        """Get OpenAI client configuration"""
        provider = self.provider.lower()
        provider = {"qwen": "dashscope", "bailian": "dashscope"}.get(
            provider, provider
        )
        defaults = self.PROVIDER_DEFAULTS.get(provider, {})
        
        # Determine API key
        api_key = self.api_key or os.getenv(f"{provider.upper()}_API_KEY")
        if not api_key and provider == "moonshot":
            api_key = os.getenv("KIMI_API_KEY")  # Fallback for moonshot

        # Determine model
        model = self.model or defaults.get("model", "gpt-5.6-luna")

        # Universal OpenRouter fallback: primary provider key absent but
        # OPENROUTER_API_KEY present -> route through OpenRouter.
        if not api_key and provider != "openrouter" and os.getenv("OPENROUTER_API_KEY"):
            return {
                "api_key": os.getenv("OPENROUTER_API_KEY"),
                "base_url": "https://openrouter.ai/api/v1",
            }, _openrouter_model_id(model)

        # Build client config
        client_config = {"api_key": api_key}
        
        # Add base URL if needed
        if base_url := defaults.get("base_url"):
            client_config["base_url"] = base_url
        
        return client_config, model


@dataclass
class ChunkingConfig:
    """Configuration for conversation chunking"""
    strategy: ChunkingStrategy = ChunkingStrategy.FIXED_ROUNDS
    rounds_per_chunk: int = 20  # Number of rounds per chunk for FIXED_ROUNDS
    overlap_rounds: int = 2  # Number of overlapping rounds between chunks
    include_metadata: bool = True  # Include conversation metadata in chunks
    min_chunk_size: int = 5  # Minimum number of rounds in a chunk
    max_chunk_size: int = 50  # Maximum number of rounds in a chunk


@dataclass
class IndexConfig:
    """Configuration for RAG indexing"""
    mode: IndexMode = IndexMode.HYBRID
    embedding_model: str = "text-embedding-3-small"  # OpenAI embedding model
    embedding_dim: int = 1536  # Dimension of embeddings
    index_path: str = "indexes/memory_index"
    chunk_store_path: str = "data/chunk_store.json"
    enable_contextual: bool = True  # Add contextual information to chunks
    contextual_window: int = 2  # Number of surrounding rounds for context
    # Retrieval backend selection:
    #   "auto"     -> use the port-4242 retrieval pipeline if reachable, otherwise fall back
    #                 to a built-in, dependency-free local BM25 index (works fully offline)
    #   "local"    -> always use the built-in local BM25 index (no external service needed)
    #   "pipeline" -> always use the external retrieval pipeline on port 4242
    retrieval_backend: str = "auto"
    retrieval_url: str = "http://localhost:4242"  # External retrieval pipeline endpoint


@dataclass
class EvaluationConfig:
    """Configuration for evaluation framework"""
    test_cases_dir: str = "../user-memory-evaluation/test_cases"
    results_dir: str = "results"
    enable_verbose: bool = True
    save_trajectories: bool = True
    max_iterations: int = 10  # Max iterations for ReAct pattern
    enable_caching: bool = True  # Cache indexed conversations


@dataclass
class AgentConfig:
    """Agent behavior configuration"""
    enable_reasoning: bool = True  # Show reasoning steps
    enable_citations: bool = True  # Include citations in responses
    max_search_results: int = 5  # Maximum search results to consider
    confidence_threshold: float = 0.7  # Minimum confidence for answers
    enable_multi_search: bool = True  # Allow multiple searches per query
    max_searches_per_query: int = 3  # Maximum searches allowed


@dataclass
class Config:
    """Main configuration container"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    index: IndexConfig = field(default_factory=IndexConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables"""
        config = cls()
        
        # Override with environment variables
        if provider := os.getenv("LLM_PROVIDER"):
            config.llm.provider = provider
        
        if model := os.getenv("LLM_MODEL"):
            config.llm.model = model
        
        if rounds := os.getenv("ROUNDS_PER_CHUNK"):
            config.chunking.rounds_per_chunk = int(rounds)
        
        if index_mode := os.getenv("INDEX_MODE"):
            config.index.mode = IndexMode(index_mode)

        if backend := os.getenv("RETRIEVAL_BACKEND"):
            config.index.retrieval_backend = backend

        if test_cases_dir := os.getenv("TEST_CASES_DIR"):
            config.evaluation.test_cases_dir = test_cases_dir

        return config
    
    def save(self, path: str):
        """Save configuration to JSON file"""
        import json
        
        config_dict = {
            "llm": {
                "provider": self.llm.provider,
                "model": self.llm.model,
                "temperature": _reasoning_safe_temperature(self.llm.model, self.llm.temperature),
                "max_tokens": self.llm.max_tokens,
                "stream": self.llm.stream
            },
            "chunking": {
                "strategy": self.chunking.strategy,
                "rounds_per_chunk": self.chunking.rounds_per_chunk,
                "overlap_rounds": self.chunking.overlap_rounds,
                "include_metadata": self.chunking.include_metadata
            },
            "index": {
                "mode": self.index.mode,
                "embedding_model": self.index.embedding_model,
                "enable_contextual": self.index.enable_contextual,
                "contextual_window": self.index.contextual_window
            },
            "evaluation": {
                "enable_verbose": self.evaluation.enable_verbose,
                "save_trajectories": self.evaluation.save_trajectories,
                "max_iterations": self.evaluation.max_iterations
            },
            "agent": {
                "enable_reasoning": self.agent.enable_reasoning,
                "enable_citations": self.agent.enable_citations,
                "max_search_results": self.agent.max_search_results,
                "confidence_threshold": self.agent.confidence_threshold
            }
        }
        
        with open(path, 'w') as f:
            json.dump(config_dict, f, indent=2)
    
    @classmethod
    def load(cls, path: str) -> "Config":
        """Load configuration from JSON file"""
        import json

        with open(path, 'r') as f:
            config_dict = json.load(f)
        
        config = cls()
        
        # Update LLM config
        if "llm" in config_dict:
            for key, value in config_dict["llm"].items():
                setattr(config.llm, key, value)
        
        # Update other configs similarly
        for section in ["chunking", "index", "evaluation", "agent"]:
            if section in config_dict:
                section_config = getattr(config, section)
                for key, value in config_dict[section].items():
                    # Handle enums
                    if key == "strategy" and section == "chunking":
                        value = ChunkingStrategy(value)
                    elif key == "mode" and section == "index":
                        value = IndexMode(value)
                    setattr(section_config, key, value)
        
        return config
