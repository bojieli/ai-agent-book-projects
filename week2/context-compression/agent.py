"""
Context Compression Research Agent with Streaming Support
"""

import json
import logging
import time
import sys
from typing import List, Dict, Any, Optional, Generator, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from openai import OpenAI
from config import Config
from web_tools import WebTools
from compression_strategies import (
    CompressionStrategy, 
    ContextCompressor,
    CompressedContent
)

# Configure logging
logging.basicConfig(level=logging.INFO, format=Config.LOG_FORMAT)
logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """Represents a single tool call"""
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Any] = None
    compressed_result: Optional[CompressedContent] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AgentTrajectory:
    """Tracks the agent's execution trajectory"""
    tool_calls: List[ToolCall] = field(default_factory=list)
    total_tokens_used: int = 0
    prompt_tokens_used: int = 0
    completion_tokens_used: int = 0
    context_overflows: int = 0
    compression_strategy: CompressionStrategy = CompressionStrategy.NO_COMPRESSION
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None


class ResearchAgent:
    """
    AI Agent for researching with context compression
    """
    
    def __init__(
        self, 
        api_key: str,
        compression_strategy: CompressionStrategy = CompressionStrategy.NO_COMPRESSION,
        verbose: bool = False,
        enable_streaming: bool = True
    ):
        """
        Initialize the research agent
        
        Args:
            api_key: API key for Moonshot/Kimi
            compression_strategy: Strategy for context compression
            verbose: Enable verbose logging
            enable_streaming: Enable streaming responses
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url=Config.MOONSHOT_BASE_URL
        )
        self.model = Config.MODEL_NAME
        self.compression_strategy = compression_strategy
        self.verbose = verbose
        self.enable_streaming = enable_streaming
        
        # Initialize tools
        self.web_tools = WebTools()
        self.compressor = ContextCompressor(compression_strategy, api_key, enable_streaming)
        
        # Initialize trajectory
        self.trajectory = AgentTrajectory(compression_strategy=compression_strategy)
        
        # Initialize conversation history
        self.conversation_history = []
        self._init_system_prompt()
        
        logger.info(f"Agent initialized with compression strategy: {compression_strategy.value}")
    
    def _init_system_prompt(self):
        """Initialize the system prompt for OpenAI co-founders research"""
        # Get current date dynamically
        from datetime import datetime
        today = datetime.now()
        date_string = today.strftime("%A, %B %d, %Y")
        
        self.conversation_history = [
            {
                "role": "system",
                "content": f"""You are a research assistant tasked with finding information about OpenAI co-founders.

Your task is to:
1. First, search for and identify ALL OpenAI co-founders
2. Then, search for EACH co-founder individually to find their CURRENT affiliations
3. Compile a comprehensive report with current status for each co-founder

Important instructions:
- Be thorough and systematic - search for each person individually
- Focus on CURRENT affiliations, not historical roles
- Include company names, positions, and any recent changes
- If someone left a position, note where they went
- When you have gathered all information, provide a FINAL ANSWER with a complete list

Available tools:
- search_web: Search the web for information
- fetch_webpage: Fetch specific webpage content

Start by searching for the complete list of OpenAI co-founders.

TODAY'S DATE: {date_string}"""
            }
        ]
    
    def _get_tools_description(self) -> List[Dict[str, Any]]:
        """Get tool descriptions for the model"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Search the web for information. Returns multiple search results with content from each webpage.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query"
                            },
                            "num_results": {
                                "type": "integer",
                                "description": "Number of results to return (default: 5)",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "fetch_webpage",
                    "description": "Fetch and extract text content from a specific webpage URL",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL of the webpage to fetch"
                            }
                        },
                        "required": ["url"]
                    }
                }
            }
        ]
    
    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Tuple[Any, Optional[CompressedContent]]:
        """
        Execute a tool and return the result with optional compression
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments for the tool
            
        Returns:
            Tuple of (tool result, compressed content if applicable)
        """
        if tool_name == "search_web":
            result = self.web_tools.search_web(**arguments)
            
            # Apply compression strategy
            query = arguments.get('query', '')
            current_context = self._get_current_context_summary()
            compressed = self.compressor.compress_search_results(
                result, 
                query, 
                current_context
            )
            
            return result, compressed
            
        elif tool_name == "fetch_webpage":
            result = self.web_tools.fetch_webpage(**arguments)
            
            # For fetch, we typically don't compress (used for follow-ups)
            return result, None
            
        else:
            return {"error": f"Unknown tool: {tool_name}"}, None
    
    def _get_current_context_summary(self) -> str:
        """Get a summary of current context for context-aware compression"""
        if not self.trajectory.tool_calls:
            return ""
        
        # Get last few tool calls for context
        recent_calls = self.trajectory.tool_calls[-3:]
        context_parts = []
        
        for call in recent_calls:
            context_parts.append(f"Previous search: {call.arguments.get('query', 'N/A')}")
        
        return " | ".join(context_parts)
    
    def _handle_windowed_compression(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply windowed compression strategy to message history
        Only compresses when context usage exceeds 80% threshold
        
        Args:
            messages: Current message history
            
        Returns:
            Messages with compressed history when needed
        """
        if self.compression_strategy != CompressionStrategy.WINDOWED_CONTEXT:
            return messages
        
        # Check if we should start compressing (80% context usage)
        context_threshold = Config.CONTEXT_WINDOW_SIZE * 0.8
        
        if self.trajectory.prompt_tokens_used <= context_threshold:
            logger.debug(f"Windowed compression: Context usage below threshold ({self.trajectory.prompt_tokens_used:,}/{context_threshold:.0f} tokens)")
            return messages  # No compression needed yet
        
        logger.info(f"⚠️ Context usage exceeds 80% threshold ({self.trajectory.prompt_tokens_used:,}/{Config.CONTEXT_WINDOW_SIZE} tokens) - Starting compression")
        
        # Compression marker to identify already-compressed messages
        COMPRESSION_MARKER = "[COMPRESSED]"
        
        # First, count how many tool messages we have and how many need compression
        tool_messages_to_compress = []
        already_compressed_count = 0
        
        for i, msg in enumerate(messages):
            if msg.get('role') == 'tool':
                original_content = msg.get('content', '')
                if original_content.startswith(COMPRESSION_MARKER):
                    already_compressed_count += 1
                else:
                    tool_messages_to_compress.append((i, msg))
        
        total_tool_messages = already_compressed_count + len(tool_messages_to_compress)
        
        if not tool_messages_to_compress:
            logger.debug(f"Windowed compression: All {total_tool_messages} tool messages already compressed")
            return messages  # All tool messages already compressed
        
        logger.info(f"📊 Compressing {len(tool_messages_to_compress)} uncompressed tool messages (out of {total_tool_messages} total)")
        
        # Build the result with compression for all uncompressed tool messages
        compressed_messages = []
        compressed_in_this_pass = 0
        
        for i, msg in enumerate(messages):
            if msg.get('role') == 'tool':
                original_content = msg.get('content', '')
                
                # Check if already compressed
                if original_content.startswith(COMPRESSION_MARKER):
                    # Already compressed, keep as is
                    compressed_messages.append(msg)
                else:
                    # Compress this tool result
                    compressed_in_this_pass += 1
                    
                    # Find the corresponding tool call to get context
                    tool_call_id = msg.get('tool_call_id')
                    query = "Information search"  # Default
                    
                    # Try to find the query from the tool call
                    for call in self.trajectory.tool_calls:
                        if hasattr(call, 'id') and call.id == tool_call_id:
                            query = call.arguments.get('query', query)
                            break
                    
                    logger.debug(f"Compressing tool message {compressed_in_this_pass}/{len(tool_messages_to_compress)} at index {i} (query: {query[:50]}...)")
                    compressed = self.compressor.compress_for_history(
                        original_content,
                        'search_web',
                        query,
                        preserve_citations=True
                    )
                    logger.debug(f"Compressed: {compressed.original_length:,} → {compressed.compressed_length:,} chars")
                    
                    # Mark as compressed with clear marker
                    compressed_content = (
                        f"{COMPRESSION_MARKER} "
                        f"[Original: {compressed.original_length:,} chars → Compressed: {compressed.compressed_length:,} chars]\n"
                        f"{compressed.content}"
                    )
                    
                    compressed_messages.append({
                        **msg,
                        'content': compressed_content
                    })
            else:
                compressed_messages.append(msg)
        
        logger.info(f"✅ Compressed {compressed_in_this_pass} tool messages in this pass")
        
        return compressed_messages
    
    def _stream_response(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Stream response from the model
        
        Args:
            messages: Conversation messages
            
        Returns:
            Complete message object with token usage
        """
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self._get_tools_description(),
                tool_choice="auto",
                temperature=Config.MODEL_TEMPERATURE,
                max_tokens=Config.MODEL_MAX_TOKENS,
                stream=True,
                stream_options={"include_usage": True}  # Request token usage in stream
            )
            
            collected_chunks = []
            collected_messages = []
            current_tool_calls = []
            usage_data = None
            
            print("\n🤖 Assistant: ", end="", flush=True)
            
            for chunk in stream:
                collected_chunks.append(chunk)
                
                # Capture usage data if present (might be in a chunk without choices)
                if hasattr(chunk, 'usage') and chunk.usage is not None:
                    usage_data = chunk.usage
                
                # Check if chunk has choices before accessing
                if hasattr(chunk, 'choices') and chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    
                    # Handle content
                    if hasattr(delta, 'content') and delta.content:
                        content = delta.content
                        print(content, end="", flush=True)
                        collected_messages.append(content)
                    
                    # Handle tool calls in streaming
                    if hasattr(delta, 'tool_calls') and delta.tool_calls:
                        for tool_call_delta in delta.tool_calls:
                            if tool_call_delta.index is not None:
                                # Ensure we have enough tool calls in the list
                                while len(current_tool_calls) <= tool_call_delta.index:
                                    current_tool_calls.append({
                                        "id": "",
                                        "type": "function",
                                        "function": {"name": "", "arguments": ""}
                                    })
                                
                                if tool_call_delta.id:
                                    current_tool_calls[tool_call_delta.index]["id"] = tool_call_delta.id
                                if tool_call_delta.function:
                                    if tool_call_delta.function.name:
                                        current_tool_calls[tool_call_delta.index]["function"]["name"] = tool_call_delta.function.name
                                    if tool_call_delta.function.arguments:
                                        current_tool_calls[tool_call_delta.index]["function"]["arguments"] += tool_call_delta.function.arguments
            
            print("\n", flush=True)
            
            # Log token usage if available
            if usage_data:
                prompt_tokens = usage_data.prompt_tokens if hasattr(usage_data, 'prompt_tokens') else 0
                completion_tokens = usage_data.completion_tokens if hasattr(usage_data, 'completion_tokens') else 0
                total_tokens = usage_data.total_tokens if hasattr(usage_data, 'total_tokens') else 0
                
                logger.info(f"🔢 Kimi API Token Usage - Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}")
                
                # Update trajectory
                self.trajectory.prompt_tokens_used += prompt_tokens
                self.trajectory.completion_tokens_used += completion_tokens
                self.trajectory.total_tokens_used += total_tokens
            
            # Construct the complete message
            complete_message = {
                "role": "assistant",
                "content": "".join(collected_messages) if collected_messages else None
            }
            
            if current_tool_calls:
                complete_message["tool_calls"] = current_tool_calls
            
            return complete_message
            
        except Exception as e:
            logger.error(f"Error in streaming response: {str(e)}")
            raise
    
    def _non_streaming_response(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get non-streaming response from the model
        
        Args:
            messages: Conversation messages
            
        Returns:
            Complete message object with token usage
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self._get_tools_description(),
            tool_choice="auto",
            temperature=Config.MODEL_TEMPERATURE,
            max_tokens=Config.MODEL_MAX_TOKENS,
            stream=False
        )
        
        message = response.choices[0].message
        
        # Log token usage
        if hasattr(response, 'usage') and response.usage:
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            
            logger.info(f"🔢 Kimi API Token Usage - Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}")
            
            # Update trajectory
            self.trajectory.prompt_tokens_used += prompt_tokens
            self.trajectory.completion_tokens_used += completion_tokens
            self.trajectory.total_tokens_used += total_tokens
        
        # Convert to dict format
        message_dict = {
            "role": "assistant",
            "content": message.content
        }
        
        if hasattr(message, 'tool_calls') and message.tool_calls:
            message_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in message.tool_calls
            ]
        
        # Display the response
        if message.content:
            print(f"\n🤖 Assistant: {message.content}\n")
        
        return message_dict
    
    def execute_research(self, max_iterations: int = 15) -> Dict[str, Any]:
        """
        Execute the research task
        
        Args:
            max_iterations: Maximum number of tool calls
            
        Returns:
            Research results
        """
        # Add initial user message
        self.conversation_history.append({
            "role": "user",
            "content": "Please research and find the current affiliations of all OpenAI co-founders."
        })
        
        messages = self.conversation_history.copy()
        iteration = 0
        final_answer = None
        
        print("\n" + "="*60)
        print(f"Starting research with {self.compression_strategy.value} strategy")
        print("="*60)
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n📍 Iteration {iteration}/{max_iterations}")
            
            try:
                # Apply windowed compression if needed
                if self.compression_strategy == CompressionStrategy.WINDOWED_CONTEXT:
                    messages = self._handle_windowed_compression(messages)
                
                # Display current token usage from trajectory
                print(f"📊 Cumulative Token Usage - Prompt: {self.trajectory.prompt_tokens_used:,}, Completion: {self.trajectory.completion_tokens_used:,}, Total: {self.trajectory.total_tokens_used:,}")
                
                # Check if we're approaching token limit based on actual usage
                if self.trajectory.total_tokens_used > 0:  # Only check after first call
                    # Kimi has a 128k context window
                    if self.trajectory.prompt_tokens_used > Config.CONTEXT_WINDOW_SIZE * 0.8:
                        logger.warning(f"Approaching context limit: {self.trajectory.prompt_tokens_used:,} prompt tokens used")
                        self.trajectory.context_overflows += 1
                        
                        if self.compression_strategy == CompressionStrategy.NO_COMPRESSION:
                            print("\n⚠️ Context overflow detected! This demonstrates the limitation of no compression.")
                            return {
                                "error": f"Context window exceeded - {self.trajectory.prompt_tokens_used:,} tokens used (limit: {Config.CONTEXT_WINDOW_SIZE})",
                                "trajectory": self.trajectory,
                                "iterations": iteration
                            }
                
                # Get response from model
                if self.enable_streaming:
                    message = self._stream_response(messages)
                else:
                    message = self._non_streaming_response(messages)
                
                # Handle tool calls
                if message.get('tool_calls'):
                    messages.append(message)

                    if message.get('content'):
                        print(f"\n🤖 Assistant: {message['content']}")
                    
                    for tool_call in message['tool_calls']:
                        function_name = tool_call['function']['name']
                        function_args = json.loads(tool_call['function']['arguments'])
                        
                        print(f"\n🔧 Executing: {function_name}")
                        print(f"   Args: {function_args}")
                        
                        # Execute the tool
                        result, compressed = self._execute_tool(function_name, function_args)
                        
                        # Record the tool call
                        tool_call_record = ToolCall(
                            tool_name=function_name,
                            arguments=function_args,
                            result=result,
                            compressed_result=compressed
                        )
                        self.trajectory.tool_calls.append(tool_call_record)
                        
                        # Determine what content to add to messages
                        if compressed and self.compression_strategy != CompressionStrategy.NO_COMPRESSION:
                            # Use compressed content
                            tool_content = compressed.content
                            print(f"   ✂️ Compressed: {compressed.original_length:,} → {compressed.compressed_length:,} chars")
                        else:
                            # Use original content (for no compression or last message in windowed)
                            if function_name == "search_web":
                                # Format search results
                                tool_content = json.dumps(result, indent=2)
                            else:
                                tool_content = json.dumps(result)
                        
                        # Add tool result to messages
                        tool_msg = {
                            "role": "tool",
                            "tool_call_id": tool_call['id'],
                            "content": tool_content
                        }
                        messages.append(tool_msg)
                        
                        print(f"   📄 Result size: {len(tool_content):,} characters")
                
                elif message.get('content'):
                    # No tool calls, just content
                    messages.append(message)
                    final_answer = message['content']
                    logger.info("Final answer found")
                    break
                    
            except Exception as e:
                logger.error(f"Error during research: {str(e)}")
                return {
                    "error": str(e),
                    "trajectory": self.trajectory,
                    "iterations": iteration
                }
        
        # Set end time
        self.trajectory.end_time = time.time()
        
        return {
            "final_answer": final_answer,
            "trajectory": self.trajectory,
            "iterations": iteration,
            "success": final_answer is not None,
            "execution_time": self.trajectory.end_time - self.trajectory.start_time
        }
    
    def reset(self):
        """Reset the agent's state"""
        self.trajectory = AgentTrajectory(compression_strategy=self.compression_strategy)
        self._init_system_prompt()
        self.web_tools.clear_cache()
        logger.info("Agent state reset")
