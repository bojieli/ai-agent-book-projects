"""
System-Hint Enhanced AI Agent
An agent that demonstrates advanced trajectory management with system hints,
including timestamps, tool call tracking, TODO lists, and detailed error messages.
"""

import json
import os
import sys
import subprocess
import platform
import logging
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
    call_number: int = 1  # Track how many times this tool has been called
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_ms: Optional[int] = None


@dataclass
class SystemHintConfig:
    """Configuration for system hints"""
    enable_timestamps: bool = True
    enable_tool_counter: bool = True
    enable_todo_list: bool = True
    enable_detailed_errors: bool = True
    enable_system_state: bool = True  # Current dir, shell, etc.
    timestamp_format: str = "%Y-%m-%d %H:%M:%S"
    simulate_time_delay: bool = False  # For demo purposes
    save_trajectory: bool = True  # Save conversation history to file
    trajectory_file: str = "trajectory.json"  # File to save trajectory to


class SystemHintAgent:
    """
    AI Agent with enhanced system hints for better trajectory management
    """
    
    def __init__(self, api_key: str, provider: str = "kimi", 
                 model: Optional[str] = None, config: Optional[SystemHintConfig] = None,
                 verbose: bool = True):
        """
        Initialize the agent
        
        Args:
            api_key: API key for the LLM provider
            provider: LLM provider ('kimi' for Kimi K2)
            model: Optional model override
            config: System hint configuration
            verbose: If True, log full details
        """
        self.provider = provider.lower()
        self.verbose = verbose
        self.config = config or SystemHintConfig()
        
        # Configure client based on provider
        if self.provider == "kimi" or self.provider == "moonshot":
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.moonshot.cn/v1"
            )
            self.model = model or "kimi-k2-0905-preview"
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        # Initialize tracking
        self.tool_call_counts: Dict[str, int] = {}
        self.tool_calls: List[ToolCall] = []
        self.todo_list: List[TodoItem] = []
        self.next_todo_id = 1
        
        # Initialize conversation history
        self.conversation_history = []
        self.simulated_time = datetime.now()  # For demo time simulation
        self._init_system_prompt()
        
        # Track current working directory
        self.current_directory = os.getcwd()
        
        logger.info(f"System-Hint Agent initialized with provider: {self.provider}, model: {self.model}")
    
    def _init_system_prompt(self):
        """Initialize the system prompt for the conversation"""
        system_content = """You are an intelligent assistant with access to various tools for file operations, code execution, and system commands.

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
        
        return "\n".join(state_info)
    
    def _get_timestamp(self) -> str:
        """Get formatted timestamp"""
        if self.config.simulate_time_delay:
            # For demo: simulate time passing
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
            # Save to file, overwriting each time to capture latest state
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
        tools = [
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
                                "description": "Optional: Line number to start reading from (1-based indexing). E.g., begin_line=10 starts from line 10."
                            },
                            "number_lines": {
                                "type": "integer",
                                "description": "Optional: Number of lines to read from begin_line. E.g., number_lines=50 reads 50 lines."
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
                                "description": "Optional working directory for the command (defaults to current directory)"
                            }
                        },
                        "required": ["command"]
                    }
                }
            }
        ]
        
        # Add TODO management tools if enabled
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
        """
        Execute a tool and return the result with detailed error information
        
        Returns:
            Tuple of (result, error_detail)
        """
        start_time = datetime.now()
        
        try:
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
            
            # Get detailed error information
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
        
        # Add traceback for debugging
        if self.verbose:
            tb = traceback.format_exc()
            error_parts.append(f"Traceback:\n{tb}")
        
        # Add suggestions based on error type
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
    
    # Tool implementations
    def _tool_read_file(self, file_path: str, begin_line: Optional[int] = None, 
                       number_lines: Optional[int] = None) -> Dict[str, Any]:
        """Read file contents with optional line-based reading"""
        try:
            # Resolve path relative to current directory
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.current_directory, file_path)
            
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Check if it's a binary file
            try:
                with open(file_path, 'rb') as f:
                    # Read first 1024 bytes to check for binary content
                    chunk = f.read(1024)
                    # Check for null bytes (common in binary files)
                    if b'\x00' in chunk:
                        return {
                            "success": False,
                            "error": "Cannot read binary file. This tool only supports text files.",
                            "file_path": file_path,
                            "is_binary": True
                        }
                    # Also check if it's valid UTF-8
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
                # If we can't read it as binary, probably permission issue
                raise
            
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as f:
                if begin_line is not None or number_lines is not None:
                    # Line-based reading
                    all_lines = f.readlines()
                    total_lines = len(all_lines)
                    
                    # Calculate line range
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
                    
                    # Get the requested lines
                    selected_lines = all_lines[start_line:end_line]
                    content = ''.join(selected_lines)
                    
                    # Get file info
                    stat = os.stat(file_path)
                    
                    return {
                        "success": True,
                        "file_path": file_path,
                        "content": content,
                        "size_bytes": stat.st_size,
                        "total_lines": total_lines,
                        "begin_line": start_line + 1,  # Convert back to 1-based
                        "end_line": end_line,
                        "lines_read": len(selected_lines),
                        "partial_read": True
                    }
                else:
                    # Full file reading
                    content = f.read()
                    
                    # Get file info
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
            # Resolve path relative to current directory
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.current_directory, file_path)
            
            # Create directory if needed
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
            # Capture output
            import io
            import contextlib
            
            output_buffer = io.StringIO()
            error_buffer = io.StringIO()
            
            with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(error_buffer):
                exec(code)
            
            # Get output
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
            # Use current directory if not specified
            if working_dir is None:
                working_dir = self.current_directory
            elif not os.path.isabs(working_dir):
                working_dir = os.path.join(self.current_directory, working_dir)
            
            # Update current directory if 'cd' command
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
            
            # Execute command
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
        # Keep completed and cancelled items
        kept_items = [
            item for item in self.todo_list
            if item.status in [TodoStatus.COMPLETED, TodoStatus.CANCELLED]
        ]
        
        # Create new pending items
        new_items = []
        for content in items:
            new_items.append(TodoItem(
                id=self.next_todo_id,
                content=content,
                status=TodoStatus.PENDING
            ))
            self.next_todo_id += 1
        
        # Update TODO list
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
    
    def execute_task(self, task: str, max_iterations: int = 20) -> Dict[str, Any]:
        """
        Execute a task using available tools with system hints
        
        Args:
            task: The task to execute
            max_iterations: Maximum number of tool calls
            
        Returns:
            Task execution result
        """
        # Add timestamp to user message if enabled
        if self.config.enable_timestamps:
            timestamp_prefix = f"[{self._get_timestamp()}] "
            task = timestamp_prefix + task
        
        # Add user message
        self.conversation_history.append({"role": "user", "content": task})
        
        iteration = 0
        final_answer = None
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Iteration {iteration}/{max_iterations}")
            
            # Simulate time passing for demo
            self._advance_simulated_time(seconds=5)
            
            # Save trajectory at the start of each iteration
            self._save_trajectory(iteration)
            
            try:
                # Prepare messages for the model - add system hint as last user message
                messages_to_send = self.conversation_history.copy()
                system_hint = self._get_system_hint()
                if system_hint:
                    messages_to_send.append({"role": "user", "content": system_hint})
                
                # Call the model
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages_to_send,
                    tools=self._get_tools_description(),
                    tool_choice="auto",
                    temperature=0.3,
                    max_tokens=8192
                )
                
                message = response.choices[0].message
                
                # Check for final answer
                if message.content and "FINAL ANSWER:" in message.content:
                    final_answer = message.content.split("FINAL ANSWER:")[1].strip()
                    logger.info(f"Final answer found: {final_answer[:100]}...")
                    self.conversation_history.append(message.model_dump())
                    # Save final trajectory
                    self._save_trajectory(iteration, final_answer)
                    break
                
                # Handle tool calls
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    self.conversation_history.append(message.model_dump())
                    
                    for tool_call in message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)
                        
                        # Track tool call count
                        if self.config.enable_tool_counter:
                            self.tool_call_counts[function_name] = self.tool_call_counts.get(function_name, 0) + 1
                            call_number = self.tool_call_counts[function_name]
                        else:
                            call_number = 1
                        
                        logger.info(f"Executing tool: {function_name} (call #{call_number})")
                        
                        # Print tool arguments in a concise format
                        args_str = json.dumps(function_args)
                        if len(args_str) > 200:
                            logger.info(f"  📥 Args: {args_str[:200]}...")
                        else:
                            logger.info(f"  📥 Args: {args_str}")
                        
                        # Execute the tool
                        result, error = self._execute_tool(function_name, function_args)
                        
                        # Print tool result in a concise format
                        if error:
                            error_preview = str(error).replace('\n', ' ')[:150]
                            logger.info(f"  ❌ Error: {error_preview}")
                        else:
                            if isinstance(result, dict):
                                if result.get('success'):
                                    # Show key information for successful operations
                                    if 'output' in result and result['output']:
                                        output_preview = str(result['output']).replace('\n', ' ')[:100]
                                        logger.info(f"  ✅ Success: {output_preview}...")
                                    elif 'content' in result:
                                        # Handle read_file results
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
                                    # Handle explicit failures (like binary file detection)
                                    if result.get('is_binary'):
                                        logger.info(f"  ⚠️ Binary file detected: {result.get('file_path', 'unknown')}")
                                    else:
                                        logger.info(f"  ⚠️ Failed: {result.get('error', 'Unknown error')[:100]}")
                                else:
                                    logger.info(f"  ✅ Success: Operation completed")
                            else:
                                result_preview = str(result).replace('\n', ' ')[:150]
                                logger.info(f"  ✅ Result: {result_preview}")
                        
                        # Record tool call
                        tool_call_record = ToolCall(
                            tool_name=function_name,
                            arguments=function_args,
                            result=result if not error else None,
                            error=error,
                            call_number=call_number
                        )
                        self.tool_calls.append(tool_call_record)
                        
                        # Prepare tool result message
                        tool_content = json.dumps(result)
                        
                        # Add metadata to tool result if enabled
                        metadata_parts = []
                        
                        if self.config.enable_timestamps:
                            metadata_parts.append(f"[{self._get_timestamp()}]")
                        
                        if self.config.enable_tool_counter:
                            metadata_parts.append(f"[Tool call #{call_number} for '{function_name}']")
                        
                        if metadata_parts:
                            tool_content = " ".join(metadata_parts) + "\n" + tool_content
                        
                        # Add tool result
                        self.conversation_history.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_content
                        })
                    
                elif message.content:
                    # Regular assistant message
                    self.conversation_history.append(message.model_dump())
                    
            except Exception as e:
                logger.error(f"Error during task execution: {str(e)}")
                # Save trajectory even on error
                self._save_trajectory(iteration)
                return {
                    "error": str(e),
                    "tool_calls": self.tool_calls,
                    "iterations": iteration,
                    "trajectory_file": self.config.trajectory_file if self.config.save_trajectory else None
                }
        
        # Save final trajectory before returning
        self._save_trajectory(iteration, final_answer)
        
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
        self._init_system_prompt()
        logger.info("Agent state reset")