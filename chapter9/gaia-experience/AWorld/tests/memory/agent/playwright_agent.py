import logging
from typing import Any, Dict, List

from aworld.agents.llm_agent import Agent
from aworld.core.common import Observation, ActionModel, ActionResult
from aworld.core.context.base import Context
from aworld.core.event.base import Message


class PlaywrightAgent(Agent):


    def __int__(self, **kwargs):
        super().__init__(name="playwright_agent", **kwargs)

    async def async_policy(self, observation: Observation, info: Dict[str, Any] = {}, message: Message = None,
                           **kwargs) -> List[ActionModel]:
        return await super().async_policy(observation, info, message, **kwargs)

    async def _add_tool_result_to_memory(self, tool_call_id: str, tool_result: ActionResult, context: Context):
        """Add tool result to memory"""
        logging.info(f"tool_result: {tool_result}")
        if isinstance(tool_result.content, str) and tool_result.content.startswith("data:image"):
            image_content = tool_result.content
            tool_result.content = "this picture is below "
            await super()._add_tool_result_to_memory(tool_call_id, tool_result, context)
            image_content = [
                {
                    "type": "text",
                    "text": f"this is file of tool_call_id:{tool_result.tool_call_id}"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_content
                    }
                }
            ]
            await super()._add_human_input_to_memory(image_content, context)
        else:
            await super()._add_tool_result_to_memory(tool_call_id, tool_result, context)

