import asyncio
import logging

from dotenv import load_dotenv

from aworld.core.memory import MemoryConfig, VectorDBConfig, EmbeddingsConfig
from aworld.memory.main import MemoryFactory
from aworld.memory.models import MessageMetadata
from tests.memory.short_term.utils import add_mock_messages

async def init():
    load_dotenv()
    MemoryFactory.init(config=MemoryConfig(
        provider="aworld",
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

async def run():
    await init()
    memory = MemoryFactory.instance()
    metadata = MessageMetadata(
        user_id="zues",
        session_id="session#foo",
        task_id="zues:session#foo:task#1",
        agent_id="super_agent",
        agent_name="super_agent"
    )

    await add_mock_messages(memory, metadata)

    # Get and print all messages
    items = memory.get_all(filters={
        "user_id": metadata.user_id,
        "agent_id": metadata.user_id,
        "session_id": metadata.session_id,
        "task_id": metadata.session_id
    })
    for item in items:
        logging.info(f"{type(item)}: {item.content}")


async def run_search():
    memory = MemoryFactory.instance()
    metadata = MessageMetadata(
        user_id="zues",
        session_id="session#foo",
        task_id="zues:session#foo:task#1",
        agent_id="super_agent",
        agent_name="super_agent"
    )
    results = memory.search("recommend some outdoor sports", limit=10, filters={
        "user_id": metadata.user_id,
        "agent_id": metadata.user_id,
        "session_id": metadata.session_id,
        "task_id": metadata.session_id
    })
    for result in results:
        logging.info(f"search result {type(result)}: {result.id}[{result.metadata['score']}]{result.content}")


# if __name__ == '__main__':
#     asyncio.run(run())
#     asyncio.run(run_search())
