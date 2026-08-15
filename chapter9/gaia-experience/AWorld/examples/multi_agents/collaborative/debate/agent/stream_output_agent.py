from aworld.config import AgentConfig
from aworld.agents.llm_agent import Agent
from aworld.models.llm import acall_llm_model_stream
from aworld.output import MessageOutput


class StreamOutputAgent(Agent):
    def __init__(self, conf: AgentConfig, name: str, **kwargs):
        super().__init__(conf, name)

    async def async_call_llm(self, messages, json_parse=False) -> MessageOutput:
        # Async streaming with acall_llm_model
        async def async_generator():
            async for chunk in acall_llm_model_stream(self.llm, messages, stream=True):
                if chunk.content:
                    yield chunk.content

        return MessageOutput(source=async_generator(), json_parse=json_parse)
