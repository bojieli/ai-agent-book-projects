import asyncio
import json
import logging
import platform
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Union

import chardet
import pandas as pd
from dotenv import load_dotenv
from pydantic.fields import FieldInfo

from mcp.server import FastMCP
from mcp.types import TextContent
from pydantic import Field, BaseModel

from base import ActionResponse

load_dotenv()
workspace = Path.home()

command_history: list[dict] = []
max_history_size = 50

# Define dangerous commands for safety
dangerous_commands = [
    "rm -rf /",
    "mkfs",
    "dd if=",
    ":(){ :|:& };:",  # Unix
    "del /f /s /q",
    "format",
    "diskpart",  # Windows
    "sudo rm",
    "sudo dd",
    "sudo mkfs",  # Sudo variants
]

# Get current platform info
platform_info = {
    "system": platform.system(),
    "platform": platform.platform(),
    "architecture": platform.architecture()[0],
}


class CommandResult(BaseModel):
    """Individual command execution result with structured data."""

    command: str
    success: bool
    stdout: str
    stderr: str
    return_code: int
    duration: str
    timestamp: str


class TerminalMetadata(BaseModel):
    """Metadata for terminal operation results."""

    command: str
    platform: str
    working_directory: str
    timeout_seconds: int
    execution_time: float | None = None
    return_code: int | None = None
    safety_check_passed: bool = True
    error_type: str | None = None
    history_count: int | None = None


mcp = FastMCP(
    "terminal-server",
    instructions="""
Terminal MCP Server

This module provides MCP server functionality for executing terminal commands safely.
It supports command execution with timeout controls and returns LLM-friendly formatted results.

Key features:
- Execute terminal commands with configurable timeouts
- Cross-platform command execution support
- Command history tracking and retrieval
- Safety checks for dangerous commands
- LLM-optimized output formatting

Main functions:
- mcp_execute_command: Execute terminal commands with safety checks
- mcp_get_command_history: Retrieve recent command execution history
- mcp_get_terminal_capabilities: Get terminal service capabilities
""",
)


@mcp.tool(
    description="""
Execute a terminal command with safety checks and timeout controls.

        This tool provides secure command execution with:
        - Cross-platform compatibility (Windows, macOS, Linux)
        - Configurable timeout controls
        - Safety checks for dangerous commands
        - LLM-optimized result formatting
        - Command history tracking

        Specialized Feature:
        - Execute Python code and output the result to stdout
            - Example (Directly execute simple Python code): `python -c "nums = [1, 2, 3, 4]\nsum_of_nums = sum(nums)\nprint(f'{sum_of_nums=}')"`
            - Example (Execute code from a file): `python my_script.py`
"""
)
async def execute_command(
    command: str = Field(description="Terminal command to execute"),
    timeout: int = Field(
        default=30, description="Command timeout in seconds (default: 30)"
    ),
    output_format: str = Field(
        default="markdown", description="Output format: 'markdown', 'json', or 'text'"
    ),
) -> Union[str, TextContent]:
    if isinstance(command, FieldInfo):
        command = command.default
    if isinstance(timeout, FieldInfo):
        timeout = timeout.default
    if isinstance(output_format, FieldInfo):
        output_format = output_format.default

    try:
        # Safety check
        is_safe, safety_reason = _check_command_safety(command)
        if not is_safe:
            action_response = ActionResponse(
                success=False,
                message=f"Command rejected for security reasons: {safety_reason}",
                metadata=TerminalMetadata(
                    command=command,
                    platform=platform_info["system"],
                    working_directory=str(workspace),
                    timeout_seconds=timeout,
                    safety_check_passed=False,
                    error_type="security_violation",
                ).model_dump(),
            )
            return TextContent(
                type="text",
                text=json.dumps(
                    action_response.model_dump()
                ),  # Empty string instead of None
                **{"metadata": {}},  # Pass as additional fields
            )

        logging.info(f"🔧 Executing command: {command}")

        # Execute command
        start_time = time.time()
        result = await _execute_command_async(command, timeout)
        execution_time = time.time() - start_time

        # Format output
        formatted_output = _format_command_output(result, output_format)

        # Create metadata
        metadata = TerminalMetadata(
            command=command,
            platform=platform_info["system"],
            working_directory=str(workspace),
            timeout_seconds=timeout,
            execution_time=execution_time,
            return_code=result.return_code,
            safety_check_passed=True,
        )

        if result.success:
            logging.info(
                "✅ Command completed successfully",
            )
        else:
            logging.info(f"❌ Command failed with return code {result.return_code}")
            metadata.error_type = "execution_failure"

        action_response = ActionResponse(
            success=result.success,
            message=formatted_output,
            metadata=metadata.model_dump(),
        )
        output_dict = {
            "artifact_type": "MARKDOWN",
            "artifact_data": json.dumps(
                action_response.model_dump()
            )
        }
        return TextContent(
            type="text",
            text=json.dumps(
                action_response.model_dump()
            ),  # Empty string instead of None
            **{"metadata": output_dict},  # Pass as additional fields
        )

    except Exception as e:
        error_msg = f"Failed to execute command: {str(e)}"
        logging.error(f"Command execution error: {traceback.format_exc()}")

        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata=TerminalMetadata(
                command=command,
                platform=platform_info["system"],
                working_directory=str(workspace),
                timeout_seconds=timeout,
                safety_check_passed=True,
                error_type="internal_error",
            ).model_dump(),
        )
        return TextContent(
            type="text",
            text=json.dumps(
                action_response.model_dump()
            ),  # Empty string instead of None
            **{"metadata": {}},  # Pass as additional fields
        )


@mcp.tool(
    description="""
Retrieve recent command execution history.
"""
)
async def get_command_history(
    count: int = Field(
        default=10, description="Number of recent commands to return (default: 10)"
    ),
    output_format: str = Field(
        default="markdown", description="Output format: 'markdown', 'json', or 'text'"
    ),
) -> Union[str, TextContent]:
    if isinstance(count, FieldInfo):
        count = count.default
    if isinstance(output_format, FieldInfo):
        output_format = output_format.default

    try:
        # Get recent history
        recent_history = command_history[-count:] if command_history else []

        if not recent_history:
            message = "No command history available."
        else:
            if output_format == "json":
                message = json.dumps(recent_history, indent=2)
            elif output_format == "text":
                history_lines = []
                for i, entry in enumerate(recent_history, 1):
                    status = "SUCCESS" if entry["success"] else "FAILED"
                    history_lines.append(
                        f"{i}. [{entry['timestamp']}] {entry['command']} - {status}"
                        f" ({entry.get('duration', 'N/A')})"
                    )
                message = "\n".join(history_lines)
            else:  # markdown
                history_lines = [
                    "# Command History",
                    f"Showing {len(recent_history)} recent commands:\n",
                ]

                for i, entry in enumerate(recent_history, 1):
                    status_emoji = "✅" if entry["success"] else "❌"
                    history_lines.extend(
                        [
                            f"## {i}. {status_emoji} `{entry['command']}`",
                            f"- **Timestamp:** {entry['timestamp']}",
                            f"- **Duration:** {entry.get('duration', 'N/A')}",
                            "",
                        ]
                    )

                message = "\n".join(history_lines)

        metadata = TerminalMetadata(
            command="get_command_history",
            platform=platform_info["system"],
            working_directory=str(workspace),
            timeout_seconds=0,
            history_count=len(recent_history),
        )

        action_response = ActionResponse(
            success=True, message=message, metadata=metadata.model_dump()
        )
        output_dict = {
            "artifact_type": "MARKDOWN",
            "artifact_data": json.dumps(
                action_response.model_dump()
            )
        }
        return TextContent(
            type="text",
            text=json.dumps(
                action_response.model_dump()
            ),  # Empty string instead of None
            **{"metadata": output_dict},  # Pass as additional fields
        )

    except Exception as e:
        error_msg = f"Failed to retrieve command history: {str(e)}"
        logging.error(f"History retrieval error: {traceback.format_exc()}")

        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata=TerminalMetadata(
                command="get_command_history",
                platform=platform_info["system"],
                working_directory=str(workspace),
                timeout_seconds=0,
                error_type="internal_error",
            ).model_dump(),
        )
        return TextContent(
            type="text",
            text=json.dumps(
                action_response.model_dump()
            ),  # Empty string instead of None
            **{"metadata": {}},  # Pass as additional fields
        )


@mcp.tool(
    description="""
Get information about terminal service capabilities and configuration.
"""
)
async def get_terminal_capabilities() -> Union[str, TextContent]:
    capabilities = {
        "platform_info": platform_info,
        "supported_features": [
            "Cross-platform command execution",
            "Configurable timeout controls",
            "Command history tracking",
            "Safety checks for dangerous commands",
            "Multiple output formats (markdown, json, text)",
            "LLM-optimized result formatting",
            "Async command execution",
        ],
        "supported_formats": ["markdown", "json", "text"],
        "configuration": {
            "max_history_size": max_history_size,
            "current_history_count": len(command_history),
            "working_directory": str(workspace),
            "dangerous_commands_count": len(dangerous_commands),
        },
        "safety_features": [
            "Dangerous command detection",
            "Timeout controls",
            "Error handling and logging",
            "Command validation",
        ],
    }

    formatted_info = f"""# Terminal Service Capabilities

            ## Platform Information
            - **System:** {platform_info["system"]}
            - **Platform:** {platform_info["platform"]}
            - **Architecture:** {platform_info["architecture"]}

            ## Features
            {chr(10).join(f"- {feature}" for feature in capabilities["supported_features"])}

            ## Supported Output Formats
            {chr(10).join(f"- {fmt}" for fmt in capabilities["supported_formats"])}

            ## Current Configuration
            - **Max History Size:** {capabilities["configuration"]["max_history_size"]}
            - **Current History Count:** {capabilities["configuration"]["current_history_count"]}
            - **Working Directory:** {capabilities["configuration"]["working_directory"]}
            - **Dangerous Commands Monitored:** {capabilities["configuration"]["dangerous_commands_count"]}

            ## Safety Features
            {chr(10).join(f"- {feature}" for feature in capabilities["safety_features"])}
            """

    action_response = ActionResponse(
        success=True, message=formatted_info, metadata=capabilities
    )
    output_dict = {
        "artifact_type": "MARKDOWN",
        "artifact_data": json.dumps(
            action_response.model_dump()
        )
    }
    return TextContent(
        type="text",
        text=json.dumps(action_response.model_dump()),  # Empty string instead of None
        **{"metadata": output_dict},  # Pass as additional fields
    )


def _check_command_safety(command: str) -> tuple[bool, str | None]:
    """Check if command is safe to execute.

    Args:
        command: Command string to check

    Returns:
        Tuple of (is_safe, reason_if_unsafe)
    """
    command_lower = command.lower().strip()

    for dangerous_cmd in dangerous_commands:
        if dangerous_cmd.lower() in command_lower:
            return False, f"Command contains dangerous pattern: {dangerous_cmd}"

    return True, None


def _format_command_output(
    result: CommandResult, output_format: str = "markdown"
) -> str:
    """Format command execution results for LLM consumption.

    Args:
        result: Command execution result
        output_format: Format type ('markdown', 'json', 'text')

    Returns:
        Formatted string suitable for LLM consumption
    """
    if output_format == "json":
        return json.dumps(result.model_dump(), indent=2)

    elif output_format == "text":
        output_parts = [
            f"Command: {result.command}",
            f"Status: {'SUCCESS' if result.success else 'FAILED'}",
            f"Duration: {result.duration}",
            f"Return Code: {result.return_code}",
        ]

        if result.stdout:
            output_parts.extend(["\nOutput:", result.stdout])

        if result.stderr:
            output_parts.extend(["\nErrors/Warnings:", result.stderr])

        return "\n".join(output_parts)

    else:  # markdown (default)
        status_emoji = "✅" if result.success else "❌"

        output_parts = [
            f"# Terminal Command Execution {status_emoji}",
            f"**Command:** `{result.command}`",
            f"**Status:** {'SUCCESS' if result.success else 'FAILED'}",
            f"**Duration:** {result.duration}",
            f"**Return Code:** {result.return_code}",
            f"**Timestamp:** {result.timestamp}",
        ]

        if result.stdout:
            output_parts.extend(["\n## Output", "```", result.stdout.strip(), "```"])

        if result.stderr:
            output_parts.extend(
                ["\n## Errors/Warnings", "```", result.stderr.strip(), "```"]
            )

        return "\n".join(output_parts)


async def _execute_command_async(command: str, timeout: int) -> CommandResult:
    """Execute command asynchronously with timeout.

    Args:
        command: Command to execute
        timeout: Timeout in seconds

    Returns:
        CommandResult with execution details
    """
    start_time = datetime.now()

    try:
        # Create appropriate subprocess for platform
        if platform_info["system"] == "Windows":
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True,
            )
        else:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True,
                executable="/bin/bash",
            )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout)
            stdout = stdout.decode("utf-8", errors="replace")
            stderr = stderr.decode("utf-8", errors="replace")
            return_code = process.returncode

        except asyncio.TimeoutError:
            try:
                process.kill()
            except Exception:
                pass

            duration = str(datetime.now() - start_time)
            return CommandResult(
                command=command,
                success=False,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                return_code=-1,
                duration=duration,
                timestamp=start_time.isoformat(),
            )

        duration = str(datetime.now() - start_time)
        result = CommandResult(
            command=command,
            success=return_code == 0,
            stdout=stdout,
            stderr=stderr,
            return_code=return_code,
            duration=duration,
            timestamp=start_time.isoformat(),
        )

        # Add to history
        command_history.append(
            {
                "timestamp": start_time.isoformat(),
                "command": command,
                "success": return_code == 0,
                "duration": duration,
            }
        )

        # Maintain history size limit
        if len(command_history) > max_history_size:
            command_history.pop(0)

        return result

    except Exception as e:
        duration = str(datetime.now() - start_time)
        return CommandResult(
            command=command,
            success=False,
            stdout="",
            stderr=f"Error executing command: {str(e)}",
            return_code=-1,
            duration=duration,
            timestamp=start_time.isoformat(),
        )


if __name__ == "__main__":
    load_dotenv(override=True)
    logging.info("Starting terminal-server MCP server!")
    mcp.run(transport="stdio")
