import asyncio

from dotenv import load_dotenv

from tests.memory.agent.self_evolving_agent import SuperAgent


async def _run_single_task_examples() -> None:
    """
    Run examples with a single task.
    Demonstrates basic agent interaction with outdoor sports topic.
    """
    super_agent = SuperAgent(id="super_agent", name="super_agent")
    user_id = "zues"
    session_id = "session#foo"
    await super_agent.async_run(user_id=user_id, session_id=session_id,
                                task_id="zues:session#foo:task#1",
                                user_input="please recommend some outdoor sports, save it use markdown")

# if __name__ == '__main__':
#     load_dotenv()
#     asyncio.run(_run_single_task_examples())