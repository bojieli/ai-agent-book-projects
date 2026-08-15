from typing import Tuple

from aworld.runners.callback.decorator import CallbackRegistry
from aworld.runners.handler.base import DefaultHandler
from aworld.core.common import Observation, CallbackItem
from aworld.core.event.base import Message, Constants
from aworld.logs.util import logger
from aworld.runners.state_manager import RuntimeStateManager, HandleResult, RunNodeStatus


class ToolCallbackHandler(DefaultHandler):
    def __init__(self, runner):
        self.runner = runner

    async def handle(self, message):
        if message.category != Constants.TOOL_CALLBACK:
            return
        logger.info(f"-------ToolCallbackHandler start handle message----: {message}")
        self.context = message.context
        observation = None
        state_mng = RuntimeStateManager.instance()
        if not state_mng:
            logger.eror("-------ToolCallbackHandler state_mng is None----")
            return
        try:
            payload = message.payload
            if not payload:
                state_mng.run_failed(message.id, "callback failed", [])
                return
            if isinstance(payload, CallbackItem):
                observation = payload.data[0] if isinstance(payload.data, Tuple) else payload.data
            elif isinstance(payload, Tuple) and isinstance(payload[0], Observation):
                observation=payload[0]
            if not isinstance(observation, Observation):
                state_mng.run_failed(message.id, "callback failed", [])
                return
            if not observation.action_result:
                state_mng.run_failed(message.id, "callback failed", [])
                return

            results = []
            for res in observation.action_result:
                success = False
                result = HandleResult(
                    result=Message(payload=None,
                                   category=Constants.TOOL_CALLBACK,
                                   sender=self.name(),
                                   session_id=message.context.session_id,
                                   headers={"context": message.context}),
                    status=RunNodeStatus.FAILED
                )
                if not res or not res.content or not res.tool_name or not res.action_name:
                    results.append(result)
                    continue
                callback_func = CallbackRegistry.get(res.tool_name + "__" + res.action_name)
                if not callback_func:
                    result.status = RunNodeStatus.SUCCESS
                    results.append(result)
                    continue
                callback_res = callback_func(res)
                if not callback_res or callback_res.success is False:
                    results.append(result)
                    continue
                result.status = RunNodeStatus.SUCCESS
                result.result.payload = callback_res
                results.append(result)

            state_mng.run_succeed(message.id, "test callback succ", results)
        except Exception as e:
            # todo
            logger.warning(f"ToolCallbackHandler Failed to parse payload: {e}")
            state_mng.run_failed(message.id, "callback failed", [])
        finally:
            yield Message(
                category=Constants.OUTPUT,
                payload=None,
                sender=self.name(),
                session_id=message.session_id,
                headers={"context": self.context}
            )

        return


