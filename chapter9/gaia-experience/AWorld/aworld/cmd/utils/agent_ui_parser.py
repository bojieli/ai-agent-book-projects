import json
from dataclasses import dataclass
import uuid

from pydantic import Field, BaseModel, ConfigDict

from aworld.output import (
    MessageOutput,
    AworldUI,
    Output,
    WorkSpace,
)
from aworld.output.artifact import Artifact, ArtifactType
from aworld.output.base import StepOutput, ToolResultOutput
from aworld.output.utils import consume_content
from abc import ABC, abstractmethod
from typing_extensions import override


class ToolCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_type: str = Field(None, description="tool type")
    tool_name: str = Field(None, description="tool name")
    function_name: str = Field(None, description="function name")
    tool_call_id: str = Field(None, description="tool call id")
    arguments: str = Field(None, description="arguments")
    results: str = Field(None, description="results")
    card_type: str = Field(None, description="card type")
    card_data: dict = Field(None, description="card data")
    artifacts: list = Field(default_factory=list, description="artifacts")

    @staticmethod
    def from_tool_result(output: ToolResultOutput) -> "ToolCard":
        return ToolCard(
            tool_type=output.tool_type,
            tool_name=output.tool_name,
            function_name=output.origin_tool_call.function.name,
            tool_call_id=output.origin_tool_call.id,
            arguments=output.origin_tool_call.function.arguments,
            results=output.data,
            artifacts=[],
        )


class BaseToolResultParser(ABC):

    def __init__(self, tool_name: str = None):
        self.tool_name = tool_name or self.__class__.__name__

    @abstractmethod
    async def parse(self, output: ToolResultOutput, workspace: WorkSpace):
        pass


class DefaultToolResultParser(BaseToolResultParser):

    @override
    async def parse(self, output: ToolResultOutput, workspace: WorkSpace):
        tool_card = ToolCard.from_tool_result(output)

        tool_card.card_type = "tool_call_card_default"

        # screenshots
        if (
            output.metadata.get("screenshots")
            and isinstance(output.metadata.get("screenshots"), list)
            and len(output.metadata.get("screenshots")) > 0
        ):
            for _, screenshot in enumerate(output.metadata.get("screenshots")):
                image_artifact = Artifact(
                    artifact_id=str(uuid.uuid4()),
                    artifact_type=ArtifactType.IMAGE,
                    content=screenshot.get("ossPath"),
                )
                await workspace.add_artifact(image_artifact)
                tool_card.artifacts.append(
                    {
                        "artifact_type": image_artifact.artifact_type.value,
                        "artifact_id": image_artifact.artifact_id,
                    }
                )

        return f"""\
\n\n**🔧 Tool: {tool_card.tool_name}#{tool_card.function_name}**\n\n
```tool_card
{json.dumps(tool_card.model_dump(), ensure_ascii=False, indent=2)}
```\n
"""


class SearchToolResultParser(BaseToolResultParser):

    @override
    async def parse(self, output: ToolResultOutput, workspace: WorkSpace):
        tool_card = ToolCard.from_tool_result(output)

        query = ""
        try:
            args = json.loads(tool_card.arguments)
            query = args.get("query")
            # aworld search server
            if not query:
                query = args.get("query_list")
        except Exception:
            pass

        result_items = []
        try:
            result_items = json.loads(tool_card.results)
            # aworld search server return url, not link
            if result_items and isinstance(result_items, list):
                for item in result_items:
                    if not item.get("link", None) and item.get("url", None):
                        item["link"] = item.get("url")
        except Exception:
            pass

        if len(result_items) > 0:
            tool_card.results = ""

        tool_card.card_type = "tool_call_card_link_list"
        tool_card.card_data = {
            "title": "🔎 Google Search",
            "query": query,
            "search_items": result_items,
        }

        artifact_id = str(uuid.uuid4())
        await workspace.create_artifact(
            artifact_type=ArtifactType.WEB_PAGES,
            artifact_id=artifact_id,
            content=result_items,
            metadata={
                "query": query,
            },
        )
        tool_card.artifacts.append(
            {
                "artifact_type": ArtifactType.WEB_PAGES.value,
                "artifact_id": artifact_id,
            }
        )

        return f"""\
\n\n**🔎 Search Results**\n\n
```tool_card
{json.dumps(tool_card.model_dump(), ensure_ascii=False, indent=2)}
```\n
"""


class ToolResultParserFactory:
    def get_parser(self, tool_type: str, tool_name: str):
        if "search" in tool_name and ("search" in tool_name or tool_name == None):
            return SearchToolResultParser()
        else:
            return DefaultToolResultParser()


@dataclass
class AWorldWebAgentUI(AworldUI):
    session_id: str = Field(default="", description="session id")
    workspace: WorkSpace = Field(default=None, description="workspace")
    tool_result_parser_factory: ToolResultParserFactory = Field(
        default=ToolResultParserFactory, description="tool result parser factory"
    )

    def __init__(
        self,
        session_id: str = None,
        workspace: WorkSpace = None,
        tool_result_parser_factory: ToolResultParserFactory = None,
        **kwargs,
    ):
        """
        Initialize MarkdownAworldUI
        Args:"""
        super().__init__(**kwargs)
        self.session_id = session_id
        self.workspace = workspace
        self.tool_result_parser_factory = (
            tool_result_parser_factory or ToolResultParserFactory()
        )

    @override
    async def message_output(self, __output__: MessageOutput):
        """
        Returns an async generator that yields each message item.
        """
        # Sentinel object for queue completion
        _SENTINEL = object()

        async def async_generator():
            async def __log_item(item):
                await queue.put(item)

            from asyncio import Queue

            queue = Queue()

            async def consume_all():
                # Consume all relevant generators
                if __output__.reason_generator or __output__.response_generator:
                    if __output__.reason_generator:
                        await consume_content(__output__.reason_generator, __log_item)
                    if __output__.response_generator:
                        await consume_content(__output__.response_generator, __log_item)
                else:
                    await consume_content(__output__.reasoning, __log_item)
                    await consume_content(__output__.response, __log_item)
                # Only after all are done, put the sentinel
                await queue.put(_SENTINEL)

            # Start the consumer in the background
            import asyncio

            consumer_task = asyncio.create_task(consume_all())

            while True:
                item = await queue.get()
                if item is _SENTINEL:
                    break
                yield item
            await consumer_task  # Ensure background task is finished

        return async_generator()

    @override
    async def tool_result(self, output: ToolResultOutput):
        """
        tool_result
        """
        parser = self.tool_result_parser_factory.get_parser(
            output.tool_type, output.tool_name
        )
        return await parser.parse(output, workspace=self.workspace)

    @override
    async def step(self, output: StepOutput):
        emptyLine = "\n\n"
        if output.status == "START":
            return f"\n\n # {output.show_name} \n\n"
        elif output.status == "FINISHED":
            return f"{emptyLine}"
        elif output.status == "FAILED":
            return f"\n\n{output.name} 💥FAILED: reason is {output.data} {emptyLine}"
        else:
            return f"\n\n{output.name} ❓❓❓UNKNOWN#{output.status} {emptyLine}"

    @override
    async def custom_output(self, output: Output):
        return output.data
