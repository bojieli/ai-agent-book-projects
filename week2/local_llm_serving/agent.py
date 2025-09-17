"""
vLLM Tool Calling Agent Implementation
Demonstrates how to use vLLM with Qwen3 for tool calling
"""

import json
import uuid
import logging
from typing import List, Dict, Any, Optional
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
        Execute tool calls and return results
        """
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            tool_args = tool_call["function"]["arguments"]
            tool_id = tool_call["id"]
            
            logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
            
            # Execute the tool
            result = self.tool_registry.execute_tool(tool_name, tool_args)
            
            # Format the result
            results.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "name": tool_name,
                "content": result
            })
            
            logger.debug(f"Tool {tool_name} returned: {result}")
        
        return results
    
    def chat(self, message: str, use_tools: bool = True, 
             temperature: float = 0.7, max_tokens: int = 2048, 
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
                model="Qwen3-0.6B",
                messages=messages,
                tools=tools,
                tool_choice="auto" if use_tools else None,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            assistant_message = response.choices[0].message
            content = assistant_message.content or ""
            
            # Check for tool calls in the response
            tool_calls = []
            if use_tools and content:
                tool_calls = self._parse_tool_calls(content)
            
            if tool_calls:
                logger.info(f"Model requested {len(tool_calls)} tool call(s)")
                
                # Add assistant message with tool calls to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": content,
                    "tool_calls": tool_calls
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
                    temperature: float = 0.7, max_tokens: int = 2048):
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
                model="Qwen3-0.6B",
                messages=messages,
                tools=tools,
                tool_choice="auto" if use_tools else None,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            collected_content = []
            tool_calls_buffer = ""
            tool_calls_detected = False
            
            # Process the stream
            for chunk in stream_response:
                if chunk.choices and chunk.choices[0].delta:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        content_chunk = delta.content
                        collected_content.append(content_chunk)
                        
                        # Check if this is internal thinking (between <think> tags)
                        if '<think>' in content_chunk or tool_calls_buffer:
                            tool_calls_buffer += content_chunk
                            if '</think>' in tool_calls_buffer:
                                # Extract and yield thinking
                                import re
                                thinking_match = re.search(r'<think>(.*?)</think>', tool_calls_buffer, re.DOTALL)
                                if thinking_match:
                                    # Stream thinking character by character
                                    for char in thinking_match.group(1).strip():
                                        yield {"type": "thinking", "content": char}
                                tool_calls_buffer = re.sub(r'<think>.*?</think>', '', tool_calls_buffer, flags=re.DOTALL)
                        
                        # Check for tool calls
                        if '<tool_call>' in content_chunk or tool_calls_buffer:
                            tool_calls_buffer += content_chunk
                            if '</tool_call>' in tool_calls_buffer:
                                tool_calls_detected = True
                                # Parse and execute tool call
                                import re
                                tool_match = re.search(r'<tool_call>(.*?)</tool_call>', tool_calls_buffer, re.DOTALL)
                                if tool_match:
                                    try:
                                        tool_data = json.loads(tool_match.group(1).strip())
                                        yield {"type": "tool_call", "content": tool_data}
                                        
                                        # Execute the tool
                                        result = self.tool_registry.execute_tool(
                                            tool_data["name"], 
                                            tool_data["arguments"]
                                        )
                                        yield {"type": "tool_result", "content": result}
                                        
                                        # Add to history
                                        self.conversation_history.append({
                                            "role": "user",
                                            "content": f'<tool_response>\n{result}\n</tool_response>',
                                            "name": tool_data["name"]
                                        })
                                    except Exception as e:
                                        logger.error(f"Tool execution error: {e}")
                                tool_calls_buffer = ""
                        else:
                            # Regular content
                            yield {"type": "content", "content": content_chunk}
            
            # Save complete response to history
            complete_response = ''.join(collected_content)
            
            if tool_calls_detected:
                # Add assistant's message to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": complete_response
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
