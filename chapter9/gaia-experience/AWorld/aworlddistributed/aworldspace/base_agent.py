import json
import logging
import os
import traceback
import uuid
from abc import abstractmethod
from typing import List, AsyncGenerator, Any

from aworld.config import AgentConfig, TaskConfig, ContextRuleConfig, OptimizationConfig
from aworld.agents.llm_agent import Agent
from aworld.core.task import Task
from aworld.output import WorkSpace, AworldUI, Outputs
from aworld.output.ui.markdown_aworld_ui import MarkdownAworldUI
from aworld.output.utils import load_workspace
from aworld.runner import Runners

from client.aworld_client import AworldTask


class AworldBaseAgent:

    def pipes(self) -> list[dict]:
        return [{"id": self.agent_name(), "name": self.agent_name()}]


    @abstractmethod
    def agent_name(self) -> str:
        pass


    async def pipe(
            self,
            user_message: str,
            model_id: str,
            messages: List[dict],
            body: dict
    ):

        try:
            logging.info(f"🤖{self.agent_name()} received user_message is {user_message}, form-data = {body}")

            task = await self.get_task_from_body(body)

            if task:
                logging.info(f"🤖{self.agent_name()} received task is {task.task_id}_{task.client_id}_{task.user_id}")
                task_id = task.task_id
            else:
                task_id = str(uuid.uuid4())

            session_id = task_id
            if body.get('metadata'):
                # user_id = body.get('metadata').get('user_id')
                session_id = body.get('metadata').get('chat_id', task_id)
                task_id = body.get('metadata').get('message_id', task_id)

            user_input = await self.get_custom_input(user_message, model_id, messages, body)
            if task and task.llm_custom_input:
                user_input = task.llm_custom_input
            logging.info(f"🤖{self.agent_name()} call llm input is [{user_input}]")

            # build agent task read from config
            swarm = await self.build_swarm(body=body)
            agent = None
            if not swarm:
                # build single agent task read from config
                agent = await self.build_agent(body=body)
                logging.info(f"🤖{self.agent_name()} build agent finished")



            # return task
            task = await self.build_task(agent=agent, task_id=task_id, user_input=user_input, user_message=user_message, body=body)
            logging.info(f"🤖{self.agent_name()} build task finished, task_id is {task_id}")


            workspace_type = os.environ.get("WORKSPACE_TYPE", "local")
            workspace_path = os.environ.get("WORKSPACE_PATH", "./data/workspaces")
            workspace = await load_workspace(session_id, workspace_type, workspace_path)
            # render output
            async_generator = await self.parse_task_output(session_id, task, workspace)

            return async_generator()

        except Exception as e:
            return await self._format_exception(e)

    async def _format_exception(self, e: Exception) -> str:
        traceback.print_exc()
        # tb_lines = traceback.format_exception(type(e), e, e.__traceback__)
        # detailed_error = "".join(tb_lines)
        # logging.error(e)
        # return json.dumps({"error": detailed_error}, ensure_ascii=False)
        return "💥💥💥process failed💥💥💥"


    async def _format_error(self, status_code: int, error: bytes) -> str:
        if isinstance(error, str):
            error_str = error
        else:
            error_str = error.decode(errors="ignore")
        try:
            err_msg = json.loads(error_str).get("message", error_str)[:200]
        except Exception:
            err_msg = error_str[:200]
        return json.dumps(
            {"error": f"HTTP {status_code}: {err_msg}"}, ensure_ascii=False
        )

    async def get_custom_input(self, user_message: str,
            model_id: str,
            messages: List[dict],
            body: dict) -> Any:
        user_input = body["messages"][-1]["content"]
        return user_input

    @abstractmethod
    async def get_history_messages(self, body) -> int:
        task = await self.get_task_from_body(body)
        if task:
            return task.history_messages
        return 100

    @abstractmethod
    async def get_agent_config(self, body) -> AgentConfig:
        pass

    @abstractmethod
    async def get_mcp_servers(self, body) -> list[str]:
        pass

    async def build_agent(self, body: dict):

        agent_config =await self.get_agent_config(body)
        mcp_servers = await self.get_mcp_servers(body)
        agent = Agent(
            conf=agent_config,
            name=agent_config.name,
            system_prompt=agent_config.system_prompt,
            mcp_servers=mcp_servers,
            mcp_config=await self.load_mcp_config(),
            history_messages=await self.get_history_messages(body),
            context_rule=ContextRuleConfig(
                optimization_config=OptimizationConfig(
                    enabled=False,
                )
            )
        )
        return agent

    async def build_task(self, agent, task_id, user_input, user_message, body):
        aworld_task = await self.get_task_from_body(body)
        task = Task(
            id=task_id,
            name=task_id,
            input=user_input,
            agent=agent,
            conf=TaskConfig(
                task_id=task_id,
                stream=False,
                ext={
                    "origin_message": user_message
                },
                max_steps=aworld_task.max_steps if aworld_task else 100
            )
        )
        return task



    async def parse_task_output(self, chat_id, task: Task, workspace: WorkSpace):
        _SENTINEL = object()

        async def async_generator():

            from asyncio import Queue
            queue = Queue()

            async def consume_all():
                openwebui_ui = MarkdownAworldUI(
                    session_id=chat_id,
                    workspace=workspace
                )

                # get outputs
                outputs = Runners.streamed_run_task(task)

                # output hooks
                await self.custom_output_before_task(outputs, chat_id, task)

                # render output
                try:
                    async for output in outputs.stream_events():
                        res = await AworldUI.parse_output(output, openwebui_ui)
                        if res:
                            if isinstance(res, AsyncGenerator):
                                async for item in res:
                                    await queue.put(item)
                            else:
                                await queue.put(res)
                    custom_output = await self.custom_output_after_task(outputs, chat_id, task)
                    if custom_output:
                        await queue.put(custom_output)
                    await queue.put(task)
                finally:
                    await queue.put(_SENTINEL)

            # Start the consumer in the background
            import asyncio
            consumer_task = asyncio.create_task(consume_all())

            while True:
                item = await queue.get()
                if item is _SENTINEL:
                    break
                yield item
            await consumer_task
            logging.info(f"🤖{self.agent_name()} task#{task.id} output finished🔚🔚🔚")

        return async_generator

    async def custom_output_before_task(self, outputs: Outputs, chat_id: str, task: Task) -> str | None:
        return None

    async def custom_output_after_task(self, outputs: Outputs, chat_id: str, task: Task):
        pass

    async def get_task_from_body(self, body: dict) -> AworldTask | None:
        try:
            if not body.get("user") or not body.get("user").get("aworld_task"):
                return None
            return AworldTask.model_validate_json(body.get("user").get("aworld_task"))
        except Exception as err:
            logging.error(f"Error parsing AworldTask: {err}; data: {body.get('user_message')}")
            traceback.print_exc()
            return None

    @abstractmethod
    async def load_mcp_config(self) -> dict:
        pass

    async def build_swarm(self, body):
        return None
