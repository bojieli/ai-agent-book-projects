# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import abc
from typing import AsyncGenerator

from aworld.core.agent.base import AgentFactory
from aworld.core.event.base import Message, Constants
from aworld.runners import HandlerFactory
from aworld.runners.handler import DefaultHandler
from aworld.runners.state_manager import RuntimeStateManager, HandleResult, RunNodeStatus


@HandlerFactory.register(name=f'__{Constants.HUMAN}__')
class DefaultHumanHandler(DefaultHandler):
    __metaclass__ = abc.ABCMeta

    def __init__(self, runner: 'TaskEventRunner'):
        super().__init__(runner)
        self.runner = runner
        self.swarm = runner.swarm
        self.endless_threshold = runner.endless_threshold
        self.task_id = runner.task.id

        self.agent_calls = []

    def is_valid_message(self, message: Message):
        if message.category != Constants.HUMAN:
            if self.swarm and message.sender in self.swarm.agents and message.sender in AgentFactory:
                if self.agent_calls:
                    if self.agent_calls[-1] != message.sender:
                        self.agent_calls.append(message.sender)
                else:
                    self.agent_calls.append(message.sender)
            return False
        return True

    async def handle_user_input(self, data):
        # rewrite this method to handle user input
        return input(f"Human Confirm Info: {data}\nPlease Input:")

    async def _do_handle(self, message: Message) -> AsyncGenerator[Message, None]:
        if not self.is_valid_message(message):
            return
        headers = {"context": message.context}
        session_id = message.session_id

        human_input = await self.handle_user_input(message)

        yield Message(
            category=Constants.HUMAN_RESPONSE,
            sender=self.name(),
            receiver=message.sender,
            session_id=session_id,
            payload=human_input,
            headers=headers,
        )
        return

    async def post_handle(self, input:Message, output: Message) -> Message:
        if not self.is_valid_message(input):
            return output

        if output.category is not Constants.HUMAN_RESPONSE:
            return output

        # update handle_result to state manager
        results = [HandleResult(
            name = output.category,
            status = RunNodeStatus.SUCCESS,
            result = output
        )]
        state_mng = RuntimeStateManager.instance()
        state_mng.run_succeed(node_id=input.id,
                              result_msg="run DefaultHumanHandler succeed",
                              results=results)
        return output
