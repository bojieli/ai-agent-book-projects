"""
Configuration for structured index project.
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def _openrouter_model_id(model) -> str:
    """Map a provider-native model name to an OpenRouter model id, used by the
    universal OpenRouter fallback. An explicit OPENROUTER_MODEL env var wins."""
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
    if ml.startswith("kimi"):
        # kimi-k3 is not on OpenRouter; moonshotai/kimi-k2.6 is the closest hosted id.
        return "moonshotai/kimi-k2.6"
    return "openai/gpt-5.6-luna"


def _resolve_llm(api_key: str, *models):
    """Return (api_key, base_url, *mapped_models). When the OpenAI key is
    absent but OPENROUTER_API_KEY is present, route the chat LLM (used for
    RAPTOR summarization / GraphRAG entity extraction) through OpenRouter.
    Embeddings here are local SentenceTransformers, so they are unaffected."""
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    # gpt-5.x (incl. gpt-5.6*) needs OpenAI org-verification on the direct API;
    # when an OpenRouter key is present, prefer routing these ids through it.
    prefer_openrouter = bool(openrouter_key) and any(
        str(m or "").lower().startswith("gpt-5") for m in models)
    if (not api_key or prefer_openrouter) and openrouter_key:
        base_url = "https://openrouter.ai/api/v1"
        return (openrouter_key, base_url,
                *[_openrouter_model_id(m) for m in models])
    return (api_key, None, *models)


@dataclass
class RaptorConfig:
    """Configuration for RAPTOR tree-based indexing."""
    openai_api_key: str
    model_name: str = "gpt-5.6-luna"
    embedding_model: str = "text-embedding-3-small"
    max_tokens: int = 2048
    temperature: float = 0.1
    chunk_size: int = 1000
    chunk_overlap: int = 200
    tree_depth: int = 3
    summarization_length: int = 200
    index_dir: Path = Path("indexes/raptor")
    base_url: Optional[str] = None


@dataclass
class GraphRAGConfig:
    """Configuration for GraphRAG graph-based indexing."""
    llm_api_key: str
    llm_model: str = "gpt-5.6-luna"
    embedding_model: str = "text-embedding-3-small"
    chunk_size: int = 1200
    chunk_overlap: int = 100
    max_knowledge_triples: int = 10
    community_detection_algorithm: str = "leiden"
    summarization_model: str = "gpt-5.6-luna"
    index_dir: Path = Path("indexes/graphrag")
    cache_dir: Path = Path("cache/graphrag")
    base_url: Optional[str] = None


@dataclass
class APIConfig:
    """Configuration for HTTP API service."""
    host: str = "127.0.0.1"
    port: int = 4242
    reload: bool = True
    max_results: int = 10
    timeout_seconds: int = 30


def get_raptor_config() -> RaptorConfig:
    """Get RAPTOR configuration from environment."""
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    provider = {"qwen": "dashscope", "bailian": "dashscope"}.get(provider, provider)
    openai_key = os.getenv("OPENAI_API_KEY", "")
    dashscope_key = os.getenv("DASHSCOPE_API_KEY", "")
    ark_key = os.getenv("ARK_API_KEY") or os.getenv("DOUBAO_API_KEY", "")
    direct_key = dashscope_key if provider == "dashscope" else (openai_key or ark_key)
    default_model = (
        os.getenv("RAPTOR_MODEL", "qwen3.7-plus")
        if provider == "dashscope"
        else (
        os.getenv("ARK_MODEL", "doubao-seed-1-6-250615")
        if ark_key and not openai_key
        else "gpt-5.6-luna")
    )
    api_key, base_url, model_name = _resolve_llm(
        direct_key,
        os.getenv("RAPTOR_MODEL", default_model),
    )
    if base_url is None and provider == "dashscope":
        base_url = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    elif base_url is None and ark_key and not openai_key:
        base_url = "https://ark.cn-beijing.volces.com/api/v3"
    return RaptorConfig(
        openai_api_key=api_key,
        model_name=model_name,
        embedding_model=os.getenv("RAPTOR_EMBEDDING_MODEL", "text-embedding-3-small"),
        max_tokens=int(os.getenv("RAPTOR_MAX_TOKENS", "2048")),
        temperature=float(os.getenv("RAPTOR_TEMPERATURE", "0.1")),
        chunk_size=int(os.getenv("RAPTOR_CHUNK_SIZE", "1000")),
        chunk_overlap=int(os.getenv("RAPTOR_CHUNK_OVERLAP", "200")),
        tree_depth=int(os.getenv("RAPTOR_TREE_DEPTH", "3")),
        summarization_length=int(os.getenv("RAPTOR_SUMMARY_LENGTH", "200")),
        base_url=base_url,
    )


def get_graphrag_config() -> GraphRAGConfig:
    """Get GraphRAG configuration from environment."""
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    provider = {"qwen": "dashscope", "bailian": "dashscope"}.get(provider, provider)
    openai_key = os.getenv("OPENAI_API_KEY", "")
    dashscope_key = os.getenv("DASHSCOPE_API_KEY", "")
    ark_key = os.getenv("ARK_API_KEY") or os.getenv("DOUBAO_API_KEY", "")
    direct_key = dashscope_key if provider == "dashscope" else (openai_key or ark_key)
    default_model = (
        os.getenv("GRAPHRAG_MODEL", "qwen3.7-plus")
        if provider == "dashscope"
        else (
        os.getenv("ARK_MODEL", "doubao-seed-1-6-250615")
        if ark_key and not openai_key
        else "gpt-5.6-luna")
    )
    api_key, base_url, llm_model, summ_model = _resolve_llm(
        direct_key,
        os.getenv("GRAPHRAG_MODEL", default_model),
        os.getenv("GRAPHRAG_SUMMARY_MODEL", default_model),
    )
    if base_url is None and provider == "dashscope":
        base_url = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    elif base_url is None and ark_key and not openai_key:
        base_url = "https://ark.cn-beijing.volces.com/api/v3"
    return GraphRAGConfig(
        llm_api_key=api_key,
        llm_model=llm_model,
        embedding_model=os.getenv("GRAPHRAG_EMBEDDING_MODEL", "text-embedding-3-small"),
        chunk_size=int(os.getenv("GRAPHRAG_CHUNK_SIZE", "1200")),
        chunk_overlap=int(os.getenv("GRAPHRAG_CHUNK_OVERLAP", "100")),
        max_knowledge_triples=int(os.getenv("GRAPHRAG_MAX_TRIPLES", "10")),
        community_detection_algorithm=os.getenv("GRAPHRAG_COMMUNITY_ALG", "leiden"),
        summarization_model=summ_model,
        base_url=base_url,
    )


def get_api_config() -> APIConfig:
    """Get API configuration from environment."""
    return APIConfig(
        host=os.getenv("API_HOST", "127.0.0.1"),
        port=int(os.getenv("API_PORT", "4242")),
        reload=os.getenv("API_RELOAD", "true").lower() == "true",
        max_results=int(os.getenv("API_MAX_RESULTS", "10")),
        timeout_seconds=int(os.getenv("API_TIMEOUT", "30"))
    )
