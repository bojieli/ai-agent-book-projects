import asyncio
import logging
import os

from dotenv import load_dotenv

from aworld.core.memory import AgentMemoryConfig
from aworld.memory.main import MemoryFactory
from aworld.memory.models import MessageMetadata, MemoryHumanMessage
from tests.memory.short_term.utils import add_mock_messages
from tests.memory.utils import init_postgres_memory


async def run():
    load_dotenv()
    # init_postgres_memory()
    memory = MemoryFactory.instance()
    metadata = MessageMetadata(
        user_id="user_id",
        session_id="session_id",
        task_id="task_id",
        agent_id="self_evolving_agent",
        agent_name="self_evolving_agent"
    )
    # Get and print all messages
    items = memory.get_all(filters={
        "user_id": metadata.user_id,
        "agent_id": metadata.agent_id,
        "session_id": metadata.session_id,
        "task_id": metadata.task_id
    })


    summary_config = AgentMemoryConfig(
        enable_summary=False,
        summary_rounds=2,
        summary_model="xxx"
    )

    await add_mock_messages(memory, metadata, memory_config=summary_config)
    await memory.add(MemoryHumanMessage(content="new1",metadata= metadata))
    await memory.add(MemoryHumanMessage(content="new2",metadata=metadata))
    await memory.add(MemoryHumanMessage(content="new3",metadata=metadata))


    retrival_memory = memory.get_last_n(last_rounds=6, filters={
        "user_id": metadata.user_id,
        "agent_id": metadata.agent_id,
        "session_id": metadata.session_id,
        "task_id": metadata.task_id
    })

    logging.info("==================  RETRIVAL  ==================")
    for item in retrival_memory:
        logging.info(f"{item.memory_type}: {item.content}")


if __name__ == '__main__':
    asyncio.run(run())
