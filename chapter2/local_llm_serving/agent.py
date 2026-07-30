"""
vLLM Tool Calling Agent Implementation
Demonstrates how to use vLLM with Qwen3 for tool calling
"""

import json
import uuid
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional, Tuple
from openai import OpenAI
from tools import ToolRegistry
from config import OPENAI_API_BASE, OPENAI_API_KEY, LOG_LEVEL

# Set up logging
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)


class VLLMToolAgent:
    """Agent that uses vLLM for tool calling with Qwen3 model"""
    
    def __init__(self, api_base: str = OPENAI_API_BASE, api_key: str = OPENAI_API_KEY):
        """
        Initialize the agent with vLLM server connection
        
        Args:
            api_base: Base URL for vLLM server
            api_key: API key (not required for vLLM, use "EMPTY")
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url=api_base
        )
        self.tool_registry = ToolRegistry()
        self.conversation_history = []
        logger.info(f"Initialized VLLMToolAgent with server at {api_base}")
    
    def _format_system_prompt_with_tools(self) -> str:
        """
        Format the system prompt with available tools in Qwen3 format
        """
        tools_json = json.dumps(self.tool_registry.get_tool_schemas(), indent=2)
        
        system_prompt = f"""# Tools

You may call one or more functions to assist with the user query.

You are provided with function signatures within <tools></tools> XML tags:
<tools>
{tools_json}
</tools>

For each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:
<tool_call>
{{"name": <function-name>, "arguments": <args-json-object>}}
</tool_call>

You are a helpful assistant that can use tools to answer questions and perform tasks.
When you need to use a tool, generate the appropriate tool call.
After receiving tool results, use them to provide a comprehensive answer to the user."""
        
        return system_prompt
    
    def _parse_tool_calls(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse tool calls from model output
        Extracts content between <tool_call> tags
        """
        tool_calls = []
        
        # Find all tool call blocks
        import re
        pattern = r'<tool_call>(.*?)</tool_call>'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for match in matches:
            try:
                tool_call = json.loads(match.strip())
                if "name" in tool_call and "arguments" in tool_call:
                    tool_calls.append({
                        "id": str(uuid.uuid4())[:8],  # Generate short ID
                        "type": "function",
                        "function": {
                            "name": tool_call["name"],
                            "arguments": tool_call["arguments"]
                        }
                    })
                    logger.debug(f"Parsed tool call: {tool_call['name']}")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse tool call JSON: {e}")
                logger.debug(f"Content was: {match}")
        
        return tool_calls
    
    def _execute_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute tool calls and return results.
        Multiple tool calls in the same turn are executed in parallel (they are
        independent by construction, since the model generated all of them
        without seeing any result). Ensures that error messages from failed
        tool executions are properly formatted.
        """
        def run_one(tool_call: Dict[str, Any]) -> Dict[str, Any]:
            tool_name = tool_call["function"]["name"]
            tool_args = tool_call["function"]["arguments"]
            tool_id = tool_call["id"]
            
            logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
            
            # Execute the tool
            result = self.tool_registry.execute_tool(tool_name, tool_args)
            
            # Check if the result indicates an error
            try:
                result_dict = json.loads(result) if isinstance(result, str) else result
                if isinstance(result_dict, dict) and not result_dict.get("success", True):
                    # Tool execution failed - format error message clearly
                    error_msg = f"❌ Tool '{tool_name}' execution failed:\n"
                    if "error" in result_dict:
                        error_msg += f"Error: {result_dict['error']}\n"
                    if "error_type" in result_dict:
                        error_msg += f"Type: {result_dict['error_type']}\n"
                    if "traceback" in result_dict:
                        error_msg += f"Traceback:\n{result_dict['traceback']}\n"
                    
                    logger.error(f"Tool {tool_name} failed: {result_dict.get('error', 'Unknown error')}")
                    result = error_msg
                else:
                    logger.debug(f"Tool {tool_name} returned: {result}")
            except (json.JSONDecodeError, TypeError):
                # Result is not JSON, just pass it through
                logger.debug(f"Tool {tool_name} returned: {result}")
            
            # Format the result
            return {
                "role": "tool",
                "tool_call_id": tool_id,
                "name": tool_name,
                "content": result if isinstance(result, str) else str(result)
            }
        
        if len(tool_calls) <= 1:
            return [run_one(tc) for tc in tool_calls]
        
        # Independent tool calls run concurrently; executor.map preserves order
        with ThreadPoolExecutor(max_workers=len(tool_calls)) as executor:
            return list(executor.map(run_one, tool_calls))
    
    def _execute_single_tool(self, tool_data: Dict[str, Any]) -> Tuple[str, bool]:
        """
        Execute one parsed tool call ({"name": ..., "arguments": ...}).
        Returns (result_text, is_error) with error messages formatted clearly.
        """
        tool_name = tool_data["name"]
        try:
            result = self.tool_registry.execute_tool(tool_name, tool_data["arguments"])
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return f"❌ Tool execution exception: {str(e)}", True
        
        # Check if the result indicates an error
        try:
            result_dict = json.loads(result) if isinstance(result, str) else result
            if isinstance(result_dict, dict) and not result_dict.get("success", True):
                # Tool execution failed - format error message clearly
                error_msg = f"❌ Tool '{tool_name}' execution failed:\n"
                if "error" in result_dict:
                    error_msg += f"Error: {result_dict['error']}\n"
                if "error_type" in result_dict:
                    error_msg += f"Type: {result_dict['error_type']}\n"
                if "traceback" in result_dict:
                    error_msg += f"Traceback:\n{result_dict['traceback']}\n"
                
                logger.error(f"Tool {tool_name} failed: {result_dict.get('error', 'Unknown error')}")
                return error_msg, True
        except (json.JSONDecodeError, TypeError):
            # Result is not JSON, just pass it through
            pass
        return result, False
    
    def chat(self, message: str, use_tools: bool = True,  
             temperature: float = 0.3, max_tokens: int = 2048, 
             stream: bool = False) -> str:
        """
        Send a message to the model and handle tool calls in a ReAct loop
        
        Args:
            message: User message
            use_tools: Whether to enable tool calling
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            Final response from the model (or generator if streaming)
        """
        if stream:
            return self.chat_stream(message, use_tools, temperature, max_tokens)
        
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": message})
        
        # Prepare messages with system prompt if using tools
        messages = []
        if use_tools:
            messages.append({
                "role": "system",
                "content": self._format_system_prompt_with_tools()
            })
        else:
            messages.append({
                "role": "system",
                "content": "You are a helpful assistant."
            })
        
        # Add conversation history
        messages.extend(self.conversation_history)
        
        # Prepare tools for the API call
        tools = self.tool_registry.get_tool_schemas() if use_tools else None
        
        # ReAct loop - keep going until no more tool calls are needed
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        final_response = ""
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"ReAct iteration {iteration}")
            
            # Prepare messages for this iteration
            messages = []
            if use_tools:
                messages.append({
                    "role": "system",
                    "content": self._format_system_prompt_with_tools()
                })
            else:
                messages.append({
                    "role": "system",
                    "content": "You are a helpful assistant."
                })
            messages.extend(self.conversation_history)
            
            # Call the model
            response = self.client.chat.completions.create(
                model="Qwen/Qwen3-0.6B",
                messages=messages,
                tools=tools,
                tool_choice="auto" if use_tools else None,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            assistant_message = response.choices[0].message
            content = assistant_message.content or ""
            
            # Read tool calls from the structured field. With
            # enable_auto_tool_choice + the hermes parser, vLLM extracts the
            # <tool_call> tags out of the text and returns them here instead of
            # leaving them in `content` (which only holds <think> and final text).
            tool_calls = []
            if use_tools and assistant_message.tool_calls:
                for tc in assistant_message.tool_calls:
                    raw_args = tc.function.arguments
                    try:
                        parsed_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse tool arguments for {tc.function.name}: {e}")
                        parsed_args = {}
                    logger.info(f"Model requested tool call: {tc.function.name}({raw_args})")
                    tool_calls.append({
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": parsed_args,
                        },
                    })
            
            if tool_calls:
                logger.info(f"Model requested {len(tool_calls)} tool call(s)")
                
                # Add assistant message with tool calls to history
                # (arguments must be a JSON string per the OpenAI API spec)
                self.conversation_history.append({
                    "role": "assistant",
                    "content": content,
                    "tool_calls": [
                        {
                            **tc,
                            "function": {
                                **tc["function"],
                                "arguments": tc["function"]["arguments"]
                                if isinstance(tc["function"]["arguments"], str)
                                else json.dumps(tc["function"]["arguments"])
                            }
                        }
                        for tc in tool_calls
                    ]
                })
                
                # Execute tool calls
                tool_results = self._execute_tool_calls(tool_calls)
                
                # Add tool results to conversation
                for result in tool_results:
                    # Format tool response for Qwen3
                    tool_response = f'<tool_response>\n{result["content"]}\n</tool_response>'
                    self.conversation_history.append({
                        "role": "user",  # Tool responses are treated as user messages in Qwen3
                        "content": tool_response,
                        "name": result.get("name", "tool")
                    })
                
                # Continue the ReAct loop
                continue
            else:
                # No tool calls - we have a final response
                self.conversation_history.append({
                    "role": "assistant",
                    "content": content
                })
                final_response = content
                break
        
        # Check if we hit max iterations
        if iteration >= max_iterations:
            logger.warning("Maximum iterations reached in ReAct loop")
            final_response = "I've reached the maximum number of reasoning steps. " + final_response
        
        return final_response
    
    def reset_conversation(self):
        """Reset the conversation history"""
        self.conversation_history = []
        logger.info("Conversation history reset")
    
    def chat_stream(self, message: str, use_tools: bool = True,
                    temperature: float = 0.3, max_tokens: int = 2048):
        """
        Stream a message to the model and handle tool calls in a ReAct loop
        
        Yields chunks that include:
        - type: 'thinking', 'tool_call', 'tool_result', 'content'
        - content: The actual content
        """
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": message})
        
        # Prepare tools for the API call
        tools = self.tool_registry.get_tool_schemas() if use_tools else None
        
        # ReAct loop - keep going until no more tool calls are needed
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"ReAct stream iteration {iteration}")
            
            # Prepare messages for this iteration
            messages = []
            if use_tools:
                messages.append({
                    "role": "system",
                    "content": self._format_system_prompt_with_tools()
                })
            else:
                messages.append({
                    "role": "system",
                    "content": "You are a helpful assistant."
                })
            messages.extend(self.conversation_history)
            
            # Stream response from model
            stream_response = self.client.chat.completions.create(
                model="Qwen/Qwen3-0.6B",
                messages=messages,
                tools=tools,
                tool_choice="auto" if use_tools else None,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            collected_content = []
            thinking_buffer = ""
            tool_call_parts = {}
            
            # Process the stream
            for chunk in stream_response:
                if chunk.choices and chunk.choices[0].delta:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        content_chunk = delta.content
                        collected_content.append(content_chunk)
                        
                        # Check if this is internal thinking (between <think> tags)
                        if '<think>' in content_chunk or thinking_buffer:
                            thinking_buffer += content_chunk
                            if '</think>' in thinking_buffer:
                                # Extract and yield thinking
                                import re
                                thinking_match = re.search(r'<think>(.*?)</think>', thinking_buffer, re.DOTALL)
                                if thinking_match:
                                    # Stream thinking character by character
                                    for char in thinking_match.group(1).strip():
                                        yield {"type": "thinking", "content": char}
                                remaining = re.sub(
                                    r'<think>.*?</think>', '', thinking_buffer, flags=re.DOTALL
                                )
                                thinking_buffer = ""
                                if remaining:
                                    yield {"type": "content", "content": remaining}
                        else:
                            # Regular content
                            yield {"type": "content", "content": content_chunk}

                    # vLLM streams structured tool calls in fragments. Calls
                    # are keyed by index because ids, names, and arguments may
                    # arrive in separate chunks.
                    for fragment in getattr(delta, "tool_calls", None) or []:
                        index = getattr(fragment, "index", None)
                        if index is None:
                            index = 0
                        buffered = tool_call_parts.setdefault(index, {
                            "id": None,
                            "type": "function",
                            "function": {"name": "", "arguments": ""},
                        })
                        if getattr(fragment, "id", None):
                            buffered["id"] = fragment.id
                        if getattr(fragment, "type", None):
                            buffered["type"] = fragment.type
                        function = getattr(fragment, "function", None)
                        if function:
                            if getattr(function, "name", None):
                                buffered["function"]["name"] += function.name
                            if getattr(function, "arguments", None):
                                buffered["function"]["arguments"] += function.arguments

            # Save complete response and structured calls to history before
            # adding tool results, matching the non-streaming message order.
            complete_response = ''.join(collected_content)

            if tool_call_parts:
                pending_tool_calls = []
                parse_errors = []
                assistant_tool_calls = []

                for index in sorted(tool_call_parts):
                    buffered = tool_call_parts[index]
                    call_id = buffered["id"] or str(uuid.uuid4())[:8]
                    tool_name = buffered["function"]["name"] or "unknown"
                    raw_args = buffered["function"]["arguments"] or "{}"
                    assistant_tool_calls.append({
                        "id": call_id,
                        "type": buffered["type"],
                        "function": {
                            "name": tool_name,
                            "arguments": raw_args,
                        },
                    })

                    try:
                        parsed_args = json.loads(raw_args)
                    except json.JSONDecodeError as e:
                        error_msg = f"❌ Tool call parse exception: {str(e)}"
                        logger.error(f"Tool call parse error: {e}")
                        parse_errors.append((tool_name, error_msg))
                        yield {"type": "tool_error", "content": error_msg}
                        continue

                    tool_data = {
                        "id": call_id,
                        "name": tool_name,
                        "arguments": parsed_args,
                    }
                    pending_tool_calls.append(tool_data)
                    yield {
                        "type": "tool_call",
                        "content": {
                            "name": tool_name,
                            "arguments": parsed_args,
                        },
                    }

                self.conversation_history.append({
                    "role": "assistant",
                    "content": complete_response,
                    "tool_calls": assistant_tool_calls,
                })

                for tool_name, error_msg in parse_errors:
                    self.conversation_history.append({
                        "role": "user",
                        "content": f'<tool_response>\n{error_msg}\n</tool_response>',
                        "name": tool_name,
                    })

                # Execute all valid tool calls from this turn in parallel.
                if not pending_tool_calls:
                    outcomes = []
                elif len(pending_tool_calls) == 1:
                    outcomes = [self._execute_single_tool(pending_tool_calls[0])]
                else:
                    with ThreadPoolExecutor(max_workers=len(pending_tool_calls)) as executor:
                        outcomes = list(executor.map(self._execute_single_tool, pending_tool_calls))
                
                for tool_data, (result, is_error) in zip(pending_tool_calls, outcomes):
                    if is_error:
                        yield {"type": "tool_error", "content": result}
                    else:
                        yield {"type": "tool_result", "content": result}
                    
                    # Add to history
                    self.conversation_history.append({
                        "role": "user",
                        "content": f'<tool_response>\n{result}\n</tool_response>',
                        "name": tool_data["name"]
                    })

                # Continue the ReAct loop - let the model decide what to do next
                continue
            else:
                # No tool calls - we have a final response
                self.conversation_history.append({
                    "role": "assistant",
                    "content": complete_response
                })
                # Exit the ReAct loop
                break
        
        # Check if we hit max iterations
        if iteration >= max_iterations:
            yield {"type": "error", "content": "Maximum iterations reached in ReAct loop"}
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the current conversation history"""
        return self.conversation_history
    
    def add_custom_tool(self, name: str, function: callable, 
                       description: str, parameters: Dict):
        """
        Add a custom tool to the registry
        
        Args:
            name: Tool name
            function: Callable function
            description: Tool description
            parameters: OpenAI-style parameter schema
        """
        self.tool_registry.register_tool(name, function, description, parameters)
        logger.info(f"Added custom tool: {name}")


def demonstrate_tool_calling():
    """Demonstrate the tool calling functionality"""
    print("=" * 60)
    print("vLLM Tool Calling Demo with Qwen3")
    print("=" * 60)
    
    # Initialize agent
    agent = VLLMToolAgent()
    
    # Test cases
    test_queries = [
        "What's the current temperature in Paris, France?",
        "Calculate 15 * 23 + sqrt(144)",
        "What time is it in Tokyo (JST)?",
        "Search for information about vLLM tool calling",
        "What's the weather in Dubai and what's 100 fahrenheit in celsius?",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test {i} ---")
        print(f"User: {query}")
        
        response = agent.chat(query)
        print(f"Assistant: {response}")
        
        # Reset conversation for next test
        agent.reset_conversation()
        print("-" * 40)


if __name__ == "__main__":
    # Run demonstration
    demonstrate_tool_calling()
