# Initialize AworldTaskClient with server endpoints
import asyncio
import random
import uuid

from base import AworldTask
from client.aworld_client import AworldTaskClient

AWORLD_TASK_CLIENT = AworldTaskClient(
    know_hosts=["localhost:9999"]
)


async def _run_web_task(web_question_id: str) -> None:
    """Run a single Web task with the given question ID.

    Args:
        web_question_id: The ID of the question to process
    """
    global AWORLD_TASK_CLIENT
    task_id = str(uuid.uuid4())

    # Submit task to Aworld server
    await AWORLD_TASK_CLIENT.submit_task(
        AworldTask(
            task_id=task_id,
            agent_id="playwright_agent",
            agent_input=web_question_id,
            session_id="session_id",
            user_id="SYSTEM"
        )
    )

    # Get and print task result
    task_result = await AWORLD_TASK_CLIENT.get_task_state(task_id=task_id)
    print(task_result)


async def _batch_run_web_task(start_i: int, end_i: int) -> None:
    """Run multiple Web tasks in parallel.

    Args:
        start_i: Starting question ID
        end_i: Ending question ID
    """
    tasks = [
        _run_web_task(str(i))
        for i in range(start_i, end_i + 1)
    ]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    # Run batch processing for questions 1-5
    asyncio.run(_batch_run_web_task(25, 25))