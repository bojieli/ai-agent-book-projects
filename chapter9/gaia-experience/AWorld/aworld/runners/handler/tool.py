# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import abc
from typing import AsyncGenerator

from aworld.config import ConfigDict
from aworld.core.agent.base import is_agent
from aworld.core.common import ActionModel, TaskItem
from aworld.core.event.base import Message, Constants, TopicType
from aworld.core.tool.base import AsyncTool, Tool, ToolFactory
from aworld.logs.util import logger
from aworld.runners import HandlerFactory
from aworld.runners.handler.base import DefaultHandler


class ToolHandler(DefaultHandler):
    __metaclass__ = abc.ABCMeta

    def __init__(self, runner: 'TaskEventRunner'):
        super().__init__(runner)
        self.tools = runner.tools
        self.tools_conf = runner.tools_conf

    @classmethod
    def name(cls):
        return "_tool_handler"


@HandlerFactory.register(name=f'__{Constants.TOOL}__')
class DefaultToolHandler(ToolHandler):
    def is_valid_message(self, message: Message):
        if message.category != Constants.TOOL:
            return False
        return True

    async def _do_handle(self, message: Message) -> AsyncGenerator[Message, None]:
        if not self.is_valid_message(message):
            return

        headers = {"context": message.context}
        # data is List[ActionModel]
        data = message.payload
        if not data:
            # error message, p2p
            yield Message(
                category=Constants.TASK,
                payload=TaskItem(msg="no data to process.", data=data, stop=True),
                sender='agent_handler',
                session_id=message.session_id,
                topic=TopicType.ERROR,
                headers=headers
            )
            return

        for action in data:
            if not isinstance(action, ActionModel):
                # error message, p2p
                yield Message(
                    category=Constants.TASK,
                    payload=TaskItem(msg="action not a ActionModel.", data=data, stop=True),
                    sender=self.name(),
                    session_id=message.session_id,
                    topic=TopicType.ERROR,
                    headers=headers
                )
                return

        new_tools = dict()
        tool_mapping = dict()
        # Directly use or use tools after creation.
        for act in data:
            if is_agent(act):
                logger.warning(f"somethings wrong, {act} is an agent.")
                continue

            if not self.tools or (self.tools and act.tool_name not in self.tools):
                # dynamic only use default config in module.
                conf = self.tools_conf.get(act.tool_name)
                if isinstance(conf, dict):
                    conf = ConfigDict(conf)
                tool = ToolFactory(act.tool_name, conf=conf, asyn=conf.use_async if conf else False)
                tool.event_driven = True
                if isinstance(tool, Tool):
                    tool.reset()
                elif isinstance(tool, AsyncTool):
                    await tool.reset()
                tool_mapping[act.tool_name] = []
                self.tools[act.tool_name] = tool
                new_tools[act.tool_name] = tool
            if act.tool_name not in tool_mapping:
                tool_mapping[act.tool_name] = []
            tool_mapping[act.tool_name].append(act)

        if new_tools:
            yield Message(
                category=Constants.TASK,
                payload=TaskItem(data=new_tools),
                sender=self.name(),
                session_id=message.session_id,
                topic=TopicType.SUBSCRIBE_TOOL,
                headers=headers
            )

        for tool_name, actions in tool_mapping.items():
            if not (isinstance(self.tools[tool_name], Tool) or isinstance(self.tools[tool_name], AsyncTool)):
                logger.warning(f"Unsupported tool type: {self.tools[tool_name]}")
                continue

            # send to the tool
            yield Message(
                category=Constants.TOOL,
                payload=actions,
                sender=actions[0].agent_name if actions else '',
                session_id=message.session_id,
                receiver=tool_name,
                headers=message.headers
            )

    async def post_handle(self, input:Message, output: Message) -> Message:
        new_context = output.context.deep_copy()
        new_context._task = output.context.get_task()
        output.context = new_context
        return output
