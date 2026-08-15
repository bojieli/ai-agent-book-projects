from pydantic import BaseModel, Field

from aworld.output import Output
import asyncio

from aworld.output.base import OutputPart


class DebateSpeech(Output, BaseModel):
    name: str = Field(default="", description="name of the speaker")
    type: str = Field(default="", description="speech type")
    stance: str = Field(default="", description="stance of the speech")
    content: str = Field(default="", description="content of the speech")
    round: int = Field(default=0, description="round of the speech")
    finished: bool = Field(default=False, description="round of the speech")
    metadata: dict = Field(default_factory=dict, description="metadata of the speech")

    async def wait_until_finished(self):
        """
        Wait until the speech is finished.
        """
        while not self.finished:
            await asyncio.sleep(1)

    async def convert_to_parts(self, message_output, after_call):
        async def __convert_to_parts__():
            async for item in message_output.response_generator:
                if item:
                    self.content += item
                    yield OutputPart(content=item)
            if message_output.finished:
                await after_call(message_output.response)

        self.parts = __convert_to_parts__()

    @classmethod
    def from_dict(cls, data: dict) -> "DebateSpeech":
        return cls(
            name=data.get("name", ""),
            type=data.get("type", ""),
            stance=data.get("stance", ""),
            content=data.get("content", ""),
            round=data.get("round", 0),
            metadata=data.get("metadata", {})
        )
