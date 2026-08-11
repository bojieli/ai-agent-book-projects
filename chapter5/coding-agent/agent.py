"""
Comprehensive Coding Agent - Modular implementation with pure Python tools
All tools implemented without command-line dependencies
"""

import os
import json
from typing import List, Dict, Any, Optional, Iterator
from pathlib import Path
from datetime import datetime
import anthropic
import openai

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from system_state import SystemState
from tool_registry import ToolRegistry


class CodingAgent:
    """Main coding agent with streaming support and modular tool system"""
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-5", base_url: Optional[str] = None, provider: str = "anthropic"):
        """
        Initialize coding agent
        
        Args:
            api_key: API key for the provider
            model: Model identifier
            base_url: Optional base URL for OpenRouter or other providers
            provider: Provider name (anthropic, openai, openrouter)
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.provider = provider.lower()
        self.system_state = SystemState()
        self.tool_registry = ToolRegistry()
        self.messages: List[Dict[str, Any]] = []
        self.tools = self._load_tools()
        self.system_prompt = self._load_system_prompt()
        
        # Initialize client based on provider
        if self.provider == "anthropic":
            # Use Anthropic SDK
            self.client = anthropic.Anthropic(api_key=api_key)
            self.client_type = "anthropic"
        elif self.provider in ["openai", "openrouter"]:
            # Use OpenAI SDK for both OpenAI and OpenRouter
            # OpenRouter uses OpenAI-compatible API format
            if base_url:
                self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
            else:
                self.client = openai.OpenAI(api_key=api_key)
            self.client_type = "openai"
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def _load_tools(self) -> List[Dict[str, Any]]:
        """Load tool definitions from tools.json"""
        tools_file = Path(__file__).parent / "tools.json"
        with open(tools_file, 'r') as f:
            data = json.load(f)
        return data["tools"]
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from system-prompt.md"""
        prompt_file = Path(__file__).parent / "system-prompt.md"
        with open(prompt_file, 'r') as f:
            content = f.read()
        
        # Inject current environment information
        content = content.replace("${Working directory}", self.system_state.current_directory)
        content = content.replace("${current_branch}", self._get_git_branch())
        content = content.replace("${main_branch}", self._get_main_branch())
        content = content.replace("${git status}", self._get_git_status())
        content = content.replace("${Last 5 Recent commits}", self._get_recent_commits())
        
        return content
    
    def _get_git_branch(self) -> str:
        """Get current git branch"""
        try:
            import subprocess
            return subprocess.getoutput("git branch --show-current") or "unknown"
        except Exception:
            return "unknown"
    
    def _get_main_branch(self) -> str:
        """Get main branch name"""
        try:
            import subprocess
            branches = subprocess.getoutput("git branch -a")
            if "main" in branches:
                return "main"
            elif "master" in branches:
                return "master"
            return "main"
        except Exception:
            return "main"
    
    def _get_git_status(self) -> str:
        """Get git status"""
        try:
            import subprocess
            return subprocess.getoutput("git status --short") or "No changes"
        except Exception:
            return "Not a git repository"
    
    def _get_recent_commits(self) -> str:
        """Get recent commits"""
        try:
            import subprocess
            return subprocess.getoutput("git log --oneline -5") or "No commits"
        except Exception:
            return "Not a git repository"
    
    def run(self, user_message: str, max_iterations: int = 50) -> Iterator[Dict[str, Any]]:
        """
        Run agent with streaming output
        
        Args:
            user_message: User's input message
            max_iterations: Maximum number of agent iterations
            
        Yields:
            Streaming events with type and content
        """
        # Add user message with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.messages.append({
            "role": "user",
            "content": f"[{timestamp}] {user_message}"
        })
        
        yield {"type": "user_message", "content": user_message, "timestamp": timestamp}
        
        for iteration in range(max_iterations):
            yield {"type": "iteration_start", "iteration": iteration + 1}
            
            # Prepare messages with system hint
            messages_with_hint = self.messages.copy()
            
            # Add system hint as a user message at the end
            system_hint = self.system_state.get_system_hint()
            messages_with_hint.append({
                "role": "user",
                "content": f"<system_hint>\n{system_hint}\n</system_hint>"
            })
            
            # Call API based on client type
            try:
                if self.client_type == "anthropic":
                    # Use Anthropic streaming
                    iteration_generator = self._run_anthropic_iteration(messages_with_hint, iteration)
                else:
                    # Use OpenAI/OpenRouter streaming
                    iteration_generator = self._run_openai_iteration(messages_with_hint, iteration)
                
                should_break = False
                for event in iteration_generator:
                    yield event
                    if event.get("type") == "done":
                        should_break = True
                
                if should_break:
                    break

            except Exception as e:
                yield {"type": "error", "error": str(e)}
                break
        
        else:
            # Reached max iterations
            yield {"type": "max_iterations_reached", "max_iterations": max_iterations}
    
    def _run_anthropic_iteration(self, messages_with_hint: List[Dict[str, Any]], iteration: int) -> Iterator[Dict[str, Any]]:
        """Run one iteration with Anthropic API"""
        try:
            with self.client.messages.stream(
                model=self.model,
                system=self.system_prompt,
                messages=messages_with_hint,
                tools=self.tools
            ) as stream:
                assistant_message = {"role": "assistant", "content": []}
                current_text = ""
                current_tool_use = None
                current_tool_json = ""

                for event in stream:
                    if event.type == "content_block_start":
                        if event.content_block.type == "text":
                            current_text = ""
                        elif event.content_block.type == "tool_use":
                            current_tool_use = {
                                "type": "tool_use",
                                "id": event.content_block.id,
                                "name": event.content_block.name,
                                "input": {}
                            }
                            current_tool_json = ""

                    elif event.type == "content_block_delta":
                        if event.delta.type == "text_delta":
                            current_text += event.delta.text
                            yield {
                                "type": "text_delta",
                                "delta": event.delta.text,
                                "accumulated": current_text
                            }
                        elif event.delta.type == "input_json_delta":
                            # Accumulate tool input; partial_json is a fragment,
                            # only the concatenation of all fragments parses.
                            if current_tool_use:
                                current_tool_json += event.delta.partial_json

                    elif event.type == "content_block_stop":
                        if current_text:
                            assistant_message["content"].append({
                                "type": "text",
                                "text": current_text
                            })
                            current_text = ""
                        elif current_tool_use:
                            try:
                                current_tool_use["input"] = json.loads(
                                    current_tool_json or "{}"
                                )
                            except json.JSONDecodeError:
                                pass
                            assistant_message["content"].append(current_tool_use)
                            yield {
                                "type": "tool_call",
                                "tool": current_tool_use["name"],
                                "input": current_tool_use["input"]
                            }
                            current_tool_use = None
                
                # Add assistant message to history
                self.messages.append(assistant_message)
                
                # Check if we have tool calls to execute
                tool_calls = [
                    block for block in assistant_message["content"]
                    if block.get("type") == "tool_use"
                ]
                
                if not tool_calls:
                    # No tool calls, agent is done
                    yield {"type": "done", "final_message": assistant_message}
                    return
                
                # Execute tool calls
                tool_results = []
                for tool_call in tool_calls:
                    tool_name = tool_call["name"]
                    tool_input = tool_call["input"]
                    
                    yield {
                        "type": "tool_execution_start",
                        "tool": tool_name,
                        "input": tool_input
                    }
                    
                    # Get tool instance and execute
                    try:
                        tool = self.tool_registry.get_tool(tool_name, self.system_state)
                        result = tool.execute(tool_input)
                        result_dict = result.to_dict()
                    except Exception as e:
                        result_dict = {
                            "error": str(e),
                            "tool": tool_name
                        }
                    
                    yield {
                        "type": "tool_execution_complete",
                        "tool": tool_name,
                        "result": result_dict
                    }
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call["id"],
                        "content": json.dumps(result_dict, ensure_ascii=False)
                    })
                
                # Add tool results to messages
                self.messages.append({
                    "role": "user",
                    "content": tool_results
                })
                
                yield {"type": "iteration_end", "iteration": iteration + 1}
                
        except Exception as e:
            raise e
    
    def _run_openai_iteration(self, messages_with_hint: List[Dict[str, Any]], iteration: int) -> Iterator[Dict[str, Any]]:
        """Run one iteration with OpenAI/OpenRouter API"""
        try:
            # Convert messages to OpenAI format
            openai_messages = self._convert_to_openai_format(messages_with_hint)
            
            # Convert tools to OpenAI format
            openai_tools = self._convert_tools_to_openai_format()
            
            # Stream completion
            params = {
                "model": self.model,
                "messages": openai_messages,
                "tools": openai_tools,
                "stream": True,
            }
            stream = self.client.chat.completions.create(**params)
            
            assistant_message = {"role": "assistant", "content": ""}
            tool_calls_data = {}
            current_text = ""
            
            for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if not delta:
                    continue
                
                # Handle text content
                if delta.content:
                    current_text += delta.content
                    yield {
                        "type": "text_delta",
                        "delta": delta.content,
                        "accumulated": current_text
                    }
                
                # Handle tool calls
                if delta.tool_calls:
                    for tool_call in delta.tool_calls:
                        idx = tool_call.index
                        if idx not in tool_calls_data:
                            tool_calls_data[idx] = {
                                "id": tool_call.id or "",
                                "name": "",
                                "arguments": ""
                            }
                        
                        if tool_call.function.name:
                            tool_calls_data[idx]["name"] = tool_call.function.name
                        if tool_call.function.arguments:
                            tool_calls_data[idx]["arguments"] += tool_call.function.arguments
            
            # Store assistant message
            assistant_message["content"] = current_text
            if tool_calls_data:
                assistant_message["tool_calls"] = list(tool_calls_data.values())
            
            self.messages.append(assistant_message)
            
            # Check if we have tool calls
            if not tool_calls_data:
                yield {"type": "done", "final_message": assistant_message}
                return
            
            # Execute tool calls
            tool_results = []
            for tool_call in tool_calls_data.values():
                tool_name = tool_call["name"]
                
                try:
                    tool_input = json.loads(tool_call["arguments"])
                except (json.JSONDecodeError, TypeError):
                    tool_input = {}
                
                yield {
                    "type": "tool_call",
                    "tool": tool_name,
                    "input": tool_input
                }
                
                yield {
                    "type": "tool_execution_start",
                    "tool": tool_name,
                    "input": tool_input
                }
                
                # Execute tool
                try:
                    tool = self.tool_registry.get_tool(tool_name, self.system_state)
                    result = tool.execute(tool_input)
                    result_dict = result.to_dict()
                except Exception as e:
                    result_dict = {
                        "error": str(e),
                        "tool": tool_name
                    }
                
                yield {
                    "type": "tool_execution_complete",
                    "tool": tool_name,
                    "result": result_dict
                }
                
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(result_dict, ensure_ascii=False)
                })
            
            # Add tool results to messages
            self.messages.extend(tool_results)
            
            yield {"type": "iteration_end", "iteration": iteration + 1}
            
        except Exception as e:
            raise e
    
    def _convert_to_openai_format(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert Anthropic message format to OpenAI format"""
        openai_messages = []
        
        # Add system message
        openai_messages.append({
            "role": "system",
            "content": self.system_prompt
        })
        
        for msg in messages:
            role = msg["role"]
            content = msg.get("content", "")
            
            if role == "user":
                if isinstance(content, str):
                    openai_messages.append({"role": "user", "content": content})
                elif isinstance(content, list):
                    # Handle tool results
                    for item in content:
                        if item.get("type") == "tool_result":
                            openai_messages.append({
                                "role": "tool",
                                "tool_call_id": item.get("tool_use_id", ""),
                                "content": item.get("content", "")
                            })
            
            elif role == "assistant":
                msg_dict = {"role": "assistant", "content": content}
                if "tool_calls" in msg and msg["tool_calls"]:
                    msg_dict["tool_calls"] = [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["name"],
                                "arguments": tc["arguments"]
                            }
                        } for tc in msg["tool_calls"]
                    ]
                openai_messages.append(msg_dict)

            elif role == "tool":
                # 保留 tool 消息
                openai_messages.append({
                    "role": "tool",
                    "tool_call_id": msg.get("tool_call_id", ""),
                    "content": content
                })
        
        return openai_messages
    
    def _convert_tools_to_openai_format(self) -> List[Dict[str, Any]]:
        """Convert Anthropic tool format to OpenAI format"""
        openai_tools = []
        
        for tool in self.tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"]
                }
            })
        
        return openai_tools
    
    def reset(self):
        """Reset agent state"""
        self.messages = []
        self.system_state = SystemState()


def main():
    """Example usage"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        return
    
    agent = CodingAgent(api_key=api_key)
    
    user_query = "List all Python files in the current directory using the Glob tool"
    
    print(f"User: {user_query}\n")
    
    for event in agent.run(user_query):
        if event["type"] == "text_delta":
            print(event["delta"], end="", flush=True)
        elif event["type"] == "tool_call":
            print(f"\n[Calling tool: {event['tool']}]")
        elif event["type"] == "tool_execution_complete":
            print(f"[Tool completed]")
        elif event["type"] == "done":
            print("\n\nAgent completed successfully!")
        elif event["type"] == "error":
            print(f"\n\nError: {event['error']}")


if __name__ == "__main__":
    main()
