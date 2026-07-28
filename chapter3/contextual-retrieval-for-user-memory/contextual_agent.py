"""Contextual RAG Agent with Advanced Memory Cards

This agent combines:
1. Advanced Memory Cards (structured facts) - always in context
2. Contextual RAG for searching conversation history
"""

import json
import logging
import time
from typing import List, Dict, Any, Optional, Generator
from dataclasses import dataclass, field
from datetime import datetime
from openai import OpenAI

from config import Config
from contextual_indexer import ContextualMemoryIndexer
from advanced_memory_manager import AdvancedMemoryManager
from tools import MemoryTools, get_tool_definitions


def _reasoning_safe_temperature(model, requested=1.0):
    """Reasoning models (Kimi K3, GPT-5, ...) only accept temperature=1.
    Return 1 for those; otherwise the requested value so non-reasoning
    providers (Doubao, DeepSeek, older Moonshot) are unchanged."""
    m = str(model or "").lower().replace("/", "-")
    return 1 if ("kimi-k3" in m or "gpt-5" in m) else requested


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Represents a message in the conversation"""
    role: str  # "user", "assistant", "tool"
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AgentTrajectory:
    """Tracks the agent's reasoning and tool usage"""
    test_id: str
    question: str
    iterations: List[Dict[str, Any]] = field(default_factory=list)
    final_answer: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    total_time: Optional[float] = None
    success: bool = False
    memory_cards_used: List[str] = field(default_factory=list)
    chunks_retrieved: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "question": self.question,
            "iterations": self.iterations,
            "final_answer": self.final_answer,
            "tool_calls": self.tool_calls,
            "total_time": self.total_time,
            "success": self.success,
            "total_iterations": len(self.iterations),
            "total_tool_calls": len(self.tool_calls),
            "memory_cards_used": self.memory_cards_used,
            "chunks_retrieved": self.chunks_retrieved
        }


class ContextualUserMemoryAgent:
    """Agent with dual memory system: structured cards + contextual RAG"""
    
    def __init__(self,
                 indexer: ContextualMemoryIndexer,
                 memory_manager: Optional[AdvancedMemoryManager] = None,
                 config: Optional[Config] = None):
        """
        Initialize the contextual agent
        
        Args:
            indexer: The contextual memory indexer
            memory_manager: Advanced memory manager (uses indexer's if not provided)
            config: Configuration object
        """
        self.config = config or Config.from_env()
        self.indexer = indexer
        self.memory_manager = memory_manager or indexer.memory_manager
        self.memory_tools = MemoryTools(indexer)  # Works with base indexer interface
        
        # Set verbose flag
        self.verbose = True  # Always verbose for debugging
        
        # Initialize LLM client
        self._init_llm_client()
        
        # Tool definitions - enhanced with contextual search
        self.tools = self._get_enhanced_tool_definitions()
        
        # Conversation history
        self.conversation_history: List[Dict[str, Any]] = []
        
        logger.info(f"Initialized ContextualUserMemoryAgent with dual memory system")
        logger.info(f"Memory cards loaded: {sum(len(cards) for cards in self.memory_manager.categories.values())}")
    
    def _init_llm_client(self):
        """Initialize the LLM client based on provider"""
        client_config, model = self.config.llm.get_client_config()
        
        # Extract base_url if present
        base_url = client_config.pop("base_url", None)
        
        # Create OpenAI client
        if base_url:
            self.client = OpenAI(base_url=base_url, **client_config)
        else:
            self.client = OpenAI(**client_config)
        
        self.model = model
        logger.info(f"Using model: {self.model}")
    
    def _get_enhanced_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get enhanced tool definitions for contextual search"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_conversation_history",
                    "description": "Search through indexed conversation history with contextual understanding. Returns conversation chunks with their contextual descriptions.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query to find relevant conversations"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of results to return",
                                "default": 3
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
    
    def _build_system_prompt(self) -> str:
        """Build enhanced system prompt with memory cards"""
        # Get memory cards context (always included in prompt)
        memory_context = self.memory_manager.get_context_string(max_cards=20)
        
        prompt = f"""You are an intelligent assistant with access to comprehensive user memory:

{memory_context}

=== YOUR CAPABILITIES ===
1. **Memory Cards** (shown above): Pre-loaded structured facts about the user
   - These are verified, persistent facts with backstories
   - Each card shows WHO it's about and WHY we know this
   - Always check these FIRST before searching

2. **Searchable Conversation History**: Use the search tool to find specific details
   - Conversations are chunked with contextual descriptions
   - Search when you need evidence or additional details
   - Each chunk includes context about what's being discussed

=== PROACTIVE SERVICE GUIDELINES ===
You should provide proactive service by:
1. **Anticipating Needs**: Look beyond the immediate question to identify related concerns
2. **Risk Detection**: Identify potential issues before they become problems
   - Check dates for expirations (passports, licenses, cards, insurances)
   - Notice scheduling conflicts or tight timelines
   - Flag missing preparations or requirements
3. **Comprehensive Assistance**: Connect different pieces of information
   - If user asks about travel, check passport, visa, insurance status
   - If discussing finances, consider upcoming payments or deadlines
   - For medical topics, recall relevant history and upcoming appointments
4. **Helpful Suggestions**: Offer actionable recommendations
   - Prioritize urgent matters (e.g., for time-sensitive issues)
   - Suggest next steps even if not explicitly requested
   - Remind about related tasks that might be overlooked

=== OPERATIONAL APPROACH ===
1. **Direct Answer First**: Address the user's immediate question clearly
2. **Then Proactive Service**: After answering, consider what else might be relevant
3. **Cross-Reference Information**: Actively connect related memory cards and conversations
4. **Cite Sources**: "According to memory card X..." or "Based on conversation Y..."
5. **Handle Conflicts**: Prefer more recent or more specific information
6. **Identify People**: Be specific about WHO information relates to

=== YOUR MISSION ===
Not just to answer questions, but to be a thoughtful assistant who:
- Notices what the user might have forgotten
- Warns about potential issues before they arise  
- Provides comprehensive support beyond what's asked
- Acts as a reliable memory partner who cares about the user's wellbeing

When answering, always consider: "What else should the user know about this topic?"

Remember: Good service answers the question. Great service anticipates what comes next."""

        return prompt
    
    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return results"""
        try:
            if tool_name == "search_conversation_history":
                query = arguments.get("query", "")
                top_k = arguments.get("top_k", 3)
                
                try:
                    # Use contextual search
                    search_results = self.indexer.search_with_context(
                        query=query,
                        top_k=top_k,
                        include_memory_cards=False  # Cards are already in context
                    )
                except Exception as search_error:
                    logger.error(f"Search failed: {search_error}")
                    return {
                        "status": "error",
                        "message": f"Search failed: {str(search_error)}",
                        "results": []
                    }
                
                chunk_results = search_results.get("chunk_results", [])
                
                if not chunk_results:
                    return {
                        "status": "success",
                        "message": "No relevant conversations found",
                        "results": []
                    }
                
                # Format results with context - NO TRUNCATION
                formatted_results = []
                for result in chunk_results:
                    formatted_results.append({
                        "chunk_id": result.get("chunk_id"),
                        "context": result.get("context", ""),  # Contextual description
                        "conversation": result.get("conversation_id"),
                        "rounds": result.get("rounds"),
                        "content": result.get("text", "")  # Full content, no truncation
                    })
                
                return {
                    "status": "success",
                    "results": formatted_results,
                    "total": len(formatted_results)
                }
            else:
                return {
                    "status": "error",
                    "message": f"Unknown tool: {tool_name}"
                }
                
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def answer_question(self,
                       question: str,
                       test_id: str = "unknown",
                       max_iterations: int = 10,
                       stream: bool = False) -> AgentTrajectory:
        """
        Answer a question using dual memory system
        
        Args:
            question: The question to answer
            test_id: Test case ID for tracking
            max_iterations: Maximum reasoning iterations
            stream: Whether to stream the response
            
        Returns:
            AgentTrajectory with the answer and reasoning steps
        """
        trajectory = AgentTrajectory(test_id=test_id, question=question)
        start_time = time.time()
        
        # Reset conversation for new question
        self.conversation_history = []
        
        # Build initial messages with system prompt
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": question}
        ]
        
        # Track which memory cards might be relevant
        relevant_cards = self._find_relevant_memory_cards(question)
        trajectory.memory_cards_used = relevant_cards
        
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            
            iteration_data = {
                "iteration": iteration,
                "timestamp": datetime.now().isoformat(),
                "messages_count": len(messages)
            }
            
            try:
                # Generate response
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                    temperature=_reasoning_safe_temperature(self.model, 0.3),
                    max_tokens=2048,
                    stream=stream
                )
                
                if stream:
                    # Handle streaming response
                    assistant_content = ""
                    tool_calls = []
                    
                    for chunk in response:
                        if chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            assistant_content += content
                            if self.verbose:
                                print(content, end='', flush=True)
                        
                        # Handle tool calls in stream
                        if chunk.choices[0].delta.tool_calls:
                            # Tool-call deltas are not accumulated on this
                            # path; silently dropping them would produce an
                            # empty answer marked success=True. Fail loudly
                            # until streaming tool support is implemented.
                            raise NotImplementedError(
                                "stream=True does not support tool calls yet; "
                                "use stream=False"
                            )
                    
                    # Process complete response
                    assistant_message = {
                        "role": "assistant",
                        "content": assistant_content if assistant_content else None
                    }
                else:
                    # Non-streaming response
                    choice = response.choices[0]
                    assistant_message = {
                        "role": "assistant",
                        "content": choice.message.content
                    }
                    
                    # Check for tool calls
                    if choice.message.tool_calls:
                        assistant_message["tool_calls"] = [
                            tc.model_dump() for tc in choice.message.tool_calls
                        ]
                
                messages.append(assistant_message)
                iteration_data["response"] = assistant_message
                
                # Handle tool calls
                if assistant_message.get("tool_calls"):
                    if self.verbose:
                        print(f"\n{'='*80}")
                        print(f"🤖 LLM MADE {len(assistant_message['tool_calls'])} TOOL CALL(S)")
                        print(f"{'='*80}")
                        print("Tool calls:")
                        for tc in assistant_message["tool_calls"]:
                            print(f"  - {tc['function']['name']}")
                        print()
                    
                    for tool_call in assistant_message["tool_calls"]:
                        tool_name = tool_call["function"]["name"]
                        # The assistant message with tool_calls is already in
                        # the conversation; answer malformed arguments with an
                        # error tool message instead of failing the question
                        # (same guard as the sibling agents).
                        try:
                            tool_args = json.loads(tool_call["function"]["arguments"] or "{}")
                        except json.JSONDecodeError as exc:
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call["id"],
                                "content": json.dumps({"error": f"Invalid tool arguments (not valid JSON): {exc}"})
                            })
                            continue

                        # Execute tool
                        tool_result = self._execute_tool(tool_name, tool_args)
                        
                        # Track tool usage
                        trajectory.tool_calls.append({
                            "iteration": iteration,
                            "tool": tool_name,
                            "arguments": tool_args,
                            "result": tool_result
                        })
                        
                        # Track retrieved chunks
                        if tool_name == "search_conversation_history" and tool_result.get("results"):
                            for result in tool_result["results"]:
                                trajectory.chunks_retrieved.append(result.get("chunk_id", ""))
                        
                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": json.dumps(tool_result)
                        })
                        
                        if self.verbose:
                            print(f"\n{'='*80}")
                            print(f"🔧 TOOL CALL: {tool_name}")
                            print(f"{'='*80}")
                            print(f"📥 Arguments:")
                            print(json.dumps(tool_args, indent=2, ensure_ascii=False))
                            print(f"\n📤 Result (FULL - NO TRUNCATION):")
                            print(json.dumps(tool_result, indent=2, ensure_ascii=False))
                            print(f"{'='*80}\n")
                else:
                    # No tool calls means we have the final answer
                    trajectory.final_answer = assistant_message.get("content", "")
                    trajectory.success = True
                    break
                
                trajectory.iterations.append(iteration_data)
                
            except Exception as e:
                logger.error(f"Error in iteration {iteration}: {e}")
                iteration_data["error"] = str(e)
                trajectory.iterations.append(iteration_data)
                break
        
        # Record timing
        trajectory.total_time = time.time() - start_time
        
        # Store conversation history
        self.conversation_history = messages
        
        if self.verbose:
            print(f"\n{'='*80}")
            print(f"✅ EVALUATION COMPLETE")
            print(f"{'='*80}")
            print(f"Iterations: {iteration}")
            print(f"Total Time: {trajectory.total_time:.2f}s")
            print(f"Memory Cards Used: {len(trajectory.memory_cards_used)}")
            if trajectory.memory_cards_used:
                print(f"  Cards: {trajectory.memory_cards_used}")
            print(f"Chunks Retrieved: {len(trajectory.chunks_retrieved)}")
            if trajectory.chunks_retrieved:
                print(f"  Chunks: {trajectory.chunks_retrieved}")
            print(f"\n📝 FINAL ANSWER:")
            print(trajectory.final_answer or "No answer generated")
            print(f"{'='*80}\n")
        
        return trajectory
    
    def _find_relevant_memory_cards(self, question: str) -> List[str]:
        """Find which memory cards might be relevant to the question"""
        relevant = []
        question_lower = question.lower()
        
        # Simple keyword matching (could be enhanced with embeddings)
        for category, cards in self.memory_manager.categories.items():
            for card_key, card in cards.items():
                card_str = json.dumps(card.to_dict()).lower()
                # Check if any question keywords appear in the card
                if any(word in card_str for word in question_lower.split() if len(word) > 3):
                    relevant.append(f"{category}.{card_key}")
        
        return relevant
    
    def reset(self):
        """Reset the agent state"""
        self.conversation_history = []
        logger.info("Agent state reset")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            "memory_cards": sum(len(cards) for cards in self.memory_manager.categories.values()),
            "indexed_chunks": len(self.indexer.contextual_chunks),
            "conversation_history_length": len(self.conversation_history),
            "indexer_stats": self.indexer.get_statistics()
        }
