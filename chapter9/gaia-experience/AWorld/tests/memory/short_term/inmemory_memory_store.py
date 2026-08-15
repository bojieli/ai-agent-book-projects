import asyncio
import logging

from dotenv import load_dotenv

from aworld.memory.main import MemoryFactory
from aworld.memory.models import MessageMetadata
from tests.memory.short_term.utils import add_mock_messages


async def run():
    load_dotenv()
    MemoryFactory.init()
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


# if __name__ == '__main__':
#     asyncio.run(run())
