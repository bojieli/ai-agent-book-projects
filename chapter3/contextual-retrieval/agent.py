"""Agentic RAG System with ReAct Pattern"""

import json
import logging
from typing import List, Dict, Any, Optional, Generator
from dataclasses import dataclass, field
from datetime import datetime
from openai import OpenAI

from config import Config, LLMConfig, AgentConfig
from tools import KnowledgeBaseTools, get_tool_definitions


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


class AgenticRAG:
    """Agentic RAG system with ReAct pattern and multiple LLM provider support"""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the agent"""
        self.config = config or Config.from_env()
        
        # Initialize LLM client
        self._init_llm_client()
        
        # Initialize knowledge base tools
        self.kb_tools = KnowledgeBaseTools(self.config.knowledge_base)
        
        # Conversation history
        self.conversation_history: List[Dict[str, Any]] = []
        
        # Tool definitions
        self.tools = get_tool_definitions()
        
        logger.info(f"Initialized AgenticRAG with provider: {self.config.llm.provider}")
    
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
    
    def _get_system_prompt(self) -> str:
        """Generate the system prompt"""
        return """You are an intelligent assistant with access to a knowledge base. Your primary role is to answer questions accurately based on the information available in the knowledge base.

## Important Guidelines:

1. **Knowledge Base Only**: You MUST only answer questions based on information found in the knowledge base. If the information is not available, clearly state that you cannot answer based on the available knowledge.

2. **Use Tools Effectively**:
   - Use `knowledge_base_search` to search for relevant information
   - Use `get_document` to retrieve complete documents when you need more context
   - You may need multiple searches with different queries to fully answer a question

3. **Citations Required**: Always include citations in your answers. Format citations as [Doc: document_id] or [Chunk: chunk_id] inline with your response.

4. **Reasoning Process**: Think step-by-step:
   - First, understand what information is needed
   - Search for relevant information
   - If needed, retrieve full documents for context
   - Synthesize the information to answer the question
   - Include proper citations

5. **Handle Follow-ups**: For follow-up questions, consider the conversation context but always verify information from the knowledge base.

6. **Be Accurate**: Never make up information. If something is unclear or not found, say so explicitly.

Remember: Your credibility depends on providing accurate, well-cited information from the knowledge base only."""
    
    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool and return the result"""
        try:
            if tool_name == "knowledge_base_search":
                query = arguments.get("query", "")
                if self.config.agent.verbose:
                    logger.info(f"Executing tool: {tool_name} with args: {arguments}")
                
                results = self.kb_tools.knowledge_base_search(query)
                
                if not results:
                    logger.info(f"No results found for query: {query}")
                    return {"status": "no_results", "message": f"No relevant documents found for query: {query}"}
                
                # Format results for agent
                formatted_results = []
                for r in results:
                    formatted_results.append({
                        "doc_id": r["doc_id"],
                        "chunk_id": r["chunk_id"],
                        "text": r["text"],
                        "score": r["score"]
                    })
                
                return {
                    "status": "success",
                    "results": formatted_results,
                    "total_found": len(results)
                }
                
            elif tool_name == "get_document":
                doc_id = arguments.get("doc_id", "")
                document = self.kb_tools.get_document(doc_id)
                
                if "error" in document:
                    return {"status": "error", "message": document["error"]}
                
                return {
                    "status": "success",
                    "document": {
                        "doc_id": document.get("doc_id", doc_id),
                        "content": document.get("content", ""),
                        "metadata": document.get("metadata", {})
                    }
                }
            
            else:
                return {"status": "error", "message": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {"status": "error", "message": str(e)}
    
    def _build_messages(self, user_query: str) -> List[Dict[str, Any]]:
        """Build messages for the LLM including conversation history"""
        messages = [{"role": "system", "content": self._get_system_prompt()}]
        
        # Add conversation history (limited)
        history_limit = self.config.agent.conversation_history_limit
        # limit<=0 → no history; list[-0:] would include all turns.
        if history_limit > 0:
            if len(self.conversation_history) > history_limit:
                messages.extend(self.conversation_history[-history_limit:])
            else:
                messages.extend(self.conversation_history)
        
        # Add current user query
        messages.append({"role": "user", "content": user_query})
        
        return messages
    
    def query(self, user_query: str, stream: bool = None) -> Any:
        """
        Process a user query using the ReAct pattern.
        
        Args:
            user_query: The user's question
            stream: Whether to stream the response
            
        Returns:
            The agent's response (string or generator for streaming)
        """
        if stream is None:
            stream = self.config.llm.stream
        
        # Build messages
        messages = self._build_messages(user_query)
        
        # Track iterations
        iterations = 0
        max_iterations = self.config.agent.max_iterations
        
        # Process with ReAct loop
        while iterations < max_iterations:
            iterations += 1
            
            if self.config.agent.verbose:
                logger.info(f"Iteration {iterations}/{max_iterations}")
            
            try:
                # Call LLM with tools
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                    temperature=_reasoning_safe_temperature(self.model, self.config.llm.temperature),
                    max_tokens=self.config.llm.max_tokens,
                    stream=False  # We handle streaming separately
                )
                
                message = response.choices[0].message
                
                # Add assistant message to history
                assistant_msg = {"role": "assistant", "content": message.content or ""}
                if message.tool_calls:
                    assistant_msg["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in message.tool_calls
                    ]
                messages.append(assistant_msg)
                
                # Process tool calls if present
                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        try:
                            arguments = json.loads(tool_call.function.arguments)
                        except json.JSONDecodeError:
                            logger.error(f"Failed to parse tool arguments: {tool_call.function.arguments}")
                            arguments = {}
                        
                        # Execute tool
                        result = self._execute_tool(tool_name, arguments)
                        
                        if self.config.agent.verbose:
                            logger.info(f"Tool result: {json.dumps(result, indent=2, ensure_ascii=False)}")
                        
                        # Add tool result to messages
                        tool_message = {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result, indent=2, ensure_ascii=False)
                        }
                        messages.append(tool_message)
                    
                    # Continue loop for next iteration
                    continue
                else:
                    # No tool calls, we have final answer
                    # Update conversation history
                    self.conversation_history.append({"role": "user", "content": user_query})
                    self.conversation_history.append(assistant_msg)
                    
                    final_response = message.content or ""
                    
                    # Log the final response if verbose
                    if self.config.agent.verbose:
                        logger.info(f"Final response generated (length: {len(final_response)} chars)")
                    
                    # Return response
                    if stream:
                        return self._stream_response(final_response)
                    else:
                        return final_response
                        
            except Exception as e:
                logger.error(f"Error in query processing: {e}")
                error_msg = f"Error processing query: {str(e)}"
                if stream:
                    return self._stream_response(error_msg)
                else:
                    return error_msg
        
        # Max iterations reached
        logger.warning(f"Max iterations ({max_iterations}) reached")
        final_msg = "I need more iterations to fully answer your question. Please try rephrasing or breaking down your query."
        
        if stream:
            return self._stream_response(final_msg)
        else:
            return final_msg
    
    def _stream_response(self, content: str) -> Generator[str, None, None]:
        """Stream response content"""
        # Simple character streaming for demonstration
        for char in content:
            yield char
    
    def query_non_agentic(self, user_query: str, stream: bool = None) -> Any:
        """
        Non-agentic RAG mode: Simple retrieval + LLM response.
        
        Args:
            user_query: The user's question
            stream: Whether to stream the response
            
        Returns:
            The response (string or generator for streaming)
        """
        if stream is None:
            stream = self.config.llm.stream
        
        try:
            # Simple retrieval
            if self.config.agent.verbose:
                logger.info(f"Non-agentic mode: searching for '{user_query}'")
                
            search_results = self.kb_tools.knowledge_base_search(user_query)
            
            if self.config.agent.verbose:
                logger.info(f"Non-agentic mode: found {len(search_results)} results")
            
            # Build context from search results
            context_parts = []
            for i, result in enumerate(search_results[:5], 1):  # Top 5 results
                context_parts.append(
                    f"[Document {i}] (ID: {result['doc_id']}, Chunk: {result['chunk_id']})\n{result['text']}\n"
                )
            
            if not context_parts:
                context = "No relevant information found in the knowledge base."
            else:
                context = "\n".join(context_parts)
            
            # Build prompt
            system_prompt = """You are an assistant that answers questions based on provided context from a knowledge base.

IMPORTANT RULES:
1. Only answer based on the provided context
2. Include citations in format [Doc: document_id] 
3. If the context doesn't contain the answer, say so clearly
4. Be accurate and don't make up information"""

            user_prompt = f"""Context from knowledge base:
{context}

User Question: {user_query}

Please answer the question based only on the provided context. Include citations."""

            # Call LLM
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            if stream:
                response_stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=_reasoning_safe_temperature(self.model, self.config.llm.temperature),
                    max_tokens=self.config.llm.max_tokens,
                    stream=True
                )
                
                def response_generator():
                    for chunk in response_stream:
                        if chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content
                
                return response_generator()
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=_reasoning_safe_temperature(self.model, self.config.llm.temperature),
                    max_tokens=self.config.llm.max_tokens,
                    stream=False
                )
                return response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"Error in non-agentic query: {e}")
            error_msg = f"Error processing query: {str(e)}"
            if stream:
                return self._stream_response(error_msg)
            else:
                return error_msg
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")
