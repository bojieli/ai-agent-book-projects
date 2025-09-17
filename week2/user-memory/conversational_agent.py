"""
Conversational Agent - Focuses purely on conversation without direct memory management
Memory updates are handled by a separate background process
"""

import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid
from openai import OpenAI
from config import Config
from conversation_history import ConversationHistory, ConversationTurn
from memory_manager import create_memory_manager, BaseMemoryManager, MemoryMode

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class ConversationConfig:
    """Configuration for the conversational agent"""
    enable_memory_context: bool = True  # Include memory in context but don't update
    enable_conversation_history: bool = True
    max_memory_context: int = 10
    temperature: float = 0.7
    max_tokens: int = 4096


class ConversationalAgent:
    """
    Pure conversational agent that focuses on dialogue
    Reads memory for context but doesn't update it directly
    """
    
    def __init__(self, 
                 user_id: str,
                 api_key: Optional[str] = None,
                 provider: Optional[str] = None,
                 model: Optional[str] = None,
                 config: Optional[ConversationConfig] = None,
                 memory_mode: MemoryMode = MemoryMode.NOTES,
                 verbose: bool = True):
        """
        Initialize the conversational agent
        
        Args:
            user_id: Unique user identifier
            api_key: API key (defaults to env based on provider)
            provider: LLM provider ('siliconflow', 'doubao', 'kimi', 'moonshot')
            model: Model name (defaults to provider's default)
            config: Agent configuration
            memory_mode: Memory storage mode
            verbose: Enable verbose logging
        """
        self.user_id = user_id
        self.verbose = verbose
        self.config = config or ConversationConfig()
        self.memory_mode = memory_mode
        
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
        
        # Initialize memory manager (read-only access)
        self.memory_manager = create_memory_manager(user_id, memory_mode)
        
        # Initialize conversation history
        self.conversation_history = ConversationHistory(user_id) if self.config.enable_conversation_history else None
        
        # Track current session
        self.session_id = self._generate_session_id()
        self.conversation = []
        
        # Initialize system prompt
        self._init_system_prompt()
        
        logger.info(f"ConversationalAgent initialized for user {user_id} with {self.provider} provider using {self.model}")
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        return f"session-{uuid.uuid4().hex[:8]}"
    
    def _init_system_prompt(self):
        """Initialize the system prompt"""
        system_content = """You are a helpful and personalized assistant. You have access to information about the user from previous conversations, which helps you provide personalized and contextual responses.

You MUST analyze the context, user's questions and memories in detail, and provide a comprehensive and detailed response.
"""

        self.conversation = [
            {
                "role": "system",
                "content": system_content
            }
        ]
    
    def _get_memory_context(self) -> str:
        """Get current memory context as a string"""
        if not self.config.enable_memory_context:
            return ""
        
        context_parts = []
        
        # Add memory summary
        memory_str = self.memory_manager.get_context_string()
        if memory_str:
            context_parts.append("=== USER CONTEXT ===")
            context_parts.append(memory_str)
            context_parts.append("")
        
        # Add ALL conversation history
        if self.conversation_history:
            # Get ALL conversation history, not just recent
            all_conversations = self.conversation_history.conversations if hasattr(self.conversation_history, 'conversations') else []
            
            if all_conversations:
                context_parts.append("=== FULL CONVERSATION HISTORY ===")
                context_parts.append(f"Total conversations: {len(all_conversations)}")
                context_parts.append("")
                
                for turn in all_conversations:
                    context_parts.append(f"[Session: {turn.session_id}, Turn {turn.turn_number}, Time: {turn.timestamp}]")
                    context_parts.append(f"User: {turn.user_message}")
                    context_parts.append(f"Assistant: {turn.assistant_message}")
                    context_parts.append("")
        
        return "\n".join(context_parts)
    
    def get_conversation_context(self) -> List[Dict[str, str]]:
        """
        Get the full conversation context for background memory processing
        
        Returns:
            List of conversation messages
        """
        # Return a copy of the conversation without system prompt
        return [msg for msg in self.conversation[1:] if msg.get('role') != 'system']
    
    def chat(self, message: str) -> str:
        """
        Have a conversation with the user
        
        Args:
            message: User message
            
        Returns:
            Assistant response
        """
        # Add memory context to the user message
        memory_context = self._get_memory_context()
        
        if memory_context:
            full_message = f"{message}\n\n{memory_context}"
        else:
            full_message = message
        
        # Log the full prompt if verbose
        if self.verbose:
            logger.info(f"User request: {message}")
            if memory_context:
                logger.info(f"Memory context added: {memory_context}")
            logger.info(f"Full prompt sent to API: {full_message}")
        
        # Add to conversation
        self.conversation.append({"role": "user", "content": full_message})
        
        try:
            # Call the model with streaming
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=True
            )
            
            # Collect streamed response
            assistant_message = ""
            if self.verbose:
                logger.info("Streaming response...")
                
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
                    assistant_message += delta
                    # Always stream output to show real-time response
                    print(delta, end='', flush=True)
            
            print()  # New line after streaming
            
            # Add assistant response to conversation
            self.conversation.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            # Save to conversation history
            if self.conversation_history:
                self.conversation_history.add_turn(
                    session_id=self.session_id,
                    user_message=message,
                    assistant_message=assistant_message
                )
            
            if self.verbose:
                logger.info(f"User: {message}")
                logger.info(f"Assistant: {assistant_message}")
            
            return assistant_message
            
        except Exception as e:
            error_msg = f"Error during conversation: {str(e)}"
            logger.error(error_msg)
            return f"I apologize, but I encountered an error: {str(e)}"
    
    def reset_session(self):
        """Start a new conversation session"""
        self.session_id = self._generate_session_id()
        self._init_system_prompt()
        logger.info(f"Started new session: {self.session_id}")
    
    def get_session_id(self) -> str:
        """Get the current session ID"""
        return self.session_id
