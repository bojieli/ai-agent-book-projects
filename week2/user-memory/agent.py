"""
User Memory Agent with Kimi K2 and React pattern
Following the system-hint project's tool-based approach
"""

import json
import os
import sys
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from openai import OpenAI
from config import Config, MemoryMode
from memory_manager import create_memory_manager, BaseMemoryManager
from conversation_history import ConversationHistory, ConversationTurn

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """Represents a single tool call with tracking"""
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class UserMemoryConfig:
    """Configuration for the user memory agent"""
    enable_memory_updates: bool = True
    enable_conversation_history: bool = True
    enable_memory_search: bool = True
    memory_mode: MemoryMode = MemoryMode.NOTES
    max_memory_context: int = 10  # Max memory items to include in context
    save_trajectory: bool = True
    trajectory_file: str = "memory_trajectory.json"


class UserMemoryAgent:
    """
    User Memory Agent with tool-based React pattern
    """
    
    def __init__(self, 
                 user_id: str,
                 api_key: Optional[str] = None,
                 provider: Optional[str] = None,
                 model: Optional[str] = None,
                 config: Optional[UserMemoryConfig] = None,
                 verbose: bool = True):
        """
        Initialize the agent
        
        Args:
            user_id: Unique user identifier
            api_key: API key (defaults to env based on provider)
            provider: LLM provider ('siliconflow', 'doubao', 'kimi', 'moonshot')
            model: Model name (defaults to provider's default)
            config: Agent configuration
            verbose: Enable verbose logging
        """
        self.user_id = user_id
        self.verbose = verbose
        self.config = config or UserMemoryConfig()
        
        # Determine provider
        self.provider = (provider or Config.PROVIDER).lower()
        
        # Get API key for provider
        api_key = api_key or Config.get_api_key(self.provider)
        if not api_key:
            raise ValueError(f"API key required for provider '{self.provider}'. Check environment variables.")
        
        # Configure client based on provider
        if self.provider == "siliconflow":
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
            self.model = model or "kimi-k2-0905-preview"
        elif self.provider == "openrouter":
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
            # Default to Gemini 2.5 Pro, but allow any of the supported models
            self.model = model or "google/gemini-2.5-pro"
            # Supported models: google/gemini-2.5-pro, openai/gpt-5, anthropic/claude-sonnet-4
        else:
            raise ValueError(f"Unsupported provider: {self.provider}. Use 'siliconflow', 'doubao', 'kimi', 'moonshot', or 'openrouter'")
        
        # Initialize memory manager
        self.memory_manager = create_memory_manager(user_id, self.config.memory_mode)
        
        # Initialize conversation history
        self.conversation_history = ConversationHistory(user_id) if self.config.enable_conversation_history else None
        
        # Track tool calls
        self.tool_calls: List[ToolCall] = []
        self.tool_call_counts: Dict[str, int] = {}
        
        # Initialize conversation
        self.conversation = []
        self.session_id = self._start_session()
        
        # Initialize system prompt
        self._init_system_prompt()
        
        logger.info(f"UserMemoryAgent initialized for user {user_id} with {self.provider} provider using {self.model}")
    
    def _start_session(self) -> str:
        """Start a new session"""
        return f"session-{uuid.uuid4().hex[:8]}"
    
    def _init_system_prompt(self):
        """Initialize the system prompt with memory context based on memory mode"""
        
        base_prompt = """You are an intelligent assistant with persistent memory across conversations. 
You have access to various tools to manage user memories and search conversation history. If you want to add, update, or delete multiple memories, you should use multiple tool calls at once. After you have finished updating memories, you should output STOP without any other text.

The full history of the latest conversation is automatically loaded in the context below.

## Key Behaviors:
1. All user memories are automatically loaded and shown in the "USER MEMORIES" section below
2. Proactively update memories when learning new information about the user
3. Reference relevant memories when responding
4. Maintain consistency with previously stored information
5. Be personalized based on what you know about the user

"""
        
        # Add mode-specific memory instructions
        if self.config.memory_mode == MemoryMode.NOTES:
            memory_instructions = """## Memory Management:
- All user memories are pre-loaded in the context below
- Use `add_memory` to store new important information about the user
- Use `update_memory` to modify existing memories
- Use `delete_memory` to remove outdated or incorrect memories

Keep memories as simple facts or preferences."""
        
        elif self.config.memory_mode == MemoryMode.ENHANCED_NOTES:
            memory_instructions = """## Memory Management:
- All user memories are pre-loaded in the context below
- Use `add_memory` to store new important information about the user
- Use `update_memory` to modify existing memories
- Use `delete_memory` to remove outdated or incorrect memories

IMPORTANT: Each note should contain all important factual information and user preferences in a complete, contextual manner.
Notes can be full paragraphs that capture the complete context, not just simple key-value pairs.

Example of good enhanced notes:
- "User works at TechCorp as a senior software engineer, specializing in machine learning. They've been there for 3 years and enjoy the collaborative culture."
- "User's email is john.doe@techcorp.com for work and johndoe.personal@gmail.com for personal matters. They prefer work emails during business hours only."
- "User has two children: Sarah (8 years old, loves soccer) and Michael (5 years old, interested in dinosaurs). Both attend Oakwood Elementary School."

Extract all factual information from the conversation that may be useful for future interactions."""

        elif self.config.memory_mode == MemoryMode.JSON_CARDS:
            memory_instructions = """## Memory Management:
- All user memories are pre-loaded in the context below
- Use `add_memory` to store new memory cards with structured data
- Use `update_memory` to modify existing memory cards
- Use `delete_memory` to remove outdated memory cards

Memory cards use a hierarchical structure: category -> subcategory -> key -> value

Example operations:
1. Adding a memory card:
   content: {"category": "personal", "subcategory": "contact", "key": "email", "value": "user@example.com"}

2. Updating a memory card:
   memory_id: "personal.contact.email"
   content: {"value": "newemail@example.com"}

3. Structure examples:
   - personal.preferences.coding_style -> "prefers functional programming"
   - work.projects.current -> "developing AI chatbot"
   - family.children.sarah -> {"age": 8, "interests": ["soccer", "reading"]}"""

        elif self.config.memory_mode == MemoryMode.ADVANCED_JSON_CARDS:
            memory_instructions = """## Memory Management:
- All user memory cards are pre-loaded in the context below
- Use `add_memory` to store complete memory card objects
- Use `update_memory` to modify existing memory cards
- Use `delete_memory` to remove memory cards

Memory cards are complete JSON objects within categories. Each card MUST include:
- backstory: Context about when/why this information was learned (1-2 sentences)
- date_created: Current timestamp (YYYY-MM-DD HH:MM:SS)
- person: Who this relates to (e.g., "John Smith (primary)", "Sarah Smith (daughter)")
- relationship: Role/relationship (e.g., "primary account holder", "family member")
- Additional relevant fields based on the information type

Example memory card operations:

1. Adding a complete memory card:
content: {
    "category": "financial",
    "card_key": "bank_account_primary",
    "card": {
        "backstory": "User shared their banking details while setting up automatic bill payments",
        "date_created": "2024-01-15 10:30:00",
        "person": "John Smith (primary)",
        "relationship": "primary account holder",
        "bank_name": "Chase Bank",
        "account_type": "checking",
        "account_ending": "4567",
        "routing_number": "021000021",
        "purpose": "primary checking for bills"
    }
}

2. Adding a medical memory card:
content: {
    "category": "medical",
    "card_key": "doctor_dermatologist_sarah",
    "card": {
        "backstory": "User needed to schedule a dermatology appointment for their daughter's skin condition",
        "date_created": "2024-01-16 14:00:00",
        "person": "Sarah Smith (daughter)",
        "relationship": "family member",
        "doctor_name": "Dr. Emily Johnson",
        "specialty": "Pediatric Dermatology",
        "clinic": "Children's Health Center",
        "phone": "555-0123",
        "condition_treated": "eczema"
    }
}

CRITICAL: The backstory and person fields prevent confusion. For example, without proper person identification, 
a dermatologist for a child might be mistakenly suggested for an elderly parent's Alzheimer's care."""

        else:
            memory_instructions = """## Memory Management:
- All user memories are pre-loaded in the context below
- Use `add_memory` to store new important information about the user
- Use `update_memory` to modify existing memories
- Use `delete_memory` to remove outdated or incorrect memories"""
        
        system_content = base_prompt + memory_instructions + """

Current Memory Context will be provided with each message."""

        self.conversation = [
            {
                "role": "system",
                "content": system_content
            }
        ]
    
    def _get_memory_context(self) -> str:
        """Get current memory context as a string"""
        context_parts = []
        
        # Add memory summary
        context_parts.append("=== USER MEMORIES ===")
        context_parts.append(self.memory_manager.get_context_string())
        context_parts.append("")
        
        # Add ALL conversation history if available
        if self.conversation_history and self.config.enable_conversation_history:
            # Get ALL conversation history, not just recent
            all_conversations = self.conversation_history.conversations if hasattr(self.conversation_history, 'conversations') else []
            
            if all_conversations:
                context_parts.append("=== FULL CONVERSATION HISTORY ===")
                context_parts.append(f"Total conversations: {len(all_conversations)}")
                context_parts.append("")
                
                for turn in all_conversations:
                    context_parts.append(f"[Session: {turn.session_id}, Turn {turn.turn_number}]")
                    context_parts.append(f"User: {turn.user_message}")
                    context_parts.append(f"Assistant: {turn.assistant_message}")
                    context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _get_tools_description(self) -> List[Dict[str, Any]]:
        """Get tool descriptions for the model"""
        tools = []
        
        # Memory management tools
        if self.config.enable_memory_updates:
            tools.extend([
                {
                    "type": "function",
                    "function": {
                        "name": "add_memory",
                        "description": "Add a new memory about the user",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "content": {
                                    "type": "string",
                                    "description": "The memory content to store"
                                },
                                "tags": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Optional tags for categorizing the memory"
                                }
                            },
                            "required": ["content"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "update_memory",
                        "description": "Update an existing memory",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "memory_id": {
                                    "type": "string",
                                    "description": "ID of the memory to update"
                                },
                                "content": {
                                    "type": "string",
                                    "description": "New content for the memory"
                                },
                                "tags": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Optional new tags"
                                }
                            },
                            "required": ["memory_id", "content"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "delete_memory",
                        "description": "Delete a memory",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "memory_id": {
                                    "type": "string",
                                    "description": "ID of the memory to delete"
                                }
                            },
                            "required": ["memory_id"]
                        }
                    }
                }
            ])
        
        return tools
    
    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Tuple[Any, Optional[str]]:
        """
        Execute a tool and return the result
        
        Returns:
            Tuple of (result, error_message)
        """
        try:
            if tool_name == "add_memory":
                result = self._tool_add_memory(**arguments)
            elif tool_name == "update_memory":
                result = self._tool_update_memory(**arguments)
            elif tool_name == "delete_memory":
                result = self._tool_delete_memory(**arguments)
            else:
                error = f"Unknown tool: {tool_name}"
                return {"error": error}, error
            
            return result, None
            
        except Exception as e:
            error_msg = f"Tool '{tool_name}' failed: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}, error_msg
    
    # Tool implementations
    def _tool_add_memory(self, content: Any, tags: List[str] = None) -> Dict[str, Any]:
        """Add a new memory"""
        if self.config.memory_mode in [MemoryMode.NOTES, MemoryMode.ENHANCED_NOTES]:
            # Both basic and enhanced notes use the same storage, just different prompts
            if isinstance(content, dict):
                # If content is a dict, extract string representation
                content_str = str(content)
            else:
                content_str = content
            
            memory_id = self.memory_manager.add_memory(
                content=content_str,
                session_id=self.session_id,
                tags=tags or []
            )
            
        elif self.config.memory_mode == MemoryMode.JSON_CARDS:
            # Basic JSON cards mode
            if isinstance(content, dict):
                # Content should already have the structure
                memory_content = content
            else:
                # Parse content to extract structure
                parts = str(content).split(':')
                if len(parts) >= 2:
                    category = "personal"
                    subcategory = "info"
                    key = parts[0].strip().replace(' ', '_').lower()
                    value = ':'.join(parts[1:]).strip()
                else:
                    category = "general"
                    subcategory = "notes"
                    key = f"note_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    value = content
                
                memory_content = {
                    'category': category,
                    'subcategory': subcategory,
                    'key': key,
                    'value': value
                }
            
            memory_id = self.memory_manager.add_memory(
                content=memory_content,
                session_id=self.session_id
            )
            
        elif self.config.memory_mode == MemoryMode.ADVANCED_JSON_CARDS:
            # Advanced JSON cards mode
            if not isinstance(content, dict):
                try:
                    content = json.loads(content)
                except:
                    return {
                        "success": False,
                        "message": "Advanced JSON cards mode requires properly structured JSON content"
                    }
            
            memory_id = self.memory_manager.add_memory(
                content=content,
                session_id=self.session_id
            )
        else:
            return {
                "success": False,
                "message": f"Unknown memory mode: {self.config.memory_mode}"
            }
        
        return {
            "success": True,
            "memory_id": memory_id,
            "message": f"Memory added successfully"
        }
    
    def _tool_update_memory(self, memory_id: str, content: Any, tags: List[str] = None) -> Dict[str, Any]:
        """Update an existing memory"""
        if self.config.memory_mode in [MemoryMode.NOTES, MemoryMode.ENHANCED_NOTES]:
            # Both basic and enhanced notes use the same storage
            if isinstance(content, dict):
                content_str = str(content)
            else:
                content_str = content
            
            success = self.memory_manager.update_memory(
                memory_id=memory_id,
                content=content_str,
                session_id=self.session_id,
                tags=tags
            )
            
        elif self.config.memory_mode == MemoryMode.JSON_CARDS:
            # Basic JSON cards mode
            if isinstance(content, dict):
                memory_content = content
            else:
                # For JSON cards, parse the memory_id and content
                parts = memory_id.split('.')
                if len(parts) == 3:
                    memory_content = {'value': content}
                else:
                    return {
                        "success": False,
                        "message": "Invalid memory_id format for JSON cards"
                    }
            
            success = self.memory_manager.update_memory(
                memory_id=memory_id,
                content=memory_content,
                session_id=self.session_id
            )
            
        elif self.config.memory_mode == MemoryMode.ADVANCED_JSON_CARDS:
            # Advanced JSON cards mode
            if not isinstance(content, dict):
                try:
                    content = json.loads(content)
                except:
                    return {
                        "success": False,
                        "message": "Advanced JSON cards mode requires properly structured JSON content"
                    }
            
            success = self.memory_manager.update_memory(
                memory_id=memory_id,
                content=content,
                session_id=self.session_id
            )
        else:
            success = False
        
        return {
            "success": success,
            "message": "Memory updated successfully" if success else "Memory not found"
        }
    
    def _tool_delete_memory(self, memory_id: str) -> Dict[str, Any]:
        """Delete a memory"""
        self.memory_manager.delete_memory(memory_id)
        return {
            "success": True,
            "message": f"Memory {memory_id} deleted"
        }
    
    def _save_trajectory(self, iteration: int, final_answer: Optional[str] = None):
        """Save current trajectory to file for debugging"""
        if not self.config.save_trajectory:
            return
        
        trajectory_data = {
            "timestamp": datetime.now().isoformat(),
            "iteration": iteration,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "model": self.model,
            "conversation": self.conversation,
            "tool_calls": [
                {
                    "tool_name": call.tool_name,
                    "arguments": call.arguments,
                    "result": call.result,
                    "error": call.error,
                    "timestamp": call.timestamp
                }
                for call in self.tool_calls
            ],
            "memory_state": self.memory_manager.get_context_string(),
            "final_answer": final_answer
        }
        
        try:
            with open(self.config.trajectory_file, 'w', encoding='utf-8') as f:
                json.dump(trajectory_data, f, indent=2, ensure_ascii=False)
            
            if self.verbose:
                logger.info(f"Trajectory saved to {self.config.trajectory_file}")
        except Exception as e:
            logger.warning(f"Failed to save trajectory: {e}")
    
    def execute_task(self, task: str, max_iterations: int = 15) -> Dict[str, Any]:
        """
        Execute a task using React pattern with tool calls and streaming support
        
        Args:
            task: The task/message from user
            max_iterations: Maximum number of tool call iterations
            
        Returns:
            Task execution result
        """
        # Add user message with memory context
        memory_context = self._get_memory_context()
        full_message = f"{task}\n\n{memory_context}"
        
        # Log the full prompt
        logger.info(f"User request: {task}")
        if memory_context:
            logger.info(f"Memory context added: {memory_context}")
        
        self.conversation.append({"role": "user", "content": full_message})
        
        iteration = 0
        final_answer = None
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Iteration {iteration}/{max_iterations}")
            
            # Save trajectory
            self._save_trajectory(iteration)
            
            logger.info(f"Sending streaming request to {self.provider.upper()} API")
            logger.info(f"Full conversation: {self.conversation}")
            logger.info(f"Tools available: {self._get_tools_description()}")
            
            try:
                # Create streaming response
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.conversation,
                    tools=self._get_tools_description(),
                    tool_choice="auto",
                    temperature=0.3,
                    max_tokens=4096,
                    stream=True  # Enable streaming
                )
                
                # Collect streaming data
                collected_content = []
                current_tool_calls = []
                
                # Process the stream
                collected_reasoning = []  # Separate collection for reasoning content
                
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta:
                        delta = chunk.choices[0].delta
                        
                        # Handle reasoning field (for o1 models and similar)
                        if hasattr(delta, 'reasoning') and delta.reasoning:
                            reasoning = delta.reasoning
                            collected_reasoning.append(reasoning)
                            
                            # Stream reasoning to console if verbose
                            if self.verbose:
                                if len(collected_reasoning) == 1:  # First reasoning chunk
                                    print("\n🤔 Reasoning: ", end="", flush=True)
                                print(reasoning, end="", flush=True)
                        
                        # Handle regular content streaming
                        if hasattr(delta, 'content') and delta.content:
                            content = delta.content
                            collected_content.append(content)
                            
                            # Stream to console if verbose
                            if self.verbose:
                                if len(collected_content) == 1 and not collected_reasoning:  # First content chunk
                                    print("\nAssistant: ", end="", flush=True)
                                print(content, end="", flush=True)
                        
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
                                    
                                    # Update tool call data
                                    if tool_call_delta.id:
                                        current_tool_calls[tool_call_delta.index]["id"] = tool_call_delta.id
                                    if tool_call_delta.function:
                                        if tool_call_delta.function.name:
                                            current_tool_calls[tool_call_delta.index]["function"]["name"] = tool_call_delta.function.name
                                            # Print tool call name when first detected
                                            if self.verbose:
                                                print(f"\n🔧 Tool Call [{tool_call_delta.index}]: {tool_call_delta.function.name}", end="", flush=True)
                                        if tool_call_delta.function.arguments:
                                            current_tool_calls[tool_call_delta.index]["function"]["arguments"] += tool_call_delta.function.arguments
                                            # Stream tool arguments in verbose mode
                                            if self.verbose:
                                                # Print arguments as they stream (they come in chunks)
                                                print(tool_call_delta.function.arguments, end="", flush=True)
                
                # Add newline after streaming content, reasoning or tool calls
                if self.verbose and (collected_content or collected_reasoning or current_tool_calls):
                    print()  # New line after streaming
                
                # Construct complete message matching OpenAI API structure
                # Keep reasoning, content, and tool_calls as separate fields
                complete_message = {
                    "role": "assistant"
                }
                
                # Add reasoning field if present
                if collected_reasoning:
                    reasoning_text = "".join(collected_reasoning)
                    complete_message["reasoning"] = reasoning_text
                
                # Add content field if present
                if collected_content:
                    complete_message["content"] = "".join(collected_content)
                else:
                    complete_message["content"] = None
                
                # Add tool_calls field if present
                if current_tool_calls:
                    complete_message["tool_calls"] = current_tool_calls
                
                # Always append the message if it has reasoning, content, or tool calls
                # This preserves all assistant output including reasoning
                if complete_message.get("reasoning") or complete_message.get("content") or current_tool_calls:
                    self.conversation.append(complete_message)
                
                # Handle tool calls if present
                if current_tool_calls:
                    for tool_call in current_tool_calls:
                        function_name = tool_call["function"]["name"]
                        function_args = json.loads(tool_call["function"]["arguments"])
                        
                        # Track tool call count
                        self.tool_call_counts[function_name] = self.tool_call_counts.get(function_name, 0) + 1
                        call_number = self.tool_call_counts[function_name]
                        
                        logger.info(f"Executing tool: {function_name} (call #{call_number})")
                        if self.verbose:
                            print(f"\n⚡ Executing: {function_name} (call #{call_number})")
                        
                        # Execute the tool
                        result, error = self._execute_tool(function_name, function_args)
                        
                        # Log and display result
                        if error:
                            logger.info(f"  ❌ Error: {error}")
                            if self.verbose:
                                print(f"\n  ❌ Tool Error: {error}")
                        else:
                            logger.info(f"  ✅ Success: {json.dumps(result)[:200]}")
                            if self.verbose:
                                result_str = json.dumps(result, ensure_ascii=False)
                                if len(result_str) > 200:
                                    result_str = result_str[:200] + "..."
                                print(f"\n  ✅ Tool Result: {result_str}")
                        
                        # Record tool call
                        tool_call_record = ToolCall(
                            tool_name=function_name,
                            arguments=function_args,
                            result=result if not error else None,
                            error=error
                        )
                        self.tool_calls.append(tool_call_record)
                        
                        # Add tool result to conversation
                        self.conversation.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": json.dumps(result)
                        })
                    
                    # Continue to next iteration for more processing
                    continue
                
                elif complete_message.get("content") or complete_message.get("reasoning"):
                    # No tool calls but has content or reasoning - this is the final answer
                    # Prioritize content over reasoning for the final answer
                    final_answer = complete_message.get("content") or complete_message.get("reasoning")
                    
                    # Log both reasoning and content if present
                    if complete_message.get("reasoning") and complete_message.get("content"):
                        logger.info(f"Response complete with reasoning and content")
                    else:
                        logger.info(f"Response complete (no more tool calls): {final_answer}")
                    
                    # Save conversation to history (use content if available, otherwise reasoning)
                    if self.conversation_history:
                        self.conversation_history.add_turn(
                            session_id=self.session_id,
                            user_message=task,
                            assistant_message=final_answer
                        )
                    
                    # Save final trajectory
                    self._save_trajectory(iteration, final_answer)
                    break  # Break when no more tool calls
                    
            except Exception as e:
                logger.error(f"Error during streaming task execution: {str(e)}")
                self._save_trajectory(iteration)
                return {
                    "error": str(e),
                    "tool_calls": self.tool_calls,
                    "iterations": iteration,
                    "trajectory_file": self.config.trajectory_file if self.config.save_trajectory else None
                }
        
        # Save final trajectory
        self._save_trajectory(iteration, final_answer)
        
        # Prepare result with all relevant information
        result = {
            "final_answer": final_answer,
            "tool_calls": self.tool_calls,
            "iterations": iteration,
            "success": final_answer is not None,
            "memory_state": self.memory_manager.get_context_string(),
            "trajectory_file": self.config.trajectory_file if self.config.save_trajectory else None
        }
        
        # Include reasoning if it was collected in the last message
        if self.conversation and isinstance(self.conversation[-1], dict):
            last_message = self.conversation[-1]
            if last_message.get("role") == "assistant" and last_message.get("reasoning"):
                result["reasoning"] = last_message["reasoning"]
        
        return result
    
    def chat(self, message: str, stream: bool = False) -> str:
        """
        Simple chat interface (wraps execute_task for compatibility)
        
        Args:
            message: User message
            stream: Whether to stream the response (only works when tools are disabled)
            
        Returns:
            Assistant response
        """
        if stream and not self.config.enable_memory_updates:
            # Stream response when tools are disabled
            return self._chat_stream(message)
        else:
            # Use regular execution with tools
            result = self.execute_task(message)
            return result.get('final_answer', result.get('error', 'I apologize, but I was unable to generate a response.'))
    
    def _chat_stream(self, message: str) -> str:
        """
        Stream chat response (only when tools are disabled)
        
        Args:
            message: User message
            
        Returns:
            Assistant response
        """
        # Get memory context
        memory_context = self._get_memory_context()
        
        if memory_context:
            full_message = f"Current Memory Context:\n{memory_context}\n\nUser Message: {message}"
        else:
            full_message = message
        
        # Log the full prompt
        logger.info(f"User request: {message}")
        if memory_context:
            logger.info(f"Memory context added: {memory_context}")
        logger.info(f"Full prompt sent to API (streaming): {full_message}")
        
        # Add to conversation
        self.conversation.append({"role": "user", "content": full_message})
        
        try:
            # Stream the response
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation,
                temperature=0.3,
                max_tokens=4096,
                stream=True
            )
            
            # Collect and stream response
            assistant_message = ""
            logger.info("Streaming response...")
            print("\nAssistant: ", end='', flush=True)
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
                    assistant_message += delta
                    # Stream output in real-time
                    print(delta, end='', flush=True)
            
            print()  # New line after streaming
            
            # Log the complete response
            logger.info(f"Assistant response (streamed): {assistant_message}")
            
            # Add to conversation
            self.conversation.append({"role": "assistant", "content": assistant_message})
            
            # Save to history if available
            if self.conversation_history:
                self.conversation_history.add_turn(
                    session_id=self.session_id,
                    user_message=message,
                    assistant_message=assistant_message
                )
            
            return assistant_message
            
        except Exception as e:
            logger.error(f"Error during streaming: {str(e)}")
            return f"Error: {str(e)}"
    
    def reset(self):
        """Reset the agent's state for a new conversation"""
        self.tool_calls = []
        self.tool_call_counts = {}
        self.session_id = self._start_session()
        self._init_system_prompt()
        logger.info("Agent state reset")
