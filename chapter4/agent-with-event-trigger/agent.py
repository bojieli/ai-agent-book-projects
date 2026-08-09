"""
Event-Triggered AI Agent with System Hints
An agent that responds to events from various sources while maintaining
all the system hint features from the original implementation.
"""

import json
import os
import sys
import subprocess
import platform
import logging
import concurrent.futures
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import requests
from openai import OpenAI
import traceback
import tempfile
import shutil
from pathlib import Path
from event_types import Event, EventType
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _reasoning_safe_temperature(model, requested=1.0):
    """Reasoning models (Kimi K3, GPT-5, ...) only accept temperature=1.
    Return 1 for those; otherwise the requested value so non-reasoning
    providers (Doubao, DeepSeek, older Moonshot) are unchanged."""
    m = str(model or "").lower().replace("/", "-")
    return 1 if ("kimi-k3" in m or "gpt-5" in m) else requested


# Per-provider env var holding that provider's API key.
_PROVIDER_KEY_ENV = {
    "dashscope": "DASHSCOPE_API_KEY",
    "qwen": "DASHSCOPE_API_KEY",
    "bailian": "DASHSCOPE_API_KEY",
    "siliconflow": "SILICONFLOW_API_KEY",
    "doubao": "DOUBAO_API_KEY",
    "kimi": "KIMI_API_KEY",
    "moonshot": "KIMI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}


def resolve_provider_and_key(provider: Optional[str] = None):
    """Resolve (provider, api_key) applying a universal OpenRouter fallback.

    Preferred provider (default from LLM_PROVIDER, else 'kimi') is used as today
    when its own key is present. Otherwise, if OPENROUTER_API_KEY is set, fall
    back to the already-supported 'openrouter' provider so the agent still runs.
    Returns (provider, None) when no usable key is found, leaving the caller to
    emit its own error.
    """
    provider = (provider or os.getenv("LLM_PROVIDER", "kimi")).lower()
    provider = {"qwen": "dashscope", "bailian": "dashscope"}.get(provider, provider)
    key_env = _PROVIDER_KEY_ENV.get(provider)
    api_key = os.getenv(key_env) if key_env else None
    if api_key:
        return provider, api_key
    or_key = os.getenv("OPENROUTER_API_KEY")
    if or_key:
        return "openrouter", or_key
    return provider, None


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TodoStatus(Enum):
    """Status of a TODO item"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class TodoItem:
    """Represents a single TODO item"""
    id: int
    content: str
    status: TodoStatus = TodoStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: Optional[str] = None


@dataclass
class ToolCall:
    """Represents a single tool call with enhanced tracking"""
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
    call_number: int = 1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_ms: Optional[int] = None


@dataclass
class SystemHintConfig:
    """Configuration for system hints"""
    enable_timestamps: bool = True
    enable_tool_counter: bool = True
    enable_todo_list: bool = True
    enable_detailed_errors: bool = True
    enable_system_state: bool = True
    timestamp_format: str = "%Y-%m-%d %H:%M:%S"
    simulate_time_delay: bool = False
    save_trajectory: bool = True
    trajectory_file: str = "trajectory.json"
    # Model configuration (matching conversational_agent.py)
    temperature: float = 0.7
    max_tokens: int = 4096
    # MCP server configuration
    use_mcp_servers: bool = False  # Disabled by default - requires async setup
    mcp_collaboration_tools_path: str = "../collaboration-tools/src/main.py"
    mcp_execution_tools_path: str = "../execution-tools/server.py"
    mcp_perception_tools_path: str = "../perception-tools/src/main.py"


class MCPServerManager:
    """Manages connections to multiple MCP servers"""
    
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.tools: Dict[str, Any] = {}
        self.server_contexts = []  # Store context managers for proper cleanup
        
    async def connect_server(self, name: str, script_path: str) -> bool:
        """
        Connect to an MCP server with proper error isolation
        
        NOTE: This stores tool metadata only. For actual tool execution,
        you'll need to spawn MCP servers differently or use built-in tools.
        
        Args:
            name: Server name
            script_path: Path to the MCP server script
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Check if script exists
            if not os.path.exists(script_path):
                logger.warning(f"MCP server script not found: {script_path}")
                return False
            
            logger.info(f"Discovering tools from MCP server '{name}' at {script_path}")
            
            server_params = StdioServerParameters(
                command=sys.executable,
                args=[script_path],
                env=os.environ.copy()  # Pass through environment variables
            )
            
            # Use a temporary connection just to discover tools
            # The actual tool execution will spawn servers on-demand
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # Discover tools
                    tools_result = await session.list_tools()
                    tools = tools_result.tools
                    
                    # Store tool metadata (not live session)
                    for tool in tools:
                        # Use underscore separator for valid function names
                        # OpenAI-compatible APIs reject names with dots
                        tool_key = f"{name}_{tool.name}"
                        self.tools[tool_key] = {
                            "server": name,
                            "tool": tool,
                            "script_path": script_path,
                            "server_params": server_params
                        }
                    
                    logger.info(f"✅ Discovered tools from '{name}': {len(tools)} tools")
                    return True
                    
        except Exception as e:
            logger.warning(f"Failed to discover tools from '{name}': {str(e)[:100]}")
            return False
    
    async def call_tool(self, tool_key: str, arguments: Dict[str, Any]) -> Any:
        """
        Call an MCP tool by spawning a fresh server connection
        
        Args:
            tool_key: Tool key in format "server.tool_name"
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        if tool_key not in self.tools:
            raise ValueError(f"Unknown MCP tool: {tool_key}")
        
        tool_info = self.tools[tool_key]
        tool = tool_info["tool"]
        server_params = tool_info["server_params"]
        
        try:
            # Spawn fresh connection for this tool call
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool.name, arguments)
                    
                    # Extract text content from result
                    text_content = []
                    if hasattr(result, 'content'):
                        for c in result.content:
                            if isinstance(c, TextContent):
                                text_content.append(c.text)
                    
                    return {
                        "success": True,
                        "result": "\n".join(text_content) if text_content else str(result)
                    }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def disconnect_all(self):
        """
        Cleanup MCP manager (no persistent connections to close)
        
        Since we spawn fresh connections for each tool call,
        there's nothing to disconnect.
        """
        logger.info("MCP manager cleanup complete (no persistent connections)")
        self.sessions.clear()
        self.tools.clear()
        self.server_contexts.clear()


class EventTriggeredAgent:
    """
    Event-Triggered AI Agent with System Hints
    Responds to events while maintaining all system hint capabilities
    """
    
    def __init__(self, api_key: str, provider: str = "kimi", 
                 model: Optional[str] = None, config: Optional[SystemHintConfig] = None,
                 verbose: bool = True):
        """
        Initialize the event-triggered agent
        
        Args:
            api_key: API key for the LLM provider
            provider: LLM provider ('dashscope'/'qwen'/'bailian', 'siliconflow', 'doubao', 'kimi', 'moonshot', 'openrouter')
            model: Optional model override
            config: System hint configuration
            verbose: If True, log full details
        """
        self.provider = provider.lower()
        self.provider = {"qwen": "dashscope", "bailian": "dashscope"}.get(
            self.provider, self.provider
        )
        self.verbose = verbose
        self.config = config or SystemHintConfig()
        
        # Configure client based on provider (matching conversational_agent.py)
        if self.provider == "dashscope":
            self.client = OpenAI(
                api_key=api_key,
                base_url=os.getenv(
                    "DASHSCOPE_BASE_URL",
                    "https://dashscope.aliyuncs.com/compatible-mode/v1",
                )
            )
            self.model = model or "qwen3.7-plus"
        elif self.provider == "siliconflow":
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.siliconflow.cn/v1"
            )
            self.model = model or "Qwen/Qwen3-235B-A22B-Thinking-2507"
        elif self.provider == "doubao":
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://ark.cn-beijing.volces.com/api/v3"
            )
            self.model = model or "doubao-seed-1-6-thinking-250715"
        elif self.provider == "kimi" or self.provider == "moonshot":
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.moonshot.cn/v1"
            )
            self.model = model or "kimi-k3"
        elif self.provider == "openrouter":
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
            # Default to Gemini 3.5 Flash, but allow any of the supported models
            self.model = model or "google/gemini-3.5-flash"
            # Supported models: google/gemini-3.5-flash, openai/gpt-5.6-luna, anthropic/claude-sonnet-4.6
        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'dashscope'/'qwen'/'bailian', 'siliconflow', 'doubao', 'kimi', 'moonshot', or 'openrouter'")
        
        # Initialize tracking
        self.tool_call_counts: Dict[str, int] = {}
        self.tool_calls: List[ToolCall] = []
        self.todo_list: List[TodoItem] = []
        self.next_todo_id = 1
        
        # Initialize conversation history
        self.conversation_history = []
        self.simulated_time = datetime.now()
        self._init_system_prompt()
        
        # Track current working directory
        self.current_directory = os.getcwd()
        
        # Event tracking
        self.last_user_interaction = datetime.now()
        self.background_processes: Dict[str, Dict[str, Any]] = {}
        
        # Initialize MCP server manager
        self.mcp_manager = MCPServerManager()
        self.mcp_tools_loaded = False
        
        logger.info(f"Event-Triggered Agent initialized with provider: {self.provider}, model: {self.model}")
        logger.info("Note: Call load_mcp_tools() to connect to MCP servers")
    
    async def load_mcp_tools(self):
        """
        Load tools from MCP servers
        
        This must be called in an async context after agent initialization.
        """
        if not self.config.use_mcp_servers:
            logger.info("MCP servers disabled in config")
            return
        
        logger.info("Loading tools from MCP servers...")
        
        # Get the directory where the agent script is located
        agent_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Try to connect to collaboration-tools
        collab_path = os.path.join(agent_dir, self.config.mcp_collaboration_tools_path)
        collab_loaded = await self.mcp_manager.connect_server("collaboration", collab_path)
        
        # Try to connect to execution-tools
        exec_path = os.path.join(agent_dir, self.config.mcp_execution_tools_path)
        exec_loaded = await self.mcp_manager.connect_server("execution", exec_path)
        
        # Try to connect to perception-tools
        percept_path = os.path.join(agent_dir, self.config.mcp_perception_tools_path)
        percept_loaded = await self.mcp_manager.connect_server("perception", percept_path)
        
        # Set flag if any tools were loaded
        self.mcp_tools_loaded = collab_loaded or exec_loaded or percept_loaded
        
        if self.mcp_tools_loaded:
            logger.info(f"✅ MCP tools loaded: {len(self.mcp_manager.tools)} tools available")
            logger.info(f"   Available MCP tools: {list(self.mcp_manager.tools.keys())[:5]}...")
        else:
            logger.info("⚠️  No MCP servers found, using built-in tools only")
    
    def _init_system_prompt(self):
        """Initialize the system prompt for the conversation"""
        system_content = """You are an intelligent assistant with access to various tools for file operations, code execution, and system commands.

You respond to events from multiple sources including:
- User messages from web interfaces and instant messaging
- Email replies and GitHub notifications
- System reminders and timeout alerts
- Timer triggers and process monitoring events

Your task is to complete the given objectives efficiently using the available tools. Think step by step and use tools as needed.

## TODO List Management Rules:
- For any complex task with 3+ distinct steps, immediately create a TODO list using `rewrite_todo_list`
- Break down the user's request into specific, actionable TODO items
- Update TODO items to 'in_progress' when starting work on them using `update_todo_status`
- Mark items as 'completed' immediately after finishing them
- Only have ONE item 'in_progress' at a time
- If you encounter errors or need to change approach, update relevant TODOs to 'cancelled' and add new ones
- Use the TODO list as your primary planning and tracking mechanism
- Reference TODO items by their ID when discussing progress

## Key Behaviors:
1. ALWAYS start complex tasks by creating a TODO list
2. Pay attention to timestamps to understand the timeline of events
3. Notice tool call numbers (e.g., "Tool call #3") to avoid repetitive loops - if you see high numbers, change strategy
4. Learn from detailed error messages to fix issues and adapt your approach
5. Be aware of your current directory and system environment shown in system state
6. When exploring projects, systematically read key files (README, main.py, agent.py) to understand structure

## Event Response Guidelines:
- Acknowledge the event source in your response
- For timeout events, proactively check status and take appropriate action
- For system alerts, investigate the issue before responding
- Maintain context across multiple events from the same conversation

## Error Handling:
- Read error messages carefully - they contain specific information about what went wrong
- Use the suggestions provided in error messages to fix issues
- If a tool fails multiple times (check the call number), try a different approach
- Common fixes: check file paths, verify current directory, ensure proper permissions

Important: When you have completed all tasks, clearly state "FINAL ANSWER:" followed by a comprehensive summary of what was accomplished."""
        
        self.conversation_history = [
            {
                "role": "system",
                "content": system_content
            }
        ]
    
    def _get_system_state(self) -> str:
        """Get current system state information"""
        if not self.config.enable_system_state:
            return ""
        
        # Detect OS
        system = platform.system()
        if system == "Windows":
            shell_type = "Windows Command Prompt or PowerShell"
        elif system == "Darwin":
            shell_type = "macOS Terminal (zsh/bash)"
        else:
            shell_type = f"Linux Shell ({os.environ.get('SHELL', 'bash')})"
        
        state_info = [
            f"Current Time: {self._get_timestamp()}",
            f"Current Directory: {self.current_directory}",
            f"System: {system} ({platform.release()})",
            f"Shell Environment: {shell_type}",
            f"Python Version: {sys.version.split()[0]}"
        ]
        
        # Add background process info if any
        if self.background_processes:
            state_info.append(f"Background Processes: {len(self.background_processes)} active")
        
        return "\n".join(state_info)
    
    def _get_timestamp(self) -> str:
        """Get formatted timestamp"""
        if self.config.simulate_time_delay:
            return self.simulated_time.strftime(self.config.timestamp_format)
        return datetime.now().strftime(self.config.timestamp_format)
    
    def _advance_simulated_time(self, hours: int = 0, minutes: int = 0, seconds: int = 30):
        """Advance simulated time for demo purposes"""
        if self.config.simulate_time_delay:
            self.simulated_time += timedelta(hours=hours, minutes=minutes, seconds=seconds)
    
    def _save_trajectory(self, iteration: int, final_answer: Optional[str] = None):
        """Save current trajectory to JSON file for debugging"""
        if not self.config.save_trajectory:
            return
        
        trajectory_data = {
            "timestamp": datetime.now().isoformat(),
            "iteration": iteration,
            "provider": self.provider,
            "model": self.model,
            "conversation_history": self.conversation_history,
            "tool_calls": [
                {
                    "tool_name": call.tool_name,
                    "arguments": call.arguments,
                    "result": call.result,
                    "error": call.error,
                    "call_number": call.call_number,
                    "timestamp": call.timestamp,
                    "duration_ms": call.duration_ms
                }
                for call in self.tool_calls
            ],
            "todo_list": [
                {
                    "id": item.id,
                    "content": item.content,
                    "status": item.status.value,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at
                }
                for item in self.todo_list
            ],
            "current_directory": self.current_directory,
            "final_answer": final_answer,
            "background_processes": self.background_processes,
            "config": {
                "enable_timestamps": self.config.enable_timestamps,
                "enable_tool_counter": self.config.enable_tool_counter,
                "enable_todo_list": self.config.enable_todo_list,
                "enable_detailed_errors": self.config.enable_detailed_errors,
                "enable_system_state": self.config.enable_system_state,
                "timestamp_format": self.config.timestamp_format,
                "simulate_time_delay": self.config.simulate_time_delay
            }
        }
        
        try:
            with open(self.config.trajectory_file, 'w', encoding='utf-8') as f:
                json.dump(trajectory_data, f, indent=2, ensure_ascii=False)
            
            if self.verbose:
                logger.info(f"Trajectory saved to {self.config.trajectory_file} (iteration {iteration})")
        except Exception as e:
            logger.warning(f"Failed to save trajectory: {e}")
    
    def _format_todo_list(self) -> str:
        """Format TODO list for display"""
        if not self.todo_list:
            return "TODO List: Empty"
        
        lines = ["TODO List:"]
        for item in self.todo_list:
            status_symbol = {
                TodoStatus.PENDING: "⏳",
                TodoStatus.IN_PROGRESS: "🔄",
                TodoStatus.COMPLETED: "✅",
                TodoStatus.CANCELLED: "❌"
            }.get(item.status, "❓")
            
            lines.append(f"  [{item.id}] {status_symbol} {item.content} ({item.status.value})")
        
        return "\n".join(lines)
    
    def _get_system_hint(self) -> Optional[str]:
        """Get system hint content with current state"""
        if not any([self.config.enable_system_state, self.config.enable_todo_list]):
            return None
        
        hint_parts = []
        
        if self.config.enable_system_state:
            hint_parts.append("=== SYSTEM STATE ===")
            hint_parts.append(self._get_system_state())
            hint_parts.append("")
        
        if self.config.enable_todo_list and self.todo_list:
            hint_parts.append("=== CURRENT TASKS ===")
            hint_parts.append(self._format_todo_list())
            hint_parts.append("")
        
        if hint_parts:
            return "\n".join(hint_parts)
        return None
    
    def _get_tools_description(self) -> List[Dict[str, Any]]:
        """Get tool descriptions for the model"""
        tools = []
        
        # Add MCP tools if available
        if self.mcp_tools_loaded:
            for tool_key, tool_info in self.mcp_manager.tools.items():
                mcp_tool = tool_info["tool"]
                
                # Convert MCP tool schema to OpenAI function format
                tool_desc = {
                    "type": "function",
                    "function": {
                        "name": tool_key,  # Use prefixed name (e.g., "collaboration.mcp_browser_navigate")
                        "description": mcp_tool.description or mcp_tool.name,
                        "parameters": mcp_tool.inputSchema if hasattr(mcp_tool, 'inputSchema') else {
                            "type": "object",
                            "properties": {}
                        }
                    }
                }
                tools.append(tool_desc)
        else:
            # Fallback to built-in tools if MCP servers not available
            tools.extend([
                {
                    "type": "function",
                    "function": {
                        "name": "read_file",
                        "description": "Read the contents of a text file. Returns error for binary files. Supports partial reading for large files.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "Path to the file to read (absolute or relative to current directory)"
                                },
                                "begin_line": {
                                    "type": "integer",
                                    "description": "Optional: Line number to start reading from (1-based indexing)"
                                },
                                "number_lines": {
                                    "type": "integer",
                                    "description": "Optional: Number of lines to read from begin_line"
                                }
                            },
                            "required": ["file_path"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "write_file",
                        "description": "Write content to a file (creates or overwrites)",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "Path to the file to write"
                                },
                                "content": {
                                    "type": "string",
                                    "description": "Content to write to the file"
                                }
                            },
                            "required": ["file_path", "content"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "code_interpreter",
                        "description": "Execute Python code in a restricted environment",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "code": {
                                    "type": "string",
                                    "description": "Python code to execute"
                                }
                            },
                            "required": ["code"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "execute_command",
                        "description": "Execute a shell command in the current directory",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "command": {
                                    "type": "string",
                                    "description": "Shell command to execute"
                                },
                                "working_dir": {
                                    "type": "string",
                                    "description": "Optional working directory for the command"
                                }
                            },
                            "required": ["command"]
                        }
                    }
                }
            ])
        
        # Always add TODO management tools if enabled
        if self.config.enable_todo_list:
            tools.extend([
                {
                    "type": "function",
                    "function": {
                        "name": "rewrite_todo_list",
                        "description": "Rewrite the TODO list with new pending items (keeps completed/cancelled items)",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "items": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    },
                                    "description": "List of new TODO items to add as pending"
                                }
                            },
                            "required": ["items"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "update_todo_status",
                        "description": "Update the status of existing TODO items",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "updates": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": {
                                                "type": "integer",
                                                "description": "TODO item ID"
                                            },
                                            "status": {
                                                "type": "string",
                                                "enum": ["pending", "in_progress", "completed", "cancelled"],
                                                "description": "New status for the item"
                                            }
                                        },
                                        "required": ["id", "status"]
                                    },
                                    "description": "List of TODO items to update with their new status"
                                }
                            },
                            "required": ["updates"]
                        }
                    }
                }
            ])
        
        return tools
    
    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Tuple[Any, Optional[str]]:
        """Execute a tool and return the result with detailed error information"""
        start_time = datetime.now()
        
        try:
            # Check if it's an MCP tool (prefixed with server name using underscore)
            if "_" in tool_name and tool_name in self.mcp_manager.tools:
                # Execute MCP tool asynchronously
                # Check if there's already a running event loop
                try:
                    loop = asyncio.get_running_loop()
                    # If we're already in an async context, we can't use asyncio.run()
                    # Create a new event loop in a separate thread
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            self.mcp_manager.call_tool(tool_name, arguments)
                        )
                        result = future.result()
                except RuntimeError:
                    # No event loop running, safe to use asyncio.run()
                    result = asyncio.run(self.mcp_manager.call_tool(tool_name, arguments))
                
                duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                return result, None if result.get("success") else result.get("error")
            
            # Built-in tools
            if tool_name == "read_file":
                result = self._tool_read_file(**arguments)
            elif tool_name == "write_file":
                result = self._tool_write_file(**arguments)
            elif tool_name == "code_interpreter":
                result = self._tool_code_interpreter(**arguments)
            elif tool_name == "execute_command":
                result = self._tool_execute_command(**arguments)
            elif tool_name == "rewrite_todo_list":
                result = self._tool_rewrite_todo_list(**arguments)
            elif tool_name == "update_todo_status":
                result = self._tool_update_todo_status(**arguments)
            else:
                error = f"Unknown tool: {tool_name}"
                return {"error": error}, error
            
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            return result, None
            
        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            error_detail = self._get_detailed_error(e, tool_name, arguments)
            
            if self.config.enable_detailed_errors:
                return {"error": error_detail}, error_detail
            else:
                return {"error": str(e)}, str(e)
    
    def _get_detailed_error(self, exception: Exception, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Get detailed error information for debugging"""
        error_parts = [
            f"Tool '{tool_name}' failed with {type(exception).__name__}: {str(exception)}",
            f"Arguments: {json.dumps(arguments, indent=2)}",
        ]
        
        if self.verbose:
            tb = traceback.format_exc()
            error_parts.append(f"Traceback:\n{tb}")
        
        suggestions = self._get_error_suggestions(exception, tool_name)
        if suggestions:
            error_parts.append(f"Suggestions: {suggestions}")
        
        return "\n".join(error_parts)
    
    def _get_error_suggestions(self, exception: Exception, tool_name: str) -> str:
        """Get suggestions for fixing common errors"""
        error_str = str(exception).lower()
        exception_type = type(exception).__name__
        
        suggestions = []
        
        if "permission" in error_str or exception_type == "PermissionError":
            suggestions.append("Check file/directory permissions")
            suggestions.append("Try using a different directory or running with appropriate permissions")
        elif "not found" in error_str or "no such file" in error_str or exception_type == "FileNotFoundError":
            suggestions.append("Verify the file/directory path exists")
            suggestions.append("Check the current working directory")
            suggestions.append("Use absolute paths or create the file/directory first")
        elif "syntax" in error_str or exception_type == "SyntaxError":
            suggestions.append("Check the code syntax")
            suggestions.append("Ensure proper indentation and valid Python syntax")
        elif "timeout" in error_str:
            suggestions.append("The operation took too long")
            suggestions.append("Try with simpler input or break into smaller steps")
        elif "import" in error_str or exception_type == "ImportError":
            suggestions.append("Required module not available in restricted environment")
            suggestions.append("Use only built-in Python modules")
        
        return " | ".join(suggestions) if suggestions else ""
    
    # Tool implementations (copied from original agent.py)
    def _tool_read_file(self, file_path: str, begin_line: Optional[int] = None, 
                       number_lines: Optional[int] = None) -> Dict[str, Any]:
        """Read file contents with optional line-based reading"""
        try:
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.current_directory, file_path)
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Check if it's a binary file
            try:
                with open(file_path, 'rb') as f:
                    chunk = f.read(1024)
                    if b'\x00' in chunk:
                        return {
                            "success": False,
                            "error": "Cannot read binary file. This tool only supports text files.",
                            "file_path": file_path,
                            "is_binary": True
                        }
                    try:
                        chunk.decode('utf-8')
                    except UnicodeDecodeError:
                        return {
                            "success": False,
                            "error": "File is not a valid text file (encoding error).",
                            "file_path": file_path,
                            "is_binary": True
                        }
            except Exception as e:
                raise
            
            with open(file_path, 'r', encoding='utf-8') as f:
                if begin_line is not None or number_lines is not None:
                    all_lines = f.readlines()
                    total_lines = len(all_lines)
                    
                    start_line = (begin_line - 1) if begin_line is not None else 0
                    if start_line < 0:
                        start_line = 0
                    if start_line >= total_lines:
                        return {
                            "success": False,
                            "error": f"begin_line {begin_line} is beyond file length ({total_lines} lines)",
                            "file_path": file_path,
                            "total_lines": total_lines
                        }
                    
                    if number_lines is not None:
                        end_line = min(start_line + number_lines, total_lines)
                    else:
                        end_line = total_lines
                    
                    selected_lines = all_lines[start_line:end_line]
                    content = ''.join(selected_lines)
                    
                    stat = os.stat(file_path)
                    
                    return {
                        "success": True,
                        "file_path": file_path,
                        "content": content,
                        "size_bytes": stat.st_size,
                        "total_lines": total_lines,
                        "begin_line": start_line + 1,
                        "end_line": end_line,
                        "lines_read": len(selected_lines),
                        "partial_read": True
                    }
                else:
                    content = f.read()
                    stat = os.stat(file_path)
                    
                    return {
                        "success": True,
                        "file_path": file_path,
                        "content": content,
                        "size_bytes": stat.st_size,
                        "lines": len(content.splitlines()),
                        "partial_read": False
                    }
        except Exception as e:
            raise
    
    def _tool_write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Write content to file"""
        try:
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.current_directory, file_path)
            
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "file_path": file_path,
                "bytes_written": len(content.encode('utf-8')),
                "lines_written": len(content.splitlines())
            }
        except Exception as e:
            raise
    
    def _tool_code_interpreter(self, code: str) -> Dict[str, Any]:
        """Execute Python code in restricted environment"""
        try:
            import io
            import contextlib
            
            output_buffer = io.StringIO()
            error_buffer = io.StringIO()
            
            # Use one namespace so functions defined by the snippet can resolve
            # names assigned earlier in the same snippet.
            exec_ns = {}
            with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(error_buffer):
                exec(code, exec_ns)
            
            stdout = output_buffer.getvalue()
            stderr = error_buffer.getvalue()
            
            return {
                "success": True,
                "stdout": stdout,
                "stderr": stderr,
            }
        except Exception as e:
            raise
    
    def _tool_execute_command(self, command: str, working_dir: Optional[str] = None) -> Dict[str, Any]:
        """Execute shell command"""
        try:
            if working_dir is None:
                working_dir = self.current_directory
            elif not os.path.isabs(working_dir):
                working_dir = os.path.join(self.current_directory, working_dir)
            
            if command.strip().startswith('cd '):
                new_dir = command.strip()[3:].strip()
                if not os.path.isabs(new_dir):
                    new_dir = os.path.join(self.current_directory, new_dir)
                
                if os.path.isdir(new_dir):
                    self.current_directory = os.path.abspath(new_dir)
                    return {
                        "success": True,
                        "command": command,
                        "output": f"Changed directory to: {self.current_directory}",
                        "return_code": 0
                    }
                else:
                    raise FileNotFoundError(f"Directory not found: {new_dir}")
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=working_dir,
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "command": command,
                "output": result.stdout,
                "error": result.stderr if result.stderr else None,
                "return_code": result.returncode,
                "working_dir": working_dir
            }
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Command timed out after 30 seconds: {command}")
        except Exception as e:
            raise
    
    def _tool_rewrite_todo_list(self, items: List[str]) -> Dict[str, Any]:
        """Rewrite TODO list with new pending items"""
        kept_items = [
            item for item in self.todo_list
            if item.status in [TodoStatus.COMPLETED, TodoStatus.CANCELLED]
        ]
        
        new_items = []
        for content in items:
            new_items.append(TodoItem(
                id=self.next_todo_id,
                content=content,
                status=TodoStatus.PENDING
            ))
            self.next_todo_id += 1
        
        self.todo_list = kept_items + new_items
        
        return {
            "success": True,
            "kept_items": len(kept_items),
            "new_items": len(new_items),
            "total_items": len(self.todo_list)
        }
    
    def _tool_update_todo_status(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update status of TODO items"""
        updated_count = 0
        
        for update in updates:
            item_id = update["id"]
            new_status = TodoStatus(update["status"])
            
            for item in self.todo_list:
                if item.id == item_id:
                    item.status = new_status
                    item.updated_at = datetime.now().isoformat()
                    updated_count += 1
                    break
        
        return {
            "success": True,
            "updated_items": updated_count,
            "total_items": len(self.todo_list)
        }
    
    def handle_event(self, event: Event, max_iterations: int = 20) -> Dict[str, Any]:
        """
        Handle an incoming event and generate a response
        
        Args:
            event: The event to handle
            max_iterations: Maximum number of tool call iterations
            
        Returns:
            Response with agent's actions and final answer
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"📥 RECEIVED EVENT")
        logger.info(f"{'='*80}")
        logger.info(f"Event Type: {event.event_type.value}")
        logger.info(f"Timestamp: {event.timestamp}")
        logger.info(f"Content: {event.content}")
        if event.metadata:
            logger.info(f"Metadata: {json.dumps(event.metadata, indent=2)}")
        logger.info(f"{'='*80}\n")
        
        # Convert event to user message
        user_message = event.to_user_message()
        
        # Add timestamp prefix if enabled
        if self.config.enable_timestamps:
            timestamp_prefix = f"[{self._get_timestamp()}] "
            user_message = timestamp_prefix + user_message
        
        # Update last user interaction time for external events
        if event.event_type in [EventType.WEB_MESSAGE, EventType.IM_MESSAGE, EventType.EMAIL_REPLY]:
            self.last_user_interaction = datetime.now()
        
        # Add user message to conversation
        self.conversation_history.append({"role": "user", "content": user_message})
        
        iteration = 0
        final_answer = None
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Iteration {iteration}/{max_iterations}")
            
            self._advance_simulated_time(seconds=5)
            self._save_trajectory(iteration)
            
            try:
                messages_to_send = self.conversation_history.copy()
                system_hint = self._get_system_hint()
                if system_hint:
                    messages_to_send.append({"role": "user", "content": system_hint})
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages_to_send,
                    tools=self._get_tools_description(),
                    tool_choice="auto",
                    temperature=_reasoning_safe_temperature(self.model, self.config.temperature),
                    max_tokens=self.config.max_tokens
                )
                
                message = response.choices[0].message
                has_tool_calls = bool(getattr(message, "tool_calls", None))

                # Terminal path: a text reply with no tool calls ends the loop,
                # even without the FINAL ANSWER: marker (e.g. a plain "hi"
                # reply). Previously only "FINAL ANSWER:" broke the loop, so
                # plain replies were re-sent for up to max_iterations.
                if not has_tool_calls:
                    self.conversation_history.append(message.model_dump())
                    content = (message.content or "").strip()
                    if content:
                        final_answer = (content.split("FINAL ANSWER:", 1)[1].strip()
                                        if "FINAL ANSWER:" in content else content)
                        logger.info(f"✅ Terminal text response (no tool calls); final answer: {final_answer[:100]}...")
                    else:
                        logger.warning("Empty model response with no tool calls; "
                                       "stopping to avoid burning remaining iterations")
                    self._save_trajectory(iteration, final_answer)
                    break

                if has_tool_calls:
                    self.conversation_history.append(message.model_dump())
                    
                    for tool_call in message.tool_calls:
                        function_name = tool_call.function.name
                        raw_args = tool_call.function.arguments or "{}"
                        try:
                            function_args = json.loads(raw_args)
                        except json.JSONDecodeError as exc:
                            # Malformed/truncated arguments must not abort the
                            # turn: the assistant message with tool_calls is
                            # already in the history, so bailing out here would
                            # leave this tool_call_id unanswered and every later
                            # request would be rejected by the provider.
                            err = (f"Invalid tool arguments (not valid JSON): {exc}. "
                                   f"Raw arguments: {raw_args[:500]}")
                            logger.warning(f"  ❌ {err}")
                            self.tool_calls.append(ToolCall(
                                tool_name=function_name, arguments={}, error=err))
                            self.conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps({"error": err})
                            })
                            continue

                        if self.config.enable_tool_counter:
                            self.tool_call_counts[function_name] = self.tool_call_counts.get(function_name, 0) + 1
                            call_number = self.tool_call_counts[function_name]
                        else:
                            call_number = 1
                        
                        logger.info(f"🔧 Executing tool: {function_name} (call #{call_number})")
                        
                        args_str = json.dumps(function_args)
                        if len(args_str) > 200:
                            logger.info(f"  📥 Args: {args_str[:200]}...")
                        else:
                            logger.info(f"  📥 Args: {args_str}")
                        
                        result, error = self._execute_tool(function_name, function_args)
                        
                        if error:
                            error_preview = str(error).replace('\n', ' ')[:150]
                            logger.info(f"  ❌ Error: {error_preview}")
                        else:
                            if isinstance(result, dict):
                                if result.get('success'):
                                    if 'output' in result and result['output']:
                                        output_preview = str(result['output']).replace('\n', ' ')[:100]
                                        logger.info(f"  ✅ Success: {output_preview}...")
                                    elif 'content' in result:
                                        if result.get('partial_read'):
                                            logger.info(f"  ✅ Success: Read lines {result.get('begin_line', 1)}-{result.get('end_line', 0)} "
                                                      f"({result.get('lines_read', 0)} lines) from {result.get('total_lines', 0)} total")
                                        else:
                                            logger.info(f"  ✅ Success: Read {result.get('lines', 0)} lines, {result.get('size_bytes', 0)} bytes")
                                    elif 'file_path' in result:
                                        logger.info(f"  ✅ Success: File operation on {result['file_path']}")
                                    else:
                                        logger.info(f"  ✅ Success: Operation completed")
                                elif result.get('success') is False:
                                    if result.get('is_binary'):
                                        logger.info(f"  ⚠️ Binary file detected: {result.get('file_path', 'unknown')}")
                                    else:
                                        logger.info(f"  ⚠️ Failed: {result.get('error', 'Unknown error')[:100]}")
                                else:
                                    logger.info(f"  ✅ Success: Operation completed")
                            else:
                                result_preview = str(result).replace('\n', ' ')[:150]
                                logger.info(f"  ✅ Result: {result_preview}")
                        
                        tool_call_record = ToolCall(
                            tool_name=function_name,
                            arguments=function_args,
                            result=result if not error else None,
                            error=error,
                            call_number=call_number
                        )
                        self.tool_calls.append(tool_call_record)
                        
                        tool_content = json.dumps(result)
                        
                        metadata_parts = []
                        if self.config.enable_timestamps:
                            metadata_parts.append(f"[{self._get_timestamp()}]")
                        if self.config.enable_tool_counter:
                            metadata_parts.append(f"[Tool call #{call_number} for '{function_name}']")
                        
                        if metadata_parts:
                            tool_content = " ".join(metadata_parts) + "\n" + tool_content
                        
                        self.conversation_history.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_content
                        })

                    # If the same turn also tagged FINAL ANSWER: (unusual with
                    # tool calls), still stop after recording the tool results.
                    if message.content and "FINAL ANSWER:" in message.content:
                        final_answer = message.content.split("FINAL ANSWER:", 1)[1].strip()
                        logger.info(f"✅ Final answer found alongside tool calls: {final_answer[:100]}...")
                        self._save_trajectory(iteration, final_answer)
                        break
                    
            except Exception as e:
                logger.error(f"Error during event handling: {str(e)}")
                self._save_trajectory(iteration)
                return {
                    "success": False,
                    "error": str(e),
                    "tool_calls": self.tool_calls,
                    "iterations": iteration,
                    "trajectory_file": self.config.trajectory_file if self.config.save_trajectory else None
                }
        
        self._save_trajectory(iteration, final_answer)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"📤 AGENT RESPONSE")
        logger.info(f"{'='*80}")
        if final_answer:
            logger.info(f"Response: {final_answer}")
        else:
            logger.info(f"Response: Task processing completed ({iteration} iterations)")
        logger.info(f"Tool Calls: {len(self.tool_calls)}")
        logger.info(f"{'='*80}\n")
        
        return {
            "final_answer": final_answer,
            "tool_calls": self.tool_calls,
            "todo_list": [
                {
                    "id": item.id,
                    "content": item.content,
                    "status": item.status.value
                }
                for item in self.todo_list
            ],
            "iterations": iteration,
            "success": final_answer is not None,
            "trajectory_file": self.config.trajectory_file if self.config.save_trajectory else None
        }
    
    def reset(self):
        """Reset the agent's state"""
        self.tool_call_counts = {}
        self.tool_calls = []
        self.todo_list = []
        self.next_todo_id = 1
        self.current_directory = os.getcwd()
        self.simulated_time = datetime.now()
        self.last_user_interaction = datetime.now()
        self.background_processes = {}
        self._init_system_prompt()
        logger.info("Agent state reset")
    
    def __del__(self):
        """Cleanup when agent is destroyed"""
        if hasattr(self, 'mcp_manager') and self.mcp_manager.sessions:
            try:
                asyncio.run(self.mcp_manager.disconnect_all())
            except Exception as e:
                logger.warning(f"Error disconnecting MCP servers: {e}")
