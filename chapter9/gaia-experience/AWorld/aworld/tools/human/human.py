# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import traceback
from typing import Any, Dict, Tuple

from aworld.config import ToolConfig
from aworld.core.common import Observation, ActionModel, ActionResult
from aworld.core.event.base import Constants, TopicType, HumanMessage, Message
from aworld.core.tool.base import ToolFactory, AsyncTool
from aworld.events.util import send_message
from aworld.logs.util import logger
from aworld.tools.human.actions import HumanExecuteAction
from aworld.tools.utils import build_observation

HUMAN = "human"


@ToolFactory.register(name=HUMAN,
                      desc=HUMAN,
                      supported_action=HumanExecuteAction)
class HumanTool(AsyncTool):
    def __init__(self, conf: ToolConfig, **kwargs) -> None:
        """Init document tool."""
        super(HumanTool, self).__init__(conf, **kwargs)
        self.cur_observation = None
        self.content = None
        self.keyframes = []
        self.init()
        self.step_finished = True

    async def reset(self, *, seed: int | None = None, options: Dict[str, str] | None = None) -> Tuple[
        Observation, dict[str, Any]]:
        await super().reset(seed=seed, options=options)

        await self.close()
        self.step_finished = True
        return build_observation(observer=self.name(),
                                 ability=HumanExecuteAction.HUMAN_CONFIRM.value.name), {}

    def init(self) -> None:
        self.initialized = True

    async def close(self) -> None:
        pass

    async def finished(self) -> bool:
        return self.step_finished

    async def do_step(self, actions: list[ActionModel], **kwargs) -> Tuple[
        Observation, float, bool, bool, Dict[str, Any]]:
        self.step_finished = False
        reward = 0.
        fail_error = ""
        observation = build_observation(observer=self.name(),
                                        ability=HumanExecuteAction.HUMAN_CONFIRM.value.name)
        info = {}
        try:
            if not actions:
                raise ValueError("actions is empty")
            action = actions[0]
            confirm_content = action.params.get("confirm_content", "")
            if not confirm_content:
                raise ValueError("content invalid")
            # send human message to read human input
            message, error = await self.send_human_message(confirm_content=confirm_content)
            if error:
                raise ValueError(f"HumanTool|send human message failed: {error}")

            # hanging on human message
            logger.info(f"HumanTool|waiting for human input")
            result = await self.long_wait_message_state(message=message)
            logger.info(f"HumanTool|human input succeed: {message.payload}")

            observation.content = result
            observation.action_result.append(
                ActionResult(is_done=True,
                             success=False if error else True,
                             content=f"{result}",
                             error=f"{error}",
                             keep=False))
            reward = 1.
        except Exception as e:
            fail_error = str(e)
            logger.warn(f"HumanTool|failed do_step: {traceback.format_exc()}")
        finally:
            self.step_finished = True
        info["exception"] = fail_error
        info.update(kwargs)
        return (observation, reward, kwargs.get("terminated", False),
                kwargs.get("truncated", False), info)

    async def long_wait_message_state(self, message: Message):
        from aworld.runners.state_manager import HandleResult, RunNodeBusiType
        from aworld.runners.state_manager import RuntimeStateManager, RunNodeStatus

        state_mng = RuntimeStateManager.instance()
        msg_id = message.id
        # init node
        state_mng.create_node(
            node_id=msg_id,
            busi_type=RunNodeBusiType.from_message_category(Constants.HUMAN),
            busi_id=message.receiver or "",
            session_id=message.session_id,
            task_id=message.task_id,
            msg_id=msg_id,
            msg_from=message.sender)
        # wait for message node completion
        res_node = await state_mng.wait_for_node_completion(node_id=msg_id)
        if res_node.status == RunNodeStatus.SUCCESS or res_node.results:
            # get result and status from node
            handle_result: HandleResult = res_node.results[0]
            logger.info(f"HumanTool|human input origin result: {res_node.results}")
            return handle_result.result.payload
        else:
            logger.debug(f"HumanTool|tool {self.name()} callback failed with node: {res_node}.")
            raise ValueError(f"HumanTool|send human message failed: {res_node}")

    async def send_human_message(self, confirm_content):
        error = None
        try:
            message = HumanMessage(
                category=Constants.HUMAN,
                payload=confirm_content,
                sender=self.name(),
                session_id=self.context.session_id,
                topic=TopicType.HUMAN_CONFIRM,
                headers={"context": self.context}
            )
            await send_message(message)
            return message, error
        except Exception as e:
            error = str(e)
            logger.warning(f"HumanTool|human_confirm error: {str(e)} {traceback.format_exc()}")
            return None, error
        finally:
            pass
