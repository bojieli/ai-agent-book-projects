# aworld/runners/handler/output.py
import json
from typing import AsyncGenerator
from aworld.core.task import TaskResponse
from aworld.models.model_response import ModelResponse
from aworld.runners import HandlerFactory
from aworld.runners.handler.base import DefaultHandler
from aworld.output.base import StepOutput, MessageOutput, Output
from aworld.core.common import TaskItem
from aworld.core.event.base import Message, Constants, TopicType
from aworld.logs.util import logger
from aworld.runners.hook.hook_factory import HookFactory
from aworld.runners.hook.hooks import HookPoint


@HandlerFactory.register(name=f'__{Constants.OUTPUT}__')
class DefaultOutputHandler(DefaultHandler):
    def __init__(self, runner):
        super().__init__(runner)
        self.runner = runner
        self.hooks = {}
        if runner.task.hooks:
            for k, vals in runner.task.hooks.items():
                self.hooks[k] = []
                for v in vals:
                    cls = HookFactory.get_class(v)
                    if cls:
                        self.hooks[k].append(cls)

    def is_valid_message(self, message: Message):
        if message.category != Constants.OUTPUT:
            return False
        return True

    async def _do_handle(self, message):
        if not self.is_valid_message(message):
            return
        # 1. get outputs
        outputs = self.runner.task.outputs
        if not outputs:
            yield Message(
                category=Constants.TASK,
                payload=TaskItem(msg="Cannot get outputs.",
                                 data=message, stop=True),
                sender=self.name(),
                session_id=self.runner.context.session_id,
                topic=TopicType.ERROR,
                headers={"context": message.context}
            )
            return

        # 2. Call OUTPUT_PROCESS hooks to process data in the message
        async for event in self.run_hooks(message, HookPoint.OUTPUT_PROCESS):
            # If hook returns a processed message, use the processed message
            if event and isinstance(event, Message) and event.payload:
                message.payload = event.payload

        # 3. build Output
        payload = message.payload
        mark_complete = False
        output = None
        try:
            if isinstance(payload, Output):
                output = payload
                output.task_id = self.runner.task.id
            elif isinstance(payload, TaskResponse):
                logger.info(
                    f"FINISHED|output get task_response with usage: {json.dumps(payload.usage)}")
                if message.topic == TopicType.FINISHED or message.topic == TopicType.ERROR:
                    mark_complete = True
            elif isinstance(payload, ModelResponse) or isinstance(payload, AsyncGenerator):
                output = MessageOutput(source=payload, task_id=self.runner.task.id)
        except Exception as e:
            logger.warning(f"Failed to parse output: {e}")
            yield Message(
                category=Constants.TASK,
                payload=TaskItem(msg="Failed to parse output.",
                                 data=payload, stop=True),
                sender=self.name(),
                session_id=self.runner.context.session_id,
                topic=TopicType.ERROR,
                headers={"context": message.context}
            )
        finally:
            if output:
                if not output.metadata:
                    output.metadata = {}
                output.metadata['sender'] = message.sender
                output.metadata['receiver'] = message.receiver
                await outputs.add_output(output)
            if mark_complete:
                logger.info(f"FINISHED|output mark_completed|{self.runner.task.id}")
                await outputs.mark_completed()

        return
