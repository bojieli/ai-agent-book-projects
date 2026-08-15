import logging
import os
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
    workspace: str | None = Field(
        default=None,
        description="The workspace of the action."
        " If not specified or invalid, the workspace will be read from the environment variable AWORLD_WORKSPACE.",
    )
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

        self.workspace: Path = self._obtain_valid_workspace(arguments.workspace)

        self.logger: logging.Logger = setup_logger(self.__class__.__name__, self.workspace)

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

    def _obtain_valid_workspace(self, workspace: str | None = None) -> Path:
        r"""
        Obtain a valid workspace path.
        Priority:
          1. user defined workspace
          2. environment variable AWORLD_WORKSPACE
          3. home directory
        """
        path = Path(workspace) if workspace else os.getenv("AWORLD_WORKSPACE", "~")
        if path and path.expanduser().is_dir():
            return path.expanduser().resolve()

        # self._color_log("Invalid workspace path, using home directory instead.", Color.yellow)
        return Path.home().expanduser().resolve()

    def _validate_file_path(self, file_path: str) -> Path:
        """Validate and resolve file path. Rely on the predefined supported_extensions class variable.

        Args:
            file_path: Path to the document or media file

        Returns:
            Resolved Path object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file type is not supported
        """
        path = Path(file_path).expanduser()
        if not path.is_absolute():
            path = self.workspace / path

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if path.suffix.lower() not in self.supported_extensions:
            raise ValueError(
                f"Unsupported file type: {path.suffix}. Supported types: {', '.join(self.supported_extensions)}"
            )

        return path
