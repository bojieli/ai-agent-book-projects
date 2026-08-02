"""MCP server for execution tools."""

import asyncio
import json
from typing import Any
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from config import Config
from llm_helper import LLMHelper
from file_tools import FileTools
from execution_tools import ExecutionTools
from external_tools import ExternalTools
from extended_tools import ExtendedTools


# Initialize server
server = Server("execution-tools")

# Initialize tools
llm_helper = LLMHelper()
file_tools = FileTools(llm_helper)
execution_tools = ExecutionTools(llm_helper)
external_tools = ExternalTools(llm_helper)
extended_tools = ExtendedTools()


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="file_write",
            description="Write content to a file with automatic syntax verification",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path (relative to workspace or absolute)"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write"
                    },
                    "overwrite": {
                        "type": "boolean",
                        "description": "Whether to overwrite existing files",
                        "default": False
                    }
                },
                "required": ["path", "content"]
            }
        ),
        types.Tool(
            name="file_edit",
            description="Edit an existing file by searching and replacing content",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path"
                    },
                    "search": {
                        "type": "string",
                        "description": "Text to search for"
                    },
                    "replace": {
                        "type": "string",
                        "description": "Replacement text"
                    }
                },
                "required": ["path", "search", "replace"]
            }
        ),
        types.Tool(
            name="code_interpreter",
            description="Execute code in multiple programming languages in a sandboxed environment with result analysis. Supports: Python, JavaScript, TypeScript, Go, Java, C++, Rust, PHP, Bash",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Code to execute"
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language (python, javascript, typescript, go, java, cpp, rust, php, bash)",
                        "default": "python"
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Execution timeout in seconds",
                        "default": 30.0
                    },
                    "stdin": {
                        "type": "string",
                        "description": "Optional stdin input for the program"
                    },
                    "files": {
                        "type": "object",
                        "description": "Optional additional files (filename -> content mapping)",
                        "additionalProperties": {"type": "string"}
                    }
                },
                "required": ["code"]
            }
        ),
        types.Tool(
            name="virtual_terminal",
            description="Execute shell commands with error summarization",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds",
                        "default": 30
                    }
                },
                "required": ["command"]
            }
        ),
        types.Tool(
            name="google_calendar_add",
            description="Add an event to Google Calendar",
            inputSchema={
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Event title"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Start time (ISO 8601 format, e.g., 2024-01-01T10:00:00)"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time (ISO 8601 format)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Event description"
                    },
                    "location": {
                        "type": "string",
                        "description": "Event location"
                    }
                },
                "required": ["summary", "start_time", "end_time"]
            }
        ),
        types.Tool(
            name="github_create_pr",
            description="Create a GitHub Pull Request",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Repository name (format: owner/repo)"
                    },
                    "title": {
                        "type": "string",
                        "description": "PR title"
                    },
                    "body": {
                        "type": "string",
                        "description": "PR description"
                    },
                    "head_branch": {
                        "type": "string",
                        "description": "Source branch"
                    },
                    "base_branch": {
                        "type": "string",
                        "description": "Target branch",
                        "default": "main"
                    }
                },
                "required": ["repo_name", "title", "body", "head_branch"]
            }
        ),
        types.Tool(
            name="excel_create_with_formula_and_screenshot",
            description="Create an XLSX workbook, apply formulas, and render a real screenshot with LibreOffice",
            inputSchema={
                "type": "object",
                "properties": {
                    "output_path": {"type": "string"},
                    "rows": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "item": {"type": "string"},
                                "quantity": {"type": "number"},
                                "unit_price": {"type": "number"},
                            },
                            "required": ["item", "quantity", "unit_price"],
                        },
                    },
                },
                "required": ["output_path", "rows"],
            }
        ),
        types.Tool(
            name="webhook_post",
            description="POST JSON to a real HTTPS webhook endpoint",
            inputSchema={"type": "object", "properties": {
                "url": {"type": "string"}, "payload": {"type": "object"}},
                "required": ["url", "payload"]}
        ),
        types.Tool(
            name="browser_navigate",
            description="Navigate with real headless Chromium, extract page content, and save a screenshot",
            inputSchema={"type": "object", "properties": {
                "url": {"type": "string"}, "screenshot_path": {"type": "string"}},
                "required": ["url", "screenshot_path"]}
        ),
        types.Tool(
            name="virtual_desktop_execute",
            description="Drive a headful Chromium desktop through X11 keyboard events and retain a screenshot",
            inputSchema={"type": "object", "properties": {
                "url": {"type": "string"},
                "screenshot_path": {"type": "string"},
                "expected_title": {"type": ["string", "null"]}},
                "required": ["url", "screenshot_path"]}
        ),
        types.Tool(
            name="virtual_mobile_execute",
            description="Operate a running AndroidWorld emulator through ADB and retain a screenshot",
            inputSchema={"type": "object", "properties": {
                "container_name": {"type": "string"},
                "screenshot_path": {"type": "string"}},
                "required": ["container_name", "screenshot_path"]}
        ),
        types.Tool(
            name="environment_capabilities",
            description="Inspect real Computer Use container and Android device availability",
            inputSchema={"type": "object", "properties": {}}
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str,
    arguments: dict[str, Any] | None
) -> list[types.TextContent]:
    """Handle tool calls."""
    if arguments is None:
        arguments = {}
    
    try:
        # Route to appropriate tool
        if name == "file_write":
            result = await file_tools.write_file(
                path=arguments["path"],
                content=arguments["content"],
                overwrite=arguments.get("overwrite", False)
            )
        elif name == "file_edit":
            result = await file_tools.edit_file(
                path=arguments["path"],
                search=arguments["search"],
                replace=arguments["replace"]
            )
        elif name == "code_interpreter":
            result = await execution_tools.code_interpreter(
                code=arguments["code"],
                language=arguments.get("language") or "python",
                timeout=arguments.get("timeout", 30.0),
                stdin=arguments.get("stdin"),
                files=arguments.get("files")
            )
        elif name == "virtual_terminal":
            result = await execution_tools.virtual_terminal(
                command=arguments["command"],
                timeout=arguments.get("timeout", 30)
            )
        elif name == "google_calendar_add":
            result = await external_tools.google_calendar_add(
                summary=arguments["summary"],
                start_time=arguments["start_time"],
                end_time=arguments["end_time"],
                description=arguments.get("description"),
                location=arguments.get("location")
            )
        elif name == "github_create_pr":
            result = await external_tools.github_create_pr(
                repo_name=arguments["repo_name"],
                title=arguments["title"],
                body=arguments["body"],
                head_branch=arguments["head_branch"],
                base_branch=arguments.get("base_branch", "main")
            )
        elif name == "excel_create_with_formula_and_screenshot":
            result = await extended_tools.excel_create_with_formula_and_screenshot(
                arguments["output_path"], arguments["rows"])
        elif name == "webhook_post":
            result = await extended_tools.webhook_post(arguments["url"], arguments["payload"])
        elif name == "browser_navigate":
            result = await extended_tools.browser_navigate(
                arguments["url"], arguments["screenshot_path"])
        elif name == "virtual_desktop_execute":
            result = await extended_tools.virtual_desktop_execute(
                arguments["url"], arguments["screenshot_path"], arguments.get("expected_title"))
        elif name == "virtual_mobile_execute":
            result = await extended_tools.virtual_mobile_execute(
                arguments["container_name"], arguments["screenshot_path"])
        elif name == "environment_capabilities":
            result = await extended_tools.environment_capabilities()
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        # Format result
        return [
            types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]
        
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"Tool execution failed: {str(e)}"
                }, indent=2)
            )
        ]


async def main():
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="execution-tools",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
