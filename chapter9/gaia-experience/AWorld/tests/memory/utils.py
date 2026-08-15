import os

from dotenv import load_dotenv

from aworld.core.memory import MemoryConfig, EmbeddingsConfig, VectorDBConfig, \
    MemoryLLMConfig
from aworld.memory.db.postgres import PostgresMemoryStore
from aworld.memory.main import MemoryFactory


def init_memory():
    load_dotenv()

    MemoryFactory.init(
        config=MemoryConfig(
            provider="aworld",
            llm_config=MemoryLLMConfig(
                provider="openai",
                model_name=os.environ["LLM_MODEL_NAME"],
                api_key=os.environ["LLM_API_KEY"],
                base_url=os.environ["LLM_BASE_URL"]
            ),
            embedding_config=EmbeddingsConfig(
                provider="ollama",
                base_url="http://localhost:11434",
                model_name="nomic-embed-text"
            ),
            vector_store_config=VectorDBConfig(
                provider="chroma",
                config=
                {
                    "chroma_data_path": "./chroma_db",
                    "collection_name": "aworld",
                }
            )
        ))


def init_postgres_memory():
    load_dotenv()
    postgres_memory_store = PostgresMemoryStore(db_url=os.getenv("MEMORY_STORE_POSTGRES_DSN"))

    MemoryFactory.init(
        custom_memory_store=postgres_memory_store,
        config=MemoryConfig(
            provider="aworld",
            llm_config=MemoryLLMConfig(
                provider="openai",
                model_name=os.environ["LLM_MODEL_NAME"],
                api_key=os.environ["LLM_API_KEY"],
                base_url=os.environ["LLM_BASE_URL"]
            ),
            embedding_config=EmbeddingsConfig(
                provider="ollama",
                base_url="http://localhost:11434",
                model_name="nomic-embed-text"
            ),
            vector_store_config=VectorDBConfig(
                provider="chroma",
                config=
                {
                    "chroma_data_path": "./chroma_db",
                    "collection_name": "aworld",
                }
            )
        ))

