# Initialize AworldTaskClient with server endpoints
import asyncio
import logging
from datetime import datetime
import os
import random
import uuid

from aworld.utils.common import get_local_ip

from client.aworld_client import AworldTask, AworldTaskClient

AWORLD_TASK_CLIENT = AworldTaskClient(
    know_hosts = ["localhost:9999"]
)


async def _run_gaia_task(gaia_task: AworldTask, delay: int, background: bool = False) -> None:
    """Run a single Gaia task with the given question ID.

    Args:
        gaia_task_id: The ID of the question to process
    """
    global AWORLD_TASK_CLIENT
    await asyncio.sleep(delay)

    # Submit task to Aworld server
    await AWORLD_TASK_CLIENT.submit_task(gaia_task, background=background)

    # Get and print task result
    task_result = await AWORLD_TASK_CLIENT.get_task_state(task_id=gaia_task.task_id)
    if not background:
        logging.info(f"execute task_result#{gaia_task.task_id} is {task_result.data if task_result else None}")
    else:
        logging.info(f"submit task_result#{gaia_task.task_id} background success, please use task_id get task_result await a moment")



async def _batch_run_gaia_task(gaia_tasks: list[AworldTask]) -> None:
    """Run multiple Gaia tasks in parallel.

    """
    tasks = [
        _run_gaia_task(gaia_task, index * 3, background=True)
        for index, gaia_task in enumerate(gaia_tasks)
    ]
    await asyncio.gather(*tasks)


CUSTOM_SYSTEM_PROMPT = f""" **PLEASE CUSTOM IT **"""

if __name__ == '__main__':
    gaia_task_ids = ['c61d22de-5f6c-4958-a7f6-5e9707bd3466']
    gaia_tasks = []
    custom_mcp_servers = [
            # "e2b-server",
            "e2b-code-server",
            "terminal-controller",
            "excel",
            # "filesystem",
            "calculator",
            "ms-playwright",
            "audio_server",
            "image_server",
            "google-search",
            # "video_server",
            # "search_server",
            # "download_server",
            # "document_server",
            # "youtube_server",
            # "reasoning_server",
        ]

    for gaia_task_id in gaia_task_ids:
        task_id = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + gaia_task_id + "_" + str(uuid.uuid4())
        gaia_tasks.append(
            AworldTask(
                task_id=task_id,
                agent_id="gaia_agent",
                agent_input=gaia_task_id,
                session_id="session_id",
                user_id=os.getenv("USER", "SYSTEM"),
                client_id=get_local_ip(),
                mcp_servers=custom_mcp_servers,
                max_retries=5,
                llm_custom_input="你好"
                # llm_model_name="gpt-4o",
                # task_system_prompt=CUSTOM_SYSTEM_PROMPT
            )
        )
    asyncio.run(_batch_run_gaia_task(gaia_tasks))
