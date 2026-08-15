import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, AsyncGenerator

from aworld.logs.util import logger
from aworld.output.ui.markdown_aworld_ui import MarkdownAworldUI

from aworld.agents.llm_agent import Agent
from aworld.config import AgentConfig, TaskConfig
from aworld.core.common import ActionModel, Observation
from aworld.core.context.base import Context
from aworld.core.event.base import Message
from aworld.core.memory import LongTermConfig, MemoryItem, AgentMemoryConfig
from aworld.core.task import Task
from aworld.memory.main import MemoryFactory
from aworld.memory.models import LongTermMemoryTriggerParams, MemoryAIMessage, MessageMetadata, UserProfile, \
    MemoryHumanMessage
from aworld.memory.utils import build_history_context
from aworld.output import AworldUI
from aworld.output.utils import load_workspace
from aworld.prompt import Prompt
from aworld.runner import Runners
from aworld.utils.common import load_mcp_config
from tests.memory.prompts import SELF_EVOLVING_USER_INPUT_REWRITE_PROMPT, RESEARCH_PROMPT


class SuperAgent:
    """
    Super agent
    """

    def __init__(self, id: str, name: str, **kwargs):
        self.memory_config = AgentMemoryConfig(
            enable_long_term=True,
            long_term_config=LongTermConfig.create_simple_config(
                enable_user_profiles=True
            )
        )
        self.memory = MemoryFactory.instance()

        agent_config = AgentConfig(
            llm_provider="openai",
            llm_model_name=os.environ["LLM_MODEL_NAME"],
            llm_api_key=os.environ["LLM_API_KEY"],
            llm_base_url=os.environ["LLM_BASE_URL"]
        )
        self.sub_agent = SelfEvolvingAgent(
            conf=agent_config,
            agent_id="self_evolving_agent",
            name="self_evolving_agent",
            system_prompt=RESEARCH_PROMPT,
            mcp_servers=["ms-playwright","google-search","tavily-mcp", "filesystem"],
            history_messages=100,
            mcp_config=load_mcp_config(),
            agent_memory_config=AgentMemoryConfig(
                enable_summary=True,
                summary_rounds=10,
                summary_model=os.environ["LLM_MODEL_NAME"],
                enable_long_term=True,
                long_term_config=LongTermConfig.create_simple_config(
                    enable_agent_experiences=True
                )
            )
        )
        self.id = id
        self.name = name

    async def async_run(self, user_id, session_id, task_id, user_input):
        """
        Run task
        """
        task_context = await self.get_history_context(user_id, session_id, task_id, user_input)

        await self.add_human_input(user_id, session_id, task_id, user_input)

        result = await self.run_task(user_id, session_id, task_id, user_input, task_context)

        await self.add_ai_message(user_id, session_id, task_id, result)

        await self.post_run(user_id, session_id, task_id, task_context)

    async def run_task(self, user_id, session_id, task_id, user_input, task_context):
        user_input = await self.rewrite_user_input(user_id, user_input, task_context)
        task = Task(
            id=task_id,
            session_id=session_id,
            user_id=user_id,
            input=user_input,
            agent=self.sub_agent,
            conf=TaskConfig(),
            context=task_context
        )
        logging.info(f"[SuperAgent] run task start, task_id = {task.id} input = {input}")
        result = ""

        session_workspace = await load_workspace(workspace_id=task.session_id, workspace_type="local",
                                                 workspace_parent_path="data/workspaces")
        local_ui = MarkdownAworldUI(
            session_id=task.session_id,
            task_id=task.id,
            workspace=session_workspace
        )

        # get outputs
        outputs = Runners.streamed_run_task(task)

        with open(f"output_{task.session_id}.md", "a") as f:
            # render output
            try:
                f.write(f"User: {user_input}")
                async for output in outputs.stream_events():
                    res = await AworldUI.parse_output(output, local_ui)
                    if res:
                        if isinstance(res, AsyncGenerator):
                            async for item in res:
                                result += item
                                f.write(item)
                        else:
                            result += res
                            f.write(res)
            except Exception as e:
                logger.error(f"Error: {e}")
            finally:
                f.close()
        logging.info(f"[SuperAgent] run task finished, task_id = {task.id} result = {result}")
        return result

    async def rewrite_user_input(self, user_id, user_input, task_context):
        """
        Rewrite user input
        """
        user_profiles = await self.retrival_user_profile(user_id, user_input)
        logging.info(f"[SuperAgent] rewrite_user_input user_profiles = {user_profiles}")
        similar_messages_history = await self.retrival_similar_messages_history(user_id, user_input)
        logging.info(f"[SuperAgent] rewrite_user_input similar_messages_history = {similar_messages_history}")
        return SELF_EVOLVING_USER_INPUT_REWRITE_PROMPT.format(user_input=user_input, user_profiles=user_profiles,
                                                              similar_messages_history=similar_messages_history)

    async def get_history_context(self, user_id, session_id, task_id, user_input):
        # get cur session history
        history_messages = self.memory.get_last_n(10, filters={
            "user_id": user_id,
            "session_id": session_id,
            "agent_id": self.id
        })
        task_context = Context()
        task_context.context_info["history"] = build_history_context(history_messages)

        # get cur user profile
        user_profiles = await self.retrival_user_profile(user_id, user_input)
        task_context.context_info["user_profiles"] = user_profiles

        # get similar messages_history
        similar_messages_history = await self.retrival_similar_messages_history(user_id, user_input)
        task_context.context_info["similar_messages_history"] = similar_messages_history

        return task_context

    async def post_run(self, user_id, session_id, task_id, task_context):
        """
        Post run
        """
        logging.info(f"[SuperAgent] post_run user_id = {user_id}, session_id = {session_id}, task_id = {task_id}")
        await self.extract_user_profile(user_id, session_id, task_id)
        await self.sub_agent.evolving(user_id, session_id, task_id)

    async def add_ai_message(self, user_id, session_id, task_id, result):
        await self.memory.add(MemoryAIMessage(
            content=result,
            metadata=MessageMetadata(
                user_id=user_id,
                session_id=session_id,
                task_id=task_id,
                agent_id=self.id,
                agent_name=self.name
            )
        ), agent_memory_config=self.memory_config)

    async def add_human_input(self, user_id, session_id, task_id, user_input):
        await self.memory.add(MemoryHumanMessage(
            content=user_input,
            metadata=MessageMetadata(
                user_id=user_id,
                session_id=session_id,
                task_id=task_id,
                agent_id=self.id,
                agent_name=self.name
            )
        ), agent_memory_config=self.memory_config)

    async def extract_user_profile(self, user_id, session_id, task_id):
        await self.memory.trigger_short_term_memory_to_long_term(LongTermMemoryTriggerParams(
            agent_id=self.id,
            session_id=session_id,
            task_id=task_id,
            user_id=user_id,
            force=True
        ), self.memory_config)

    async def gen_long_term_memory(self, user_id, session_id, task_id):
        """
        Gen long-term memory
        """
        await self.memory.trigger_short_term_memory_to_long_term(LongTermMemoryTriggerParams(
            agent_id=self.id,
            session_id=session_id,
            task_id=task_id,
            user_id=user_id
        ), self.memory_config)

    async def retrival_user_profile(self, user_id, user_input) -> Optional[list[UserProfile]]:
        """
        Retrieve similar user profiles from long-term storage for context.
        """
        return await self.memory.retrival_user_profile(user_id, user_input)

    async def retrival_similar_messages_history(self, user_id, user_input) -> Optional[List[MemoryItem]]:
        """
        Retrieve similar messages history from long-term storage for context.
        """
        return await self.memory.retrival_similar_user_messages_history(user_id, user_input)

class SelfEvolvingAgent(Agent):
    """
    Self-evolving agent
    """

    async def async_policy(self, observation: Observation, info: Dict[str, Any] = {}, message: Message = None,
                           **kwargs) -> List[ActionModel]:
        return await super().async_policy(observation, info, message, **kwargs)


    async def evolving(self, user_id, session_id, task_id):
        """
        Evolving agent experience
        """
        logging.info(
            f"[SelfEvolvingAgent] evolving_agent_experience user_id = {user_id}, session_id = {session_id}, task_id = {task_id}")
        await self.memory.trigger_short_term_memory_to_long_term(LongTermMemoryTriggerParams(
            agent_id=self.id(),
            session_id=session_id,
            task_id=task_id,
            user_id=user_id,
            force=True
        ), self.memory_config)

    async def custom_system_prompt(self, context: Context, content: str):
        """
        custom it
        """
        agent_experiences = await self.memory.retrival_agent_experience(self.id(), context.get_task().input)
        logging.info(f"[SelfEvolvingAgent] custom_system_prompt agent_experiences = {agent_experiences}")

        return Prompt(self.system_prompt).get_prompt(variables={
            "history": context.context_info.get("history", ""),
            "agent_experiences": agent_experiences,
            "cur_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
