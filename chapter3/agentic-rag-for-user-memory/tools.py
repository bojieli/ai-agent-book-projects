"""Tool definitions for the User Memory RAG Agent

This module provides tool definitions and implementations for searching
and retrieving information from indexed conversation memories.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from indexer import MemoryIndexer, SearchResult
from config import IndexConfig


logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """Result from a tool execution"""
    success: bool
    data: Any
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        if self.success:
            return {"status": "success", "data": self.data}
        else:
            return {"status": "error", "error": self.error}


class MemoryTools:
    """Tools for searching and retrieving user memory information"""
    
    def __init__(self, indexer: MemoryIndexer):
        """
        Initialize memory tools
        
        Args:
            indexer: The memory indexer instance
        """
        self.indexer = indexer
        logger.info("Initialized memory tools")
    
    def search_memory(self, 
                     query: str, 
                     top_k: int = 3,
                     filter_test_id: Optional[str] = None) -> ToolResult:
        """
        Search user memory for relevant information
        
        Args:
            query: Natural language search query
            top_k: Number of results to return
            filter_test_id: Optional test ID to filter results
            
        Returns:
            ToolResult with search results
        """
        try:
            # Perform search
            results = self.indexer.search(query, top_k=top_k)
            
            # Filter by test ID if specified
            if filter_test_id:
                results = [r for r in results if r.chunk.test_id == filter_test_id]
            
            # Format results
            formatted_results = []
            for result in results:
                # Extract key information from the chunk
                chunk_info = {
                    "chunk_id": result.chunk_id,
                    "score": round(result.score, 4),
                    "test_id": result.chunk.test_id,
                    "conversation_id": result.chunk.conversation_id,
                    "rounds": f"{result.chunk.start_round}-{result.chunk.end_round}",
                    "metadata": result.chunk.metadata,
                    "content": result.chunk.to_text(),  # FULL content, not truncated
                    "match_type": result.match_type
                }
                formatted_results.append(chunk_info)
            
            logger.info(f"Search query: '{query}' returned {len(formatted_results)} results")
            
            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "total_results": len(formatted_results),
                    "results": formatted_results
                }
            )
            
        except Exception as e:
            logger.error(f"Error in search_memory: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    def get_conversation_context(self,
                                chunk_id: str,
                                context_size: int = 2) -> ToolResult:
        """
        Get surrounding context for a specific chunk
        
        Args:
            chunk_id: The chunk ID to get context for
            context_size: Number of chunks before/after to include
            
        Returns:
            ToolResult with conversation context
        """
        try:
            # Get the target chunk
            if chunk_id not in self.indexer.chunks:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Chunk {chunk_id} not found"
                )
            
            target_chunk = self.indexer.chunks[chunk_id]
            
            # Find related chunks from same conversation
            related_chunks = []
            for cid, chunk in self.indexer.chunks.items():
                if (chunk.conversation_id == target_chunk.conversation_id and 
                    chunk.test_id == target_chunk.test_id):
                    related_chunks.append(chunk)
            
            # Sort by chunk index
            related_chunks.sort(key=lambda x: x.chunk_index)
            
            # Find target index
            target_idx = next(
                (i for i, c in enumerate(related_chunks) if c.chunk_id == chunk_id),
                None
            )
            
            if target_idx is None:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Could not locate chunk in conversation"
                )
            
            # Get context chunks
            start_idx = max(0, target_idx - context_size)
            end_idx = min(len(related_chunks), target_idx + context_size + 1)
            context_chunks = related_chunks[start_idx:end_idx]
            
            # Format result
            context_data = {
                "target_chunk": {
                    "chunk_id": target_chunk.chunk_id,
                    "rounds": f"{target_chunk.start_round}-{target_chunk.end_round}",
                    "content": target_chunk.to_text()
                },
                "context_chunks": []
            }
            
            for chunk in context_chunks:
                if chunk.chunk_id != chunk_id:
                    context_data["context_chunks"].append({
                        "chunk_id": chunk.chunk_id,
                        "rounds": f"{chunk.start_round}-{chunk.end_round}",
                        "position": "before" if chunk.chunk_index < target_chunk.chunk_index else "after",
                        "content": chunk.to_text()
                    })
            
            return ToolResult(
                success=True,
                data=context_data
            )
            
        except Exception as e:
            logger.error(f"Error in get_conversation_context: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    def get_full_conversation(self,
                            conversation_id: str,
                            test_id: str) -> ToolResult:
        """
        Retrieve all chunks from a specific conversation
        
        Args:
            conversation_id: Conversation identifier
            test_id: Test case identifier
            
        Returns:
            ToolResult with full conversation
        """
        try:
            # Find all chunks for this conversation
            conversation_chunks = []
            for chunk_id, chunk in self.indexer.chunks.items():
                if (chunk.conversation_id == conversation_id and 
                    chunk.test_id == test_id):
                    conversation_chunks.append(chunk)
            
            if not conversation_chunks:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"No chunks found for conversation {conversation_id}"
                )
            
            # Sort by chunk index
            conversation_chunks.sort(key=lambda x: x.chunk_index)
            
            # Format result
            conversation_data = {
                "conversation_id": conversation_id,
                "test_id": test_id,
                "total_chunks": len(conversation_chunks),
                "total_rounds": max(c.end_round for c in conversation_chunks),
                "metadata": conversation_chunks[0].metadata if conversation_chunks else {},
                "chunks": []
            }
            
            for chunk in conversation_chunks:
                conversation_data["chunks"].append({
                    "chunk_id": chunk.chunk_id,
                    "chunk_index": chunk.chunk_index,
                    "rounds": f"{chunk.start_round}-{chunk.end_round}",
                    "content": chunk.to_text()
                })
            
            return ToolResult(
                success=True,
                data=conversation_data
            )
            
        except Exception as e:
            logger.error(f"Error in get_full_conversation: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )
    


def get_tool_definitions() -> List[Dict[str, Any]]:
    """
    Get OpenAI function calling tool definitions
    
    Returns:
        List of tool definitions for OpenAI API
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "search_memory",
                "description": "Search user conversation memory for relevant information. Use this to find specific details from past conversations.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language search query describing what information to find"
                        },
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_conversation_context",
                "description": "Get surrounding context for a specific conversation chunk. Use this when you need more context around a search result.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "chunk_id": {
                            "type": "string",
                            "description": "The chunk ID to get context for"
                        },
                        "context_size": {
                            "type": "integer",
                            "description": "Number of chunks before/after to include (default: 2)",
                            "default": 2
                        }
                    },
                    "required": ["chunk_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_full_conversation",
                "description": "Retrieve all chunks from a specific conversation. Use this when you need to review an entire conversation history.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "conversation_id": {
                            "type": "string",
                            "description": "The conversation identifier"
                        },
                        "test_id": {
                            "type": "string",
                            "description": "The test case identifier"
                        }
                    },
                    "required": ["conversation_id", "test_id"]
                }
            }
        }
    ]
