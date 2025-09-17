"""
KV Cache Demonstration Agent with ReAct Pattern
Demonstrates the importance of KV cache through correct and incorrect implementations.
Uses local file system tools to read and search through code files.
"""

import json
import os
import re
import time
import logging
import random
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
from openai import OpenAI
import glob as glob_module
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class KVCacheMode(Enum):
    """Different KV cache optimization modes"""
    CORRECT = "correct"  # Correct implementation with stable context
    DYNAMIC_SYSTEM = "dynamic_system"  # Changing system prompt with timestamp
    SHUFFLED_TOOLS = "shuffled_tools"  # Shuffling tool order each request
    DYNAMIC_PROFILE = "dynamic_profile"  # Changing user profile with credits
    SLIDING_WINDOW = "sliding_window"  # Only keeping recent 5 messages
    TEXT_FORMAT = "text_format"  # Formatting messages as plain text


@dataclass
class ToolCall:
    """Represents a single tool call"""
    name: str
    arguments: Dict[str, Any]
    result: Any = None
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class AgentMetrics:
    """Metrics for agent performance"""
    ttft: float = 0.0  # Time to first token (first iteration)
    ttft_per_iteration: List[float] = field(default_factory=list)  # TTFT for each iteration
    total_time: float = 0.0
    iterations: int = 0
    tool_calls: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_tokens: int = 0


class LocalFileTools:
    """Local implementations of file system tools"""
    
    def __init__(self, root_dir: str = "."):
        self.root_dir = os.path.abspath(root_dir)
        logger.info(f"File tools initialized with root: {self.root_dir}")
    
    def read_file(self, file_path: str, offset: int = 0, size: int = None) -> Dict[str, Any]:
        """
        Read contents of a file
        
        Args:
            file_path: Path to the file relative to root directory
            offset: Line number to start reading from (0-based, default: 0)
            size: Number of lines to read (default: None, read all)
            
        Returns:
            Dictionary with file contents or error
        """
        try:
            full_path = os.path.join(self.root_dir, file_path)
            
            # Security check - ensure path is within root_dir
            real_path = os.path.realpath(full_path)
            if not real_path.startswith(self.root_dir):
                return {
                    "error": f"Access denied: Path outside root directory",
                    "success": False
                }
            
            with open(real_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            
            # Apply offset and size
            if offset < 0:
                offset = 0
            if offset >= total_lines:
                return {
                    "path": file_path,
                    "content": "",
                    "total_lines": total_lines,
                    "lines_read": 0,
                    "offset": offset,
                    "success": True,
                    "message": f"Offset {offset} exceeds file length ({total_lines} lines)"
                }
            
            # Determine end line
            if size is None:
                end = total_lines
            else:
                end = min(offset + size, total_lines)
            
            # Get the requested lines
            selected_lines = lines[offset:end]
            content = ''.join(selected_lines)
            
            # Apply size limit for safety (10KB)
            truncated = False
            if len(content) > 10000:
                content = content[:10000]
                truncated = True
            
            return {
                "path": file_path,
                "content": content,
                "total_lines": total_lines,
                "lines_read": len(selected_lines),
                "offset": offset,
                "end_line": end,
                "truncated": truncated,
                "success": True
            }
        except FileNotFoundError:
            return {
                "error": f"File not found: {file_path}",
                "success": False
            }
        except Exception as e:
            return {
                "error": f"Error reading file: {str(e)}",
                "success": False
            }
    
    def find(self, pattern: str = "*", directory: str = ".") -> Dict[str, Any]:
        """
        Find files matching a pattern (similar to Unix find command)
        
        Args:
            pattern: File name pattern (supports wildcards, default: "*" for all files)
            directory: Directory to search in (relative to root_dir)
            
        Returns:
            Dictionary with list of matching files
        """
        try:
            # Handle directory path properly
            if directory == ".":
                search_dir = self.root_dir
            else:
                # Remove leading/trailing slashes for consistency
                directory = directory.strip('/')
                search_dir = os.path.join(self.root_dir, directory)
            
            # Security check
            real_path = os.path.realpath(search_dir)
            if not real_path.startswith(self.root_dir):
                return {
                    "error": f"Access denied: Path outside root directory",
                    "success": False
                }
            
            # Check if directory exists
            if not os.path.exists(real_path):
                return {
                    "error": f"Directory not found: {directory}",
                    "success": False
                }
            
            # Use glob to find matching files
            matches = []
            for root, dirs, files in os.walk(real_path):
                # Filter hidden directories and __pycache__
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
                
                for file in files:
                    # Skip hidden files and .pyc files
                    if file.startswith('.') or file.endswith('.pyc'):
                        continue
                        
                    if glob_module.fnmatch.fnmatch(file, pattern):
                        # Get path relative to root_dir (not search_dir)
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, self.root_dir)
                        matches.append(rel_path)
            
            # Sort for consistency
            matches.sort()
            
            # Limit results for demonstration
            if len(matches) > 100:
                matches = matches[:100]
                truncated = True
            else:
                truncated = False
            
            return {
                "pattern": pattern,
                "directory": directory,
                "matches": matches,
                "count": len(matches),
                "truncated": truncated,
                "success": True
            }
        except Exception as e:
            return {
                "error": f"Error finding files: {str(e)}",
                "success": False
            }
    
    def grep(self, pattern: str, file_path: str = None, directory: str = None) -> Dict[str, Any]:
        """
        Search for pattern in files (similar to Unix grep command)
        
        Args:
            pattern: Regular expression pattern to search for
            file_path: Single file to search in (optional)
            directory: Directory to search in (optional)
            
        Returns:
            Dictionary with matching lines
        """
        try:
            matches = []
            files_searched = []
            
            if file_path:
                # Search in single file
                full_path = os.path.join(self.root_dir, file_path)
                real_path = os.path.realpath(full_path)
                
                if not real_path.startswith(self.root_dir):
                    return {
                        "error": f"Access denied: Path outside root directory",
                        "success": False
                    }
                
                files_to_search = [file_path]
            elif directory:
                # Search in directory
                search_dir = os.path.join(self.root_dir, directory)
                real_path = os.path.realpath(search_dir)
                
                if not real_path.startswith(self.root_dir):
                    return {
                        "error": f"Access denied: Path outside root directory",
                        "success": False
                    }
                
                # Find all text files in directory
                files_to_search = []
                for root, dirs, files in os.walk(real_path):
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    for file in files:
                        if file.endswith(('.py', '.txt', '.md', '.json', '.yaml', '.yml', '.js', '.ts', '.jsx', '.tsx')):
                            rel_path = os.path.relpath(os.path.join(root, file), self.root_dir)
                            files_to_search.append(rel_path)
                            if len(files_to_search) >= 50:  # Limit files for demonstration
                                break
            else:
                return {
                    "error": "Must specify either file_path or directory",
                    "success": False
                }
            
            # Compile regex pattern
            regex = re.compile(pattern, re.IGNORECASE)
            
            # Search in files
            for file in files_to_search:
                full_path = os.path.join(self.root_dir, file)
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines, 1):
                            if regex.search(line):
                                matches.append({
                                    "file": file,
                                    "line_num": i,
                                    "line": line.strip()[:200]  # Truncate long lines
                                })
                                if len(matches) >= 100:  # Limit matches
                                    break
                    files_searched.append(file)
                except:
                    continue
                
                if len(matches) >= 100:
                    break
            
            return {
                "pattern": pattern,
                "matches": matches,
                "files_searched": len(files_searched),
                "match_count": len(matches),
                "truncated": len(matches) >= 100,
                "success": True
            }
        except Exception as e:
            return {
                "error": f"Error searching: {str(e)}",
                "success": False
            }


class KVCacheAgent:
    """
    ReAct Agent with different KV cache optimization modes
    """
    
    def __init__(self, api_key: str, mode: KVCacheMode = KVCacheMode.CORRECT,
                 model: str = "kimi-k2-0905-preview", root_dir: str = ".",
                 verbose: bool = True):
        """
        Initialize the agent
        
        Args:
            api_key: API key for Moonshot/Kimi
            mode: KV cache optimization mode
            model: Model to use
            root_dir: Root directory for file operations
            verbose: If True, log detailed information
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.moonshot.cn/v1"
        )
        self.model = model
        self.mode = mode
        self.verbose = verbose
        self.tools = LocalFileTools(root_dir)
        
        # Initialize conversation history
        self.conversation_history = []
        self.user_credits = 100  # For dynamic profile mode
        self.metrics = AgentMetrics()
        
        # Tool definitions in OpenAI format
        self.tool_definitions = [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read the contents of a file, optionally specifying a line range",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file relative to root directory"
                            },
                            "offset": {
                                "type": "integer",
                                "description": "Line number to start reading from (0-based, default: 0)",
                                "default": 0
                            },
                            "size": {
                                "type": "integer",
                                "description": "Number of lines to read (default: read all lines)",
                                "default": None
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find",
                    "description": "Find files matching a pattern",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "File name pattern (supports wildcards like *.py)"
                            },
                            "directory": {
                                "type": "string",
                                "description": "Directory to search in (default: current directory)",
                                "default": "."
                            }
                        },
                        "required": ["pattern"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "grep",
                    "description": "Search for a pattern in files",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "Regular expression pattern to search for"
                            },
                            "file_path": {
                                "type": "string",
                                "description": "Single file to search in (optional)"
                            },
                            "directory": {
                                "type": "string",
                                "description": "Directory to search in (optional)"
                            }
                        },
                        "required": ["pattern"]
                    }
                }
            }
        ]
        
        logger.info(f"Agent initialized with mode: {mode.value}, model: {model}")
    
    def _get_system_prompt(self) -> str:
        """Get system prompt based on mode"""
        base_prompt = """You are a helpful AI assistant with access to file system tools.
You can read files, find files by pattern, and search for text within files.
Use the ReAct pattern: Reason about what to do, then Act using tools, and Observe the results.

When asked to analyze or summarize code projects, be thorough:
1. First use 'find' to discover the structure
2. Then read key files to understand the content
3. Use 'grep' to search for specific patterns if needed
4. Once you have gathered sufficient information, provide your response

Always think step by step and use tools to gather information. When you have enough information to answer the user's question, simply provide your response without calling any tools."""
        
        if self.mode == KVCacheMode.DYNAMIC_SYSTEM:
            # Add timestamp to system prompt (breaks KV cache)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            return f"{base_prompt}\n\nCURRENT TIME: {timestamp}"
        
        return base_prompt
    
    def _get_tools(self) -> List[Dict]:
        """Get tool definitions based on mode"""
        tools = self.tool_definitions.copy()
        
        if self.mode == KVCacheMode.SHUFFLED_TOOLS:
            # Shuffle tool order (breaks KV cache)
            random.shuffle(tools)
        
        return tools
    
    def _get_user_profile_message(self) -> Optional[Dict]:
        """Get user profile message for dynamic profile mode"""
        if self.mode == KVCacheMode.DYNAMIC_PROFILE:
            self.user_credits -= 1
            return {
                "role": "user",
                "content": f"[User Profile: Premium user with {self.user_credits} credits remaining]"
            }
        return None
    
    def _format_messages(self, task: str) -> List[Dict]:
        """Format messages based on mode - recreated each iteration for incorrect modes"""
        messages = []
        
        # Add system prompt (changes each time for DYNAMIC_SYSTEM mode)
        messages.append({
            "role": "system",
            "content": self._get_system_prompt()
        })
        
        # Add user profile if in dynamic profile mode (changes each time)
        profile_msg = self._get_user_profile_message()
        if profile_msg:
            messages.append(profile_msg)
        
        if self.mode == KVCacheMode.SLIDING_WINDOW:
            # Preserve all system and user messages, at the most recent 6 messages
            if self.conversation_history:
                # Include all system and user messages, and if there are at least 6 messages, include the last 6 messages regardless of role
                system_user_msgs = [msg for msg in self.conversation_history if msg.get("role") in ("system", "user")]
                messages.extend(system_user_msgs)
                if len(self.conversation_history) >= 6:
                    messages.extend(self.conversation_history[-6:])
        elif self.mode == KVCacheMode.TEXT_FORMAT:
            # Format all history as plain text (breaks KV cache)
            # Reformatting each time breaks structured format
            if self.conversation_history:
                history_text = "Previous conversation:\n"
                for msg in self.conversation_history:
                    role = msg['role'].upper()
                    
                    # Handle different message types
                    if role == "ASSISTANT":
                        # Also include any content
                        if msg.get('content'):
                            history_text += f"{role}: {msg['content']}\n"
                        # Check for tool calls
                        if msg.get('tool_calls'):
                            history_text += f"{role}: [Making tool calls]\n"
                            for tool_call in msg['tool_calls']:
                                func_name = tool_call.get('function', {}).get('name', 'unknown')
                                func_args = tool_call.get('function', {}).get('arguments', '{}')
                                history_text += f"  - Calling {func_name} with args: {func_args}\n"
                    elif role == "TOOL":
                        # Format tool responses
                        tool_content = msg.get('content', '')
                        history_text += f"TOOL RESPONSE: {tool_content}\n"
                    else:
                        # USER, SYSTEM, or other roles
                        content = msg.get('content', '')
                        if content:
                            history_text += f"{role}: {content}\n"
                
                messages.append({
                    "role": "user",
                    "content": history_text
                })
        else:
            # For CORRECT, DYNAMIC_SYSTEM, SHUFFLED_TOOLS, DYNAMIC_PROFILE modes
            # Include full conversation history
            messages.extend(self.conversation_history)
        
        # Add current task (always at the end)
        messages.append({
            "role": "user",
            "content": task
        })
        
        return messages
    
    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool and return the result"""
        tool_map = {
            "read_file": self.tools.read_file,
            "find": self.tools.find,
            "grep": self.tools.grep
        }
        
        if tool_name not in tool_map:
            return {"error": f"Unknown tool: {tool_name}", "success": False}
        
        try:
            # Filter out any unexpected arguments
            tool_func = tool_map[tool_name]
            # Get the expected arguments for this tool
            import inspect
            sig = inspect.signature(tool_func)
            valid_args = {}
            for param_name in sig.parameters:
                if param_name in arguments:
                    valid_args[param_name] = arguments[param_name]
            
            # Log if any arguments were filtered
            filtered = set(arguments.keys()) - set(valid_args.keys())
            if filtered and self.verbose:
                logger.warning(f"Filtered unexpected arguments for {tool_name}: {filtered}")
            
            return tool_func(**valid_args)
        except Exception as e:
            # Return error as tool result instead of raising
            error_msg = f"Tool execution error: {str(e)}"
            logger.error(f"{tool_name} failed: {error_msg}")
            return {"error": error_msg, "success": False}
    
    
    def execute_task(self, task: str, max_iterations: int = 50) -> Dict[str, Any]:
        """
        Execute a task using ReAct pattern with standard OpenAI tool calling
        
        Args:
            task: The task to execute
            max_iterations: Maximum number of iterations
            
        Returns:
            Task execution result with metrics
        """
        start_time = time.time()
        iteration = 0
        final_answer = None
        tool_calls = []
        
        # Store the original task
        original_task = task
        
        while iteration < max_iterations:
            iteration += 1
            
            # CRITICAL: Message handling for KV cache demonstration
            # 
            # CORRECT mode: Build messages once on first iteration, then keep appending
            #   - Maintains stable context → KV cache works efficiently
            # 
            # INCORRECT modes: Recreate entire messages list from history each iteration
            #   - Forces complete context reconstruction → KV cache invalidated
            #   - Within an iteration, we still append to messages for proper API flow
            #   - But at the start of each new iteration, we rebuild from scratch
            
            if self.mode == KVCacheMode.CORRECT:
                # Correct mode: Build messages once, then keep using same list
                if iteration == 1:
                    messages = self._format_messages(original_task)
            else:
                # Incorrect modes: Recreate messages from history each iteration
                # This forces cache invalidation due to context changes
                messages = self._format_messages(original_task)
            
            # Prepare request
            request_data = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            # Add tools for all modes (TEXT_FORMAT still needs tools to work)
            # TEXT_FORMAT only affects how conversation history is formatted, not tool availability
            request_data["tools"] = self._get_tools()
            request_data["tool_choice"] = "auto"
            
            # Make API call
            api_start = time.time()
            try:
                response = self.client.chat.completions.create(**request_data)
                
                # Record TTFT for this iteration
                iteration_ttft = time.time() - api_start
                self.metrics.ttft_per_iteration.append(iteration_ttft)
                
                # Record first iteration TTFT separately for backwards compatibility
                if iteration == 1:
                    self.metrics.ttft = iteration_ttft
                
                # Extract response
                message = response.choices[0].message
                
                # Print assistant content to console (always show, not just verbose)
                if message.content:
                    print(f"\n🤖 Assistant (Iteration {iteration}):")
                    print("-" * 40)
                    print(message.content)
                    print("-" * 40)
                
                # Log token usage and cache information
                if hasattr(response, 'usage'):
                    usage = response.usage
                    self.metrics.prompt_tokens += usage.prompt_tokens
                    self.metrics.completion_tokens += usage.completion_tokens
                    
                    # Check for cached tokens (Kimi specific)
                    # The cached_tokens field appears directly in the usage object
                    cached = 0
                    if hasattr(usage, 'cached_tokens'):
                        # Direct attribute on usage object
                        cached = usage.cached_tokens if usage.cached_tokens is not None else 0
                        self.metrics.cached_tokens += cached
                        if cached > 0:
                            self.metrics.cache_hits += 1
                        else:
                            self.metrics.cache_misses += 1
                    else:
                        # Try alternative locations
                        if hasattr(usage, 'prompt_tokens_details'):
                            details = usage.prompt_tokens_details
                            if details and hasattr(details, 'cached_tokens'):
                                cached = details.cached_tokens if details.cached_tokens is not None else 0
                                self.metrics.cached_tokens += cached
                                if cached > 0:
                                    self.metrics.cache_hits += 1
                                else:
                                    self.metrics.cache_misses += 1
                        
                        # Debug logging when verbose and no cached tokens field found
                        if self.verbose and iteration > 1 and cached == 0:
                            logger.debug(f"Usage object attributes: {dir(usage)}")
                            logger.debug(f"Usage data: {usage}")
                    
                    if self.verbose:
                        # Log with TTFT for this iteration
                        cache_info = f", cached={cached}" if cached > 0 else ""
                        logger.info(f"Iteration {iteration} - TTFT: {iteration_ttft:.3f}s, "
                                  f"Tokens: prompt={usage.prompt_tokens}, "
                                  f"completion={usage.completion_tokens}"
                                  f"{cache_info}")
                
                # Handle tool calls using standard OpenAI format
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    # Add the assistant message with tool calls
                    # Always append to messages for current iteration
                    messages.append(message.model_dump())
                    # Also append to history for next iteration
                    self.conversation_history.append(message.model_dump())
                    
                    for tool_call in message.tool_calls:
                        function_name = tool_call.function.name
                        
                        # Parse arguments safely
                        try:
                            function_args = json.loads(tool_call.function.arguments)
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse tool arguments: {e}")
                            function_args = {}
                            result = {"error": f"Invalid tool arguments: {str(e)}", "success": False}
                        else:
                            if self.verbose:
                                logger.info(f"Executing tool: {function_name} with args: {function_args}")
                            
                            # Execute tool (errors are handled internally and returned as results)
                            result = self._execute_tool(function_name, function_args)
                        
                        # Record tool call
                        tc = ToolCall(name=function_name, arguments=function_args, result=result)
                        tool_calls.append(tc)
                        
                        # Print tool result summary
                        if result.get("success"):
                            # Success - show brief summary
                            if function_name == "read_file":
                                lines_info = f"{result.get('lines_read', 'unknown')} lines"
                                if result.get('offset', 0) > 0 or result.get('size'):
                                    lines_info += f" (lines {result.get('offset', 0)}-{result.get('end_line', '?')})"
                                print(f"    ✓ {function_name}: Read {lines_info}")
                            elif function_name == "find":
                                print(f"    ✓ {function_name}: Found {result.get('count', 0)} files")
                            elif function_name == "grep":
                                print(f"    ✓ {function_name}: Found {result.get('match_count', 0)} matches")
                            else:
                                print(f"    ✓ {function_name}: Success")
                        else:
                            # Error - show the error message
                            print(f"    ✗ {function_name}: {result.get('error', 'Unknown error')}")
                        
                        # Add tool result as proper tool message (including errors)
                        tool_message = {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result)
                        }
                        # Always append to messages for current iteration
                        messages.append(tool_message)
                        # Also append to history for next iteration
                        self.conversation_history.append(tool_message)
                        
                        # Log if tool returned an error
                        if not result.get("success", True):
                            if self.verbose:
                                logger.warning(f"Tool {function_name} returned error: {result.get('error', 'Unknown error')}")
                
                elif message.content:
                    # No tool calls - consider this the final answer
                    final_answer = message.content
                    # Always append to messages for current iteration
                    messages.append(message.model_dump())
                    # Also append to history for next iteration
                    self.conversation_history.append(message.model_dump())
                    if self.verbose:
                        logger.info("No tool calls in response - considering as final answer")
                    break
                
            except Exception as e:
                logger.error(f"Error in iteration {iteration}: {str(e)}")
                break
        
        # Calculate final metrics
        self.metrics.total_time = time.time() - start_time
        self.metrics.iterations = iteration
        self.metrics.tool_calls = len(tool_calls)
        
        return {
            "success": final_answer is not None,
            "final_answer": final_answer,
            "iterations": iteration,
            "tool_calls": tool_calls,
            "metrics": self.metrics,
            "mode": self.mode.value
        }


def compare_implementations(api_key: str, task: str, root_dir: str = ".") -> Dict[str, Any]:
    """
    Compare different KV cache implementations
    
    Args:
        api_key: API key for Kimi
        task: Task to execute
        root_dir: Root directory for file operations
        
    Returns:
        Comparison results
    """
    results = {}
    
    for mode in KVCacheMode:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing mode: {mode.value}")
        logger.info(f"{'='*60}")
        
        agent = KVCacheAgent(api_key=api_key, mode=mode, root_dir=root_dir, verbose=True)
        result = agent.execute_task(task)
        
        results[mode.value] = {
            "success": result["success"],
            "iterations": result["iterations"],
            "tool_calls": result["tool_calls"],
            "metrics": asdict(result["metrics"])
        }
        
        # Log summary
        metrics = result["metrics"]
        logger.info(f"\nMode: {mode.value}")
        logger.info(f"First TTFT: {metrics.ttft:.3f}s")
        
        # Log TTFT progression
        if metrics.ttft_per_iteration:
            ttft_summary = ", ".join([f"{t:.3f}s" for t in metrics.ttft_per_iteration[:5]])
            if len(metrics.ttft_per_iteration) > 5:
                ttft_summary += f"... ({len(metrics.ttft_per_iteration)} total)"
            logger.info(f"TTFT per iteration: [{ttft_summary}]")
            
            # Calculate TTFT improvement from first to last
            if len(metrics.ttft_per_iteration) > 1:
                improvement = (metrics.ttft_per_iteration[0] - metrics.ttft_per_iteration[-1]) / metrics.ttft_per_iteration[0] * 100
                logger.info(f"TTFT improvement: {improvement:.1f}% (first vs last)")
        
        logger.info(f"Total Time: {metrics.total_time:.3f}s")
        logger.info(f"Cached Tokens: {metrics.cached_tokens}")
        logger.info(f"Cache Hits: {metrics.cache_hits}")
        logger.info(f"Cache Misses: {metrics.cache_misses}")
        logger.info(f"Total Tokens: {metrics.prompt_tokens + metrics.completion_tokens}")
    
    return results
