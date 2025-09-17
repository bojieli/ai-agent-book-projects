"""
Ollama Native Tool Calling Implementation
Uses Ollama's standard tool calling API (requires compatible models)
"""

import json
import logging
from typing import List, Dict, Any, Optional
import ollama
from tools import ToolRegistry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OllamaNativeAgent:
    """Agent using Ollama's native tool calling support"""
    
    def __init__(self, model: str = "qwen3:0.6b"):
        """
        Initialize with a model that supports tool calling
        """
        self.model = model
        self.client = ollama.Client()
        self.tool_registry = ToolRegistry()
        self.conversation_history = []
        
        # Check if Ollama is running
        try:
            self.client.list()
            logger.info(f"✅ Connected to Ollama with model: {model}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Ollama: {e}")
            logger.info("Please start Ollama with: ollama serve")
    
    def _convert_tools_to_ollama_format(self) -> List[Dict]:
        """Convert tool registry to Ollama's expected format"""
        tools = []
        for tool_def in self.tool_registry.get_tool_schemas():
            # Ollama expects the same format as OpenAI
            tools.append(tool_def)
        return tools
    
    def chat(self, message: str, use_tools: bool = True, 
             temperature: float = 0.7, stream: bool = False) -> str:
        """
        Send a message using Ollama's native tool calling
        
        Args:
            message: User message
            use_tools: Whether to enable tool calling
            temperature: Sampling temperature
            stream: Whether to stream the response
            
        Returns:
            Final response from the model (or generator if streaming)
        """
        if stream:
            return self.chat_stream(message, use_tools, temperature)
        
        # Original non-streaming implementation continues below...
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        
        # Prepare tools if enabled
        tools = self._convert_tools_to_ollama_format() if use_tools else None
        
        try:
            # Call Ollama with tools
            response = self.client.chat(
                model=self.model,
                messages=self.conversation_history,
                tools=tools,
                options={"temperature": temperature}
            )
            
            # Check if model made tool calls
            message_content = response.get('message', {})
            
            # Handle tool calls if present
            if 'tool_calls' in message_content:
                tool_calls = message_content['tool_calls']
                logger.info(f"Model requested {len(tool_calls)} tool call(s)")
                
                # Add assistant's message with tool calls to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": message_content.get('content', ''),
                    "tool_calls": tool_calls
                })
                
                # Execute each tool call
                for tool_call in tool_calls:
                    function = tool_call.get('function', {})
                    tool_name = function.get('name')
                    tool_args = function.get('arguments')
                    
                    # Parse arguments if they're a string
                    if isinstance(tool_args, str):
                        try:
                            tool_args = json.loads(tool_args)
                        except json.JSONDecodeError:
                            logger.error(f"Failed to parse tool arguments: {tool_args}")
                            tool_args = {}
                    
                    # Execute the tool
                    logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                    result = self.tool_registry.execute_tool(tool_name, tool_args)
                    
                    # Add tool result to conversation
                    self.conversation_history.append({
                        "role": "tool",
                        "content": result
                    })
                
                # Get final response with tool results (still include tools!)
                final_response = self.client.chat(
                    model=self.model,
                    messages=self.conversation_history,
                    tools=tools,  # IMPORTANT: Keep tools available
                    options={"temperature": temperature}
                )
                
                final_content = final_response.get('message', {}).get('content', '')
                
                # Clean response (remove <think> tags if present)
                import re
                final_content = re.sub(r'<think>.*?</think>', '', final_content, flags=re.DOTALL).strip()
                
                # Add final response to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": final_content
                })
                
                return final_content
            
            else:
                # No tool calls, just return the response
                content = message_content.get('content', '')
                self.conversation_history.append({
                    "role": "assistant",
                    "content": content
                })
                return content
                
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return f"Error: {e}"
    
    def chat_stream(self, message: str, use_tools: bool = True,
                    temperature: float = 0.7):
        """
        Stream a message to the model and handle tool calls in a ReAct loop
        
        Yields chunks that include:
        - type: 'thinking', 'tool_call', 'tool_result', 'content'
        - content: The actual content
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        
        # Prepare tools if enabled
        tools = self._convert_tools_to_ollama_format() if use_tools else None
        
        # ReAct loop - keep going until no more tool calls are needed
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            try:
                # Get response from model
                stream_response = self.client.chat(
                    model=self.model,
                    messages=self.conversation_history,
                    tools=tools,
                    options={"temperature": temperature},
                    stream=True
                )
                
                collected_content = []
                tool_calls_detected = False
                thinking_buffer = ""
                in_thinking = False
                
                # Process the stream
                for chunk in stream_response:
                    # Extract message content from chunk
                    message_chunk = chunk.get('message', {})
                    content_chunk = message_chunk.get('content', '')
                    
                    if content_chunk:
                        collected_content.append(content_chunk)
                        
                        # Handle thinking content
                        if '<think>' in content_chunk:
                            in_thinking = True
                            thinking_buffer = content_chunk
                            # Extract any content before <think>
                            import re
                            before_think = content_chunk.split('<think>')[0]
                            if before_think:
                                yield {"type": "content", "content": before_think}
                            # Extract thinking content from this chunk
                            if '</think>' in content_chunk:
                                # Complete thinking in one chunk
                                thinking_match = re.search(r'<think>(.*?)</think>', content_chunk, re.DOTALL)
                                if thinking_match:
                                    thinking_content = thinking_match.group(1).strip()
                                    # Stream thinking content character by character
                                    for char in thinking_content:
                                        yield {"type": "thinking", "content": char}
                                # Check for content after </think>
                                after_think = content_chunk.split('</think>')[-1]
                                if after_think:
                                    yield {"type": "content", "content": after_think}
                                in_thinking = False
                                thinking_buffer = ""
                            else:
                                # Partial thinking, extract what we have so far
                                partial_thinking = content_chunk.split('<think>')[-1]
                                for char in partial_thinking:
                                    yield {"type": "thinking", "content": char}
                        elif in_thinking:
                            thinking_buffer += content_chunk
                            if '</think>' in content_chunk:
                                # End of thinking
                                before_end = content_chunk.split('</think>')[0]
                                for char in before_end:
                                    yield {"type": "thinking", "content": char}
                                # Check for content after </think>
                                after_think = content_chunk.split('</think>')[-1]
                                if after_think:
                                    yield {"type": "content", "content": after_think}
                                in_thinking = False
                                thinking_buffer = ""
                            else:
                                # Continue streaming thinking
                                for char in content_chunk:
                                    yield {"type": "thinking", "content": char}
                        else:
                            # Regular content - yield as-is
                            yield {"type": "content", "content": content_chunk}
                    
                    # Check for tool calls in the chunk
                    if 'tool_calls' in message_chunk:
                        tool_calls = message_chunk['tool_calls']
                        tool_calls_detected = True
                        
                        for tool_call in tool_calls:
                            function = tool_call.get('function', {})
                            tool_name = function.get('name')
                            tool_args = function.get('arguments')
                            
                            # Parse arguments if they're a string
                            if isinstance(tool_args, str):
                                try:
                                    tool_args = json.loads(tool_args)
                                except json.JSONDecodeError:
                                    tool_args = {}
                            
                            # Yield tool call info
                            yield {"type": "tool_call", "content": {"name": tool_name, "arguments": tool_args}}
                            
                            # Execute the tool
                            logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                            result = self.tool_registry.execute_tool(tool_name, tool_args)
                            
                            # Yield tool result
                            yield {"type": "tool_result", "content": result}
                            
                            # Add tool result to conversation
                            self.conversation_history.append({
                                "role": "tool",
                                "content": result
                            })
                
                # Save complete response to history
                complete_response = ''.join(collected_content)
                
                if tool_calls_detected:
                    # Add assistant's message to history
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": complete_response if complete_response else ""
                    })
                    # Continue the ReAct loop - let the model decide what to do next
                    # The loop will continue and get the next response
                else:
                    # No tool calls - we have a final response
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": complete_response
                    })
                    # Exit the ReAct loop
                    break
                    
            except Exception as e:
                logger.error(f"Error in chat stream: {e}")
                yield {"type": "error", "content": str(e)}
                break
        
        # Check if we hit max iterations
        if iteration >= max_iterations:
            yield {"type": "error", "content": "Maximum iterations reached in ReAct loop"}
    
    def reset_conversation(self):
        """Reset the conversation history"""
        self.conversation_history = []
        logger.info("Conversation history reset")


class OllamaOpenAICompatible:
    """Use Ollama through its OpenAI-compatible endpoint"""
    
    def __init__(self, model: str = "qwen3:0.6b", 
                 base_url: str = "http://localhost:11434/v1"):
        """
        Initialize using Ollama's OpenAI-compatible API
        
        This provides better compatibility with tool calling
        """
        from openai import OpenAI
        
        self.model = model
        self.client = OpenAI(
            base_url=base_url,
            api_key="ollama"  # Ollama doesn't need a real key
        )
        self.tool_registry = ToolRegistry()
        self.conversation_history = []
        
        logger.info(f"✅ Initialized Ollama OpenAI-compatible client with {model}")
    
    def chat(self, message: str, use_tools: bool = True,
             temperature: float = 0.7) -> str:
        """
        Chat using OpenAI-compatible endpoint
        """
        # Add user message
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        
        # Prepare tools
        tools = self.tool_registry.get_tool_schemas() if use_tools else None
        
        try:
            # Call with tools
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                tools=tools,
                tool_choice="auto" if tools else None,
                temperature=temperature
            )
            
            assistant_message = response.choices[0].message
            
            # Check for tool calls
            if assistant_message.tool_calls:
                logger.info(f"Model requested {len(assistant_message.tool_calls)} tool(s)")
                
                # Add assistant message to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": assistant_message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in assistant_message.tool_calls
                    ]
                })
                
                # Execute tool calls
                for tool_call in assistant_message.tool_calls:
                    # Parse arguments
                    try:
                        args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        args = {}
                    
                    # Execute tool
                    result = self.tool_registry.execute_tool(
                        tool_call.function.name,
                        args
                    )
                    
                    # Add tool result
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })
                
                # Get final response
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.conversation_history,
                    tools=tools,   # IMPORTANT: Keep tools available
                    temperature=temperature
                )
                
                final_content = final_response.choices[0].message.content
                
                # Add to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": final_content
                })
                
                return final_content
            
            else:
                # No tool calls
                content = assistant_message.content
                self.conversation_history.append({
                    "role": "assistant",
                    "content": content
                })
                return content
                
        except Exception as e:
            logger.error(f"Error: {e}")
            return f"Error: {e}"
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []
        logger.info("Conversation reset")


def test_native_tools():
    """Test Ollama's native tool calling"""
    print("="*60)
    print("🔧 Testing Ollama Native Tool Calling")
    print("="*60)
    
    # Test with default model
    models_to_test = [
        "qwen3:0.6b",  # Default model for this project
    ]
    
    for model_name in models_to_test:
        print(f"\n📦 Testing with {model_name}")
        print("-"*40)
        
        try:
            # Check if model is available
            client = ollama.Client()
            available_models = [m['name'] for m in client.list()['models']]
            
            if not any(model_name in m for m in available_models):
                print(f"⚠️  Model {model_name} not installed")
                print(f"   Install with: ollama pull {model_name}")
                continue
            
            # Test the model
            agent = OllamaNativeAgent(model=model_name)
            
            test_queries = [
                "What's 15 * 23?",
                "What's the weather in London?",
            ]
            
            for query in test_queries:
                print(f"\n👤 User: {query}")
                response = agent.chat(query)
                print(f"🤖 Assistant: {response[:200]}...")  # Truncate long responses
                agent.reset_conversation()
                
        except Exception as e:
            print(f"❌ Error testing {model_name}: {e}")
    
    print("\n" + "="*60)
    print("💡 Note:")
    print("This project uses qwen3:0.6b as the default model.")
    print("Install with: ollama pull qwen3:0.6b")
    print("="*60)


def demo():
    """Interactive demo with proper tool calling"""
    print("="*60)
    print("🎯 Ollama Standard Tool Calling Demo")
    print("="*60)
    
    # Let user choose implementation
    print("\nChoose implementation:")
    print("1. Native Ollama API (recommended)")
    print("2. OpenAI-compatible API")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "2":
        print("\nUsing OpenAI-compatible endpoint...")
        agent = OllamaOpenAICompatible()
    else:
        print("\nUsing native Ollama API...")
        # Check for best available model
        try:
            client = ollama.Client()
            models = [m['name'] for m in client.list()['models']]
            
            # Use qwen3:0.6b as the default model
            model = "qwen3:0.6b"
            
            if model in models:
                print(f"Using recommended model: {model}")
            else:
                print(f"Recommended model {model} not found")
                print("Install with: ollama pull qwen3:0.6b")
                # Fall back to first available model
                model = models[0] if models else "qwen3:0.6b"
                print(f"Using fallback model: {model}")
                
            agent = OllamaNativeAgent(model=model)
            
        except Exception as e:
            print(f"Error: {e}")
            return
    
    # Interactive loop
    print("\n💬 Chat with the assistant (type 'exit' to quit)")
    print("-"*40)
    
    while True:
        user_input = input("\n👤 You: ").strip()
        if user_input.lower() in ['exit', 'quit']:
            break
        
        response = agent.chat(user_input)
        print(f"🤖 Assistant: {response}")
    
    print("\n👋 Goodbye!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_native_tools()
    else:
        demo()
