"""Mem0-powered agent with Kimi K3 integration for LOCOMO benchmark."""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from collections import defaultdict

from mem0 import Memory, MemoryClient
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import numpy as np
from rich.console import Console
from rich.table import Table
from rich.progress import track

from config import Config, config as default_config


def _reasoning_safe_temperature(model, requested=1.0):
    """Reasoning models (Kimi K3, GPT-5, ...) only accept temperature=1.
    Return 1 for those; otherwise the requested value so non-reasoning
    providers (Doubao, DeepSeek, older Moonshot) are unchanged."""
    m = str(model or "").lower().replace("/", "-")
    return 1 if ("kimi-k3" in m or "gpt-5" in m) else requested


def _as_memory_list(result: Any) -> List[Dict[str, Any]]:
    """Normalize a mem0 return value to a plain list of memory dicts.

    Current mem0 OSS returns ``{"results": [...]}``; accepting a bare list as
    well keeps the helper useful for simple test doubles.
    """
    if isinstance(result, dict):
        return result.get("results", []) or []
    if isinstance(result, list):
        return result
    return []


def _extract_added_memories(add_result: Any) -> List[Dict[str, str]]:
    """Return facts appended by mem0's v3 ADD-only extraction pass."""
    added = []
    for item in _as_memory_list(add_result):
        added.append({
            "memory": item.get("memory", item.get("text", "")),
            "id": item.get("id", ""),
        })
    return added


def _memory_filters(user_id: str, agent_id: Optional[str] = None) -> Dict[str, str]:
    """Build the entity filter required by mem0 v3 search/get_all."""
    filters = {"user_id": user_id}
    if agent_id:
        filters["agent_id"] = agent_id
    return filters


# Set up logging
logging.basicConfig(
    level=getattr(logging, default_config.logging.level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
console = Console()


@dataclass
class AgentContext:
    """Context information for an agent in the LOCOMO benchmark."""
    
    agent_id: str
    user_id: str
    session_id: str
    turn_count: int = 0
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_turn(self, role: str, content: str) -> None:
        """Add a turn to the conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "turn": self.turn_count
        })
        self.turn_count += 1


class KimiK3Client:
    """Client for interacting with Kimi K3 model."""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = OpenAI(
            api_key=config.kimi.api_key,
            base_url=config.kimi.api_base
        )
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate response using Kimi K3 model."""
        try:
            response = self.client.chat.completions.create(
                model=self.config.kimi.model_name,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", self.config.kimi.max_tokens),
                temperature=_reasoning_safe_temperature(self.config.kimi.model_name, kwargs.get("temperature", self.config.kimi.temperature)),
                top_p=kwargs.get("top_p", 0.95),
                frequency_penalty=kwargs.get("frequency_penalty", 0),
                presence_penalty=kwargs.get("presence_penalty", 0)
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating response with Kimi K3: {e}")
            raise
    
    async def agenerate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Async generate response using Kimi K3 model."""
        return await asyncio.to_thread(self.generate, messages, **kwargs)


class Mem0Agent:
    """Agent powered by Mem0 memory system and Kimi K3 model."""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or default_config
        self.config.validate()
        
        # Initialize Kimi K3 client
        self.llm_client = KimiK3Client(self.config)
        
        # Initialize Mem0 memory system
        self._init_memory()
        
        # Agent state management
        self.active_contexts: Dict[str, AgentContext] = {}
        self.performance_metrics: Dict[str, List[float]] = defaultdict(list)
        
    def _init_memory(self) -> None:
        """Initialize Mem0 memory system."""
        # Mem0 runs its own LLM call for ADD-only fact extraction. Left unset,
        # mem0 defaults to
        # max_tokens=2000 / temperature=0.1, which is unsafe for reasoning
        # models (Kimi K3 wants temperature=1 and enough room for its thinking
        # tokens). Pin both explicitly so the pipeline is reasoning-safe.
        mem0_config = {
            "llm": {
                "provider": "openai",
                "config": {
                    "api_key": self.config.kimi.api_key,
                    # mem0 >=1.0 names this field openai_base_url (not base_url);
                    # it points the OpenAI-compatible client at Moonshot.
                    "openai_base_url": self.config.kimi.api_base,
                    "model": self.config.kimi.model_name,
                    "temperature": _reasoning_safe_temperature(
                        self.config.kimi.model_name, self.config.kimi.temperature
                    ),
                    "max_tokens": max(self.config.kimi.max_tokens, 2048),
                }
            },
            "vector_store": self.config.mem0.vector_store_config,
            "embedder": {
                "provider": "openai",
                "config": {
                    "model": self.config.mem0.embedding_model
                }
            }
        }
        
        if self.config.mem0.backend == "local":
            self.memory = Memory.from_config(mem0_config)
        else:
            self.memory = MemoryClient(api_key=self.config.mem0.api_key)
        
        logger.info(f"Initialized Mem0 memory system with {self.config.mem0.backend} backend")
    
    def create_context(self, agent_id: str, user_id: str, session_id: str) -> AgentContext:
        """Create a new agent context for a session."""
        context = AgentContext(
            agent_id=agent_id,
            user_id=user_id,
            session_id=session_id,
            metadata={
                "created_at": datetime.now().isoformat(),
                "model": self.config.kimi.model_name
            }
        )
        self.active_contexts[session_id] = context
        logger.info(f"Created context for agent {agent_id} in session {session_id}")
        return context
    
    def get_context(self, session_id: str) -> Optional[AgentContext]:
        """Get agent context for a session."""
        return self.active_contexts.get(session_id)
    
    def _prepare_messages(self, context: AgentContext, user_input: str) -> List[Dict[str, str]]:
        """Prepare messages for LLM including memory context."""
        messages = []
        
        # System prompt
        system_prompt = f"""You are an intelligent agent participating in the LOCOMO benchmark.
Your task is to maintain consistent and coherent conversations across multiple sessions.
You have access to a memory system that helps you remember important information.

Agent ID: {context.agent_id}
User ID: {context.user_id}
Session ID: {context.session_id}
Current Turn: {context.turn_count}

Guidelines:
1. Maintain consistency with previous conversations
2. Reference relevant past information when appropriate
3. Build upon established context naturally
4. Be concise but informative in your responses
"""
        messages.append({"role": "system", "content": system_prompt})
        
        # Retrieve relevant memories
        memories = _as_memory_list(self.memory.search(
            query=user_input,
            filters=_memory_filters(context.user_id, context.agent_id),
            top_k=5,
        ))
        
        if memories and len(memories) > 0:
            memory_context = "\n\nRelevant memories from past interactions:\n"
            for mem in memories:
                memory_context += f"- {mem.get('memory', mem.get('text', ''))}\n"
            messages.append({"role": "system", "content": memory_context})
        
        # Add recent conversation history (last 10 turns)
        recent_history = context.conversation_history[-10:] if len(context.conversation_history) > 10 else context.conversation_history
        for turn in recent_history:
            messages.append({"role": turn["role"], "content": turn["content"]})
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    def process_turn(self, session_id: str, user_input: str) -> Tuple[str, Dict[str, Any]]:
        """Process a single turn in the conversation."""
        context = self.get_context(session_id)
        if not context:
            raise ValueError(f"No context found for session {session_id}")
        
        # Record user input
        context.add_turn("user", user_input)
        
        # Prepare messages with memory context
        messages = self._prepare_messages(context, user_input)
        
        # Generate response using Kimi K3
        start_time = datetime.now()
        response = self.llm_client.generate(messages)
        generation_time = (datetime.now() - start_time).total_seconds()
        
        # Record assistant response
        context.add_turn("assistant", response)
        
        # Store interaction in memory. Mem0 v3 performs one ADD-only
        # extraction pass and returns the facts it appended.
        add_result = self.memory.add(
            messages=[
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": response}
            ],
            user_id=context.user_id,
            agent_id=context.agent_id,
            metadata={
                "session_id": session_id,
                "turn": context.turn_count - 1,
                "timestamp": datetime.now().isoformat()
            }
        )
        added_memories = _extract_added_memories(add_result)

        # Calculate metrics
        metrics = {
            "generation_time": generation_time,
            "response_length": len(response),
            "turn_count": context.turn_count,
            "memory_count": len(self.get_all_memories(context.user_id, top_k=100)),
            "added_memories": added_memories,
        }
        
        # Store performance metrics
        self.performance_metrics[session_id].append(generation_time)
        
        logger.info(f"Processed turn {context.turn_count} for session {session_id} in {generation_time:.2f}s")
        
        return response, metrics
    
    async def process_turn_async(self, session_id: str, user_input: str) -> Tuple[str, Dict[str, Any]]:
        """Async version of process_turn."""
        return await asyncio.to_thread(self.process_turn, session_id, user_input)

    # ------------------------------------------------------------------
    # Direct memory operations (used by the CLI and the pipeline demo)
    # ------------------------------------------------------------------
    def add_memory(self, messages, user_id: str, agent_id: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        """Add a message/conversation to memory.

        Returns the facts appended by mem0's ADD-only extraction. An empty
        list means that no new fact was extracted (including exact dedupes).
        ``messages`` may be a plain string or an OpenAI-style message list.
        """
        add_result = self.memory.add(
            messages=messages,
            user_id=user_id,
            agent_id=agent_id,
            metadata=metadata or {}
        )
        return _extract_added_memories(add_result)

    def search_memory(self, query: str, user_id: str, agent_id: Optional[str] = None,
                      top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve memories with mem0 v3's fused search signals."""
        return _as_memory_list(self.memory.search(
            query=query,
            filters=_memory_filters(user_id, agent_id),
            top_k=top_k,
        ))

    def get_all_memories(self, user_id: str, agent_id: Optional[str] = None,
                         top_k: int = 100) -> List[Dict[str, Any]]:
        """List up to ``top_k`` stored memories for a user."""
        kwargs = {"filters": _memory_filters(user_id, agent_id)}
        if isinstance(self.memory, MemoryClient):
            kwargs["page_size"] = top_k
        else:
            kwargs["top_k"] = top_k
        return _as_memory_list(self.memory.get_all(**kwargs))

    def memory_history(self, memory_id: str) -> List[Dict[str, Any]]:
        """Return the audit history of one memory."""
        return self.memory.history(memory_id)

    def delete_memory(self, memory_id: str) -> str:
        """Delete a single memory by id."""
        self.memory.delete(memory_id)
        return memory_id
    
    def evaluate_consistency(self, session_id: str) -> float:
        """Evaluate consistency of responses in a session."""
        context = self.get_context(session_id)
        if not context or len(context.conversation_history) < 2:
            return 1.0
        
        # Simple consistency check based on response patterns
        responses = [turn["content"] for turn in context.conversation_history if turn["role"] == "assistant"]
        
        if len(responses) < 2:
            return 1.0
        
        # Calculate consistency score based on semantic similarity (simplified)
        # In a real implementation, you would use embeddings and cosine similarity
        consistency_scores = []
        for i in range(1, len(responses)):
            # Simplified: check for contradiction keywords
            prev_response = responses[i-1].lower()
            curr_response = responses[i].lower()
            
            contradiction_words = ["however", "but actually", "correction", "i was wrong", "let me correct"]
            has_contradiction = any(word in curr_response for word in contradiction_words)
            
            consistency_scores.append(0.5 if has_contradiction else 1.0)
        
        return np.mean(consistency_scores) if consistency_scores else 1.0
    
    def evaluate_coherence(self, session_id: str) -> float:
        """Evaluate coherence of the conversation."""
        context = self.get_context(session_id)
        if not context or len(context.conversation_history) < 2:
            return 1.0
        
        # Simple coherence check based on response relevance
        coherence_scores = []
        for i in range(0, len(context.conversation_history) - 1, 2):
            if i + 1 < len(context.conversation_history):
                user_turn = context.conversation_history[i]["content"]
                assistant_turn = context.conversation_history[i + 1]["content"]
                
                # Check if response addresses the user input (simplified)
                user_keywords = set(user_turn.lower().split())
                assistant_keywords = set(assistant_turn.lower().split())
                
                overlap = len(user_keywords.intersection(assistant_keywords))
                score = min(1.0, overlap / max(len(user_keywords), 1) * 2)
                coherence_scores.append(score)
        
        return np.mean(coherence_scores) if coherence_scores else 1.0
    
    def evaluate_memory_retention(self, user_id: str) -> float:
        """Evaluate memory retention for a user."""
        memories = self.get_all_memories(user_id, top_k=100)

        if not memories or len(memories) == 0:
            return 0.0
        
        # Calculate retention score based on memory count and recency
        now = datetime.now()
        retention_scores = []
        
        for memory in memories:
            created_at = memory.get("created_at", now.isoformat())
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            
            age_hours = (now - created_at).total_seconds() / 3600
            # Decay function: memories lose value over time
            retention_score = np.exp(-age_hours / 24)  # Half-life of 24 hours
            retention_scores.append(retention_score)
        
        return np.mean(retention_scores)
    
    def get_performance_summary(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get performance summary for a session or all sessions."""
        if session_id:
            context = self.get_context(session_id)
            if not context:
                return {}
            
            metrics = self.performance_metrics.get(session_id, [])
            return {
                "session_id": session_id,
                "turn_count": context.turn_count,
                "avg_response_time": np.mean(metrics) if metrics else 0,
                "consistency_score": self.evaluate_consistency(session_id),
                "coherence_score": self.evaluate_coherence(session_id),
                "memory_retention": self.evaluate_memory_retention(context.user_id)
            }
        else:
            # Aggregate metrics for all sessions
            all_metrics = []
            for sid in self.active_contexts:
                all_metrics.append(self.get_performance_summary(sid))
            
            if not all_metrics:
                return {}
            
            return {
                "total_sessions": len(all_metrics),
                "avg_turn_count": np.mean([m["turn_count"] for m in all_metrics]),
                "avg_response_time": np.mean([m["avg_response_time"] for m in all_metrics]),
                "avg_consistency": np.mean([m["consistency_score"] for m in all_metrics]),
                "avg_coherence": np.mean([m["coherence_score"] for m in all_metrics]),
                "avg_memory_retention": np.mean([m["memory_retention"] for m in all_metrics])
            }
    
    def display_metrics(self, session_id: Optional[str] = None) -> None:
        """Display performance metrics in a formatted table."""
        summary = self.get_performance_summary(session_id)
        
        if not summary:
            console.print("[yellow]No metrics available[/yellow]")
            return
        
        table = Table(title="Performance Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in summary.items():
            if isinstance(value, float):
                table.add_row(key.replace("_", " ").title(), f"{value:.4f}")
            else:
                table.add_row(key.replace("_", " ").title(), str(value))
        
        console.print(table)
    
    def reset(self) -> None:
        """Reset the agent state."""
        self.active_contexts.clear()
        self.performance_metrics.clear()
        logger.info("Agent state reset")
    
    def save_state(self, filepath: str) -> None:
        """Save agent state to file."""
        state = {
            "contexts": {
                sid: {
                    "agent_id": ctx.agent_id,
                    "user_id": ctx.user_id,
                    "session_id": ctx.session_id,
                    "turn_count": ctx.turn_count,
                    "conversation_history": ctx.conversation_history,
                    "metadata": ctx.metadata
                }
                for sid, ctx in self.active_contexts.items()
            },
            "metrics": dict(self.performance_metrics),
            "timestamp": datetime.now().isoformat()
        }
        
        with open(filepath, "w") as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"Agent state saved to {filepath}")
    
    def load_state(self, filepath: str) -> None:
        """Load agent state from file."""
        with open(filepath, "r") as f:
            state = json.load(f)
        
        self.active_contexts.clear()
        for sid, ctx_data in state["contexts"].items():
            context = AgentContext(
                agent_id=ctx_data["agent_id"],
                user_id=ctx_data["user_id"],
                session_id=ctx_data["session_id"],
                turn_count=ctx_data["turn_count"],
                conversation_history=ctx_data["conversation_history"],
                metadata=ctx_data["metadata"]
            )
            self.active_contexts[sid] = context
        
        self.performance_metrics = defaultdict(list, state["metrics"])
        
        logger.info(f"Agent state loaded from {filepath}")
