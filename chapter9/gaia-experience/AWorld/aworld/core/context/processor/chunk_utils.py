import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Union

from aworld.core.context.processor import MessageChunk, ChunkResult, MessageType

logger = logging.getLogger(__name__)


class ChunkUtils:
    
    def __init__(self, 
                 enable_chunking: bool = False,
                 preserve_order: bool = True,
                 merge_consecutive: bool = True,
                 max_chunk_size: int = None,
                 split_by_tool_name: bool = False):
        
        # Chunker configuration
        self.enable_chunking = enable_chunking
        self.preserve_order = preserve_order
        self.merge_consecutive = merge_consecutive
        self.max_chunk_size = max_chunk_size
        self.split_by_tool_name = split_by_tool_name
        
        # Statistics
        self.stats = {
            # Chunking statistics
            "chunking": {
                "total_processed": 0,
                "total_chunks_created": 0,
                "processing_time": 0.0
            }
        }

    def _process_chunking(self, messages: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """Process chunking logic"""
        # First chunk
        chunk_result = self.split_messages(messages, kwargs.get('metadata', {}))
        
        # Then merge back to message list
        merged_messages = self.merge_chunks(chunk_result.chunks, 
                                          kwargs.get('preserve_type_order', True))
        
        return merged_messages

    def classify_message(self, message: Dict[str, Any]) -> MessageType:
        """
        Classify a single message
        
        Args:
            message: OpenAI format message
            
        Returns:
            Message type
        """
        role = message.get("role", "")
        
        if role in ["system", "user", "assistant"]:
            return MessageType.TEXT
        elif role == "tool":
            return MessageType.TOOL
        else:
            logger.warning(f"Unknown message role: {role}")
            return MessageType.UNKNOWN

    def split_messages(self, 
                      messages: List[Dict[str, Any]], 
                      metadata: Dict[str, Any] = None) -> ChunkResult:
        """
        Split message list into chunks by type, and merge messages of the same type into strings
        
        Args:
            messages: OpenAI format message list
            metadata: Metadata
            
        Returns:
            Chunking result
        """
        start_time = time.time()
        
        if not messages:
            return ChunkResult(
                chunks=[],
                total_messages=0,
                processing_time=0.0,
                metadata=metadata or {}
            )
        
        chunks = []
        current_chunk_type = None
        current_chunk_messages = []
        
        for i, message in enumerate(messages):
            msg_type = self.classify_message(message)
            
            # If it's a new type or not merging consecutive messages
            if (current_chunk_type != msg_type or 
                not self.merge_consecutive):
                
                # Save current chunk (if has content)
                if current_chunk_messages:
                    chunk_metadata = (metadata or {}).copy()
                    chunk_metadata.update({
                        "chunk_index": len(chunks),
                        "start_message_index": i - len(current_chunk_messages),
                        "end_message_index": i - 1,
                        "message_count": len(current_chunk_messages),
                        "original_messages": current_chunk_messages.copy()
                    })
                    
                    # Merge messages into strings based on message type
                    if current_chunk_type == MessageType.TEXT:
                        merged_content = self._messages_to_string(current_chunk_messages)
                        merged_message = {
                            "role": "merged_text",
                            "content": merged_content,
                            "original_count": len(current_chunk_messages)
                        }
                        chunk_messages = [merged_message]
                    elif current_chunk_type == MessageType.TOOL:
                        merged_content = self._tool_messages_to_string(current_chunk_messages)
                        merged_message = {
                            "role": "merged_tool",
                            "content": merged_content,
                            "original_count": len(current_chunk_messages)
                        }
                        chunk_messages = [merged_message]
                    else:
                        # Unknown type keeps as is
                        chunk_messages = current_chunk_messages.copy()
                    
                    chunks.append(MessageChunk(
                        message_type=current_chunk_type,
                        messages=chunk_messages,
                        metadata=chunk_metadata
                    ))
                
                # Start new chunk
                current_chunk_type = msg_type
                current_chunk_messages = [message]
            else:
                # Add to current chunk
                current_chunk_messages.append(message)
        
        # Process the last chunk
        if current_chunk_messages:
            chunk_metadata = (metadata or {}).copy()
            chunk_metadata.update({
                "chunk_index": len(chunks),
                "start_message_index": len(messages) - len(current_chunk_messages),
                "end_message_index": len(messages) - 1,
                "message_count": len(current_chunk_messages),
                "original_messages": current_chunk_messages.copy()
            })
            
            # Merge messages into strings based on message type
            if current_chunk_type == MessageType.TEXT:
                merged_content = self._messages_to_string(current_chunk_messages)
                merged_message = {
                    "role": "merged_text",
                    "content": merged_content,
                    "original_count": len(current_chunk_messages)
                }
                chunk_messages = [merged_message]
            elif current_chunk_type == MessageType.TOOL:
                merged_content = self._tool_messages_to_string(current_chunk_messages)
                merged_message = {
                    "role": "merged_tool",
                    "content": merged_content,
                    "original_count": len(current_chunk_messages)
                }
                chunk_messages = [merged_message]
            else:
                chunk_messages = current_chunk_messages.copy()
            
            chunks.append(MessageChunk(
                message_type=current_chunk_type,
                messages=chunk_messages,
                metadata=chunk_metadata
            ))
        
        processing_time = time.time() - start_time
        
        # Update statistics
        self.stats["chunking"]["total_processed"] += len(messages)
        self.stats["chunking"]["total_chunks_created"] += len(chunks)
        self.stats["chunking"]["processing_time"] += processing_time
        
        # Build result metadata
        result_metadata = (metadata or {}).copy()
        result_metadata.update({
            "chunk_count": len(chunks),
            "text_chunks": sum(1 for chunk in chunks if chunk.message_type == MessageType.TEXT),
            "tool_chunks": sum(1 for chunk in chunks if chunk.message_type == MessageType.TOOL),
            "unknown_chunks": sum(1 for chunk in chunks if chunk.message_type == MessageType.UNKNOWN),
            "preserve_order": self.preserve_order,
            "merge_consecutive": self.merge_consecutive,
            "processing_time": processing_time,
            "string_merge_applied": True
        })
        
        logger.debug(f"Message splitting completed: {len(messages)} messages -> {len(chunks)} chunks (string merge applied)")
        
        return ChunkResult(
            chunks=chunks,
            total_messages=len(messages),
            processing_time=processing_time,
            metadata=result_metadata
        )

    def merge_chunks(self, 
                    chunks: List[MessageChunk], 
                    preserve_type_order: bool = True) -> List[Dict[str, Any]]:
        """
        Merge processed chunks back to message list, and split string format messages back to multiple messages
        
        Args:
            chunks: Message chunk list
            preserve_type_order: Whether to preserve type order
            
        Returns:
            Merged message list
        """
        if not chunks:
            return []
        
        if preserve_type_order and self.preserve_order:
            # Merge in original order
            sorted_chunks = sorted(chunks, key=lambda x: x.metadata.get("chunk_index", 0))
        else:
            # Merge by type groups (text first, then tools)
            text_chunks = [chunk for chunk in chunks if chunk.message_type == MessageType.TEXT]
            tool_chunks = [chunk for chunk in chunks if chunk.message_type == MessageType.TOOL]
            unknown_chunks = [chunk for chunk in chunks if chunk.message_type == MessageType.UNKNOWN]
            sorted_chunks = text_chunks + tool_chunks + unknown_chunks
        
        merged_messages = []
        for chunk in sorted_chunks:
            chunk_messages = []
            
            for message in chunk.messages:
                # Check if it's a merged message that needs splitting
                if message.get("role") == "merged_text":
                    # This is a merged TEXT type message that needs splitting
                    merged_content = message.get("content", "")
                    original_messages = chunk.metadata.get("original_messages", [])
                    
                    if original_messages:
                        split_messages = self._string_to_messages(merged_content, original_messages)
                        chunk_messages.extend(split_messages)
                    else:
                        split_messages = self._string_to_messages(merged_content, [])
                        chunk_messages.extend(split_messages)
                        
                elif message.get("role") == "merged_tool":
                    # This is a merged TOOL type message that needs splitting
                    merged_content = message.get("content", "")
                    original_messages = chunk.metadata.get("original_messages", [])
                    
                    if original_messages:
                        split_messages = self._string_to_tool_messages(merged_content, original_messages)
                        chunk_messages.extend(split_messages)
                    else:
                        split_messages = self._string_to_tool_messages(merged_content, "")
                        chunk_messages.extend(split_messages)
                        
                else:
                    # Regular message added directly
                    chunk_messages.append(message)
            
            merged_messages.extend(chunk_messages)
        
        return merged_messages

    # Message conversion methods
    @staticmethod
    def _messages_to_string(messages: List[Dict[str, str]]) -> str:
        """Convert OpenAI message format to string"""
        content_parts = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            content_parts.append(f"[{role.upper()}]: {content}")
        return "\n".join(content_parts)
    
    @staticmethod
    def _string_to_messages(content: str, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert string to OpenAI message format"""
        # Restore all tool_calls
        tool_calls = []
        if messages:
            for msg in messages:
                if msg.get("role") == "assistant" and msg.get("tool_calls") is not None:
                    tool_calls += msg["tool_calls"]

        result_messages = []
        lines = content.split('\n')
        current_role = 'user'
        current_content = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('[') and ']:' in line:
                # Save previous message
                if current_content:
                    result_messages.append({
                        'role': current_role,
                        'content': '\n'.join(current_content).strip()
                    })
                    current_content = []
                
                # Parse new role
                role_end = line.find(']:')
                role = line[1:role_end].lower()
                if role in ['system', 'user', 'assistant']:
                    current_role = role
                    content_part = line[role_end + 2:].strip()
                    if content_part:
                        current_content.append(content_part)
                else:
                    current_content.append(line)
            else:
                current_content.append(line)

        # Save last message
        if current_content:
            result_messages.append({
                'role': current_role,
                'content': '\n'.join(current_content).strip(),
            })
        
        final_messages = result_messages if result_messages else [{'role': 'user', 'content': content}]

        # Add tool_calls results
        if tool_calls and len(tool_calls) > 0:
            tool_call_chunk = {
                'role': 'assistant',
                'content': None,
                'tool_calls': tool_calls
            }
            final_messages.append(tool_call_chunk)

        return final_messages

    def _tool_messages_to_string(self, messages: List[Dict[str, str]]) -> str:
        """Convert tool message format to string"""
        content_parts = []
        for msg in messages:
            role = msg.get('role', 'tool')
            content = msg.get('content', '')
            tool_call_id = msg.get('tool_call_id', '')
            name = msg.get('name', '')
    
            if role == 'tool':
                header = f"[TOOL:{name}:{tool_call_id}]"
            else:
                header = f"[{role.upper()}]"
    
            content_parts.append(f"{header}: {content}")
        return "\n".join(content_parts)
    
    def _string_to_tool_messages(self, content: str, original_prompt: Union[str, List[Dict[str, str]]]) -> List[Dict[str, str]]:
        """Convert string to tool message format"""
        messages = []
        lines = content.split('\n')
        current_role = 'tool'
        current_content = []
        current_tool_call_id = ''
        current_name = ''
    
        for line in lines:
            line = line.strip()
            if line.startswith('[') and ']:' in line:
                # Save previous message
                if current_content:
                    msg = {
                        'role': current_role,
                        'content': '\n'.join(current_content).strip()
                    }
                    if current_role == 'tool':
                        if current_tool_call_id:
                            msg['tool_call_id'] = current_tool_call_id
                        if current_name:
                            msg['name'] = current_name
                    messages.append(msg)
                    current_content = []
    
                # Parse new role and tool information
                role_end = line.find(']:')
                role_part = line[1:role_end]
                content_part = line[role_end + 2:].strip()
    
                if role_part.startswith('TOOL:'):
                    # Parse tool message format: [TOOL:name:tool_call_id]
                    current_role = 'tool'
                    tool_parts = role_part.split(':')
                    if len(tool_parts) >= 2:
                        current_name = tool_parts[1]
                    if len(tool_parts) >= 3:
                        current_tool_call_id = tool_parts[2]
                else:
                    current_role = role_part.lower()
                    current_tool_call_id = ''
                    current_name = ''
    
                if content_part:
                    current_content.append(content_part)
            else:
                current_content.append(line)
    
        # Save last message
        if current_content:
            msg = {
                'role': current_role,
                'content': '\n'.join(current_content).strip()
            }
            if current_role == 'tool':
                if current_tool_call_id:
                    msg['tool_call_id'] = current_tool_call_id
                if current_name:
                    msg['name'] = current_name
            messages.append(msg)
    
        # If no messages parsed, return original format
        if not messages and isinstance(original_prompt, list):
            return original_prompt
        elif not messages:
            return [{'role': 'tool', 'content': content}]
    
        return messages
