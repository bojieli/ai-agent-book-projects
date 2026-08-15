from typing import Optional

from aworld.core.memory import EmbeddingsConfig
from aworld.memory.embeddings.base import Embeddings


class EmbedderFactory:

    @staticmethod
    def get_embedder(config: EmbeddingsConfig) -> Optional[Embeddings]:
        if not config:
            return None
        if config.provider == "openai":
            from aworld.memory.embeddings.openai_compatible import OpenAICompatibleEmbeddings
            return OpenAICompatibleEmbeddings(config)
        elif config.provider == "ollama":
            from aworld.memory.embeddings.ollama import OllamaEmbeddings
            return OllamaEmbeddings(config)
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")