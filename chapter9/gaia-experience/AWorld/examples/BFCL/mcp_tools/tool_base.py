import logging
from pathlib import Path
from typing import Any, Literal

from mcp.server import FastMCP
from pydantic import BaseModel, Field

from aworld.logs.util import Color
from examples.gaia.utils import color_log, setup_logger


class ActionArguments(BaseModel):
    r"""Protocol: MCP Action Arguments"""

    name: str = Field(description="The name of the action")
    transport: Literal["stdio", "sse"] = Field(default="stdio", description="The transport of the action")
    unittest: bool = Field(default=False, description="Whether to run in unittest mode")


class ActionResponse(BaseModel):
    r"""Protocol: MCP Action Response"""

    success: bool = Field(default=False, description="Whether the action is successfully executed")
    message: Any = Field(default=None, description="The execution result of the action")
    metadata: dict[str, Any] = Field(default={}, description="The metadata of the action")


class ActionCollection:
    r"""Base class for all ActionCollection."""

    server: FastMCP
    logger: logging.Logger

    def __init__(self, arguments: ActionArguments) -> None:
        self.unittest = arguments.unittest
        self.transport = arguments.transport
        self.supported_extensions = set()

        self.logger: logging.Logger = setup_logger(self.__class__.__name__, output_folder_path='./logs')

        self.server = FastMCP(arguments.name)
        for tool_name in self.__class__.__dict__:
            if tool_name.startswith("mcp_") and callable(getattr(self.__class__, tool_name)):
                tool = getattr(self, tool_name)
                self.server.add_tool(tool, description=tool.__doc__)

    def run(self) -> None:
        if not self.unittest:
            self.server.run(transport=self.transport)

    def _color_log(self, value: str, color: Color = None, level: str = "info"):
        return color_log(self.logger, value, color, level=level)