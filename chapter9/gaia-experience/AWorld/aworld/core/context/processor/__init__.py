# coding: utf-8
# Copyright (c) 2025 inclusionAI.


from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List


class MessageType(Enum):
    """Message type enum"""
    TEXT = "text"  # system, user, assistant messages
    TOOL = "tool"  # tool messages
    UNKNOWN = "unknown"


@dataclass
class MessageChunk:
    """Message chunk containing messages of the same type"""
    message_type: MessageType
    messages: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    
    def __len__(self):
        return len(self.messages)
    
    def is_empty(self):
        return len(self.messages) == 0

@dataclass
class ChunkResult:
    """Chunking result"""
    chunks: List[MessageChunk]
    total_messages: int
    processing_time: float
    metadata: Dict[str, Any]


class CompressionType(Enum):
    LLM_BASED = "llm_based"
    LLMLINGUA = "llmlingua"

@dataclass
class CompressionResult:
    """Compression result data structure"""
    original_content: str
    compressed_content: str
    compression_ratio: float
    metadata: Dict[str, Any]
    compression_type: CompressionType


@dataclass
class MessagesProcessingResult:
    """Processing result"""
    original_token_len: int
    processing_token_len: int
    original_messages_len: int
    processing_messaged_len: int
    processing_time: float
    method_used: str
    processed_messages: List[Dict[str, Any]]

@dataclass
class ContextProcessingResult:
    """Context processing result"""
    processed_messages: List[Dict[str, Any]]
    processed_tool_results: List[str]
    statistics: Dict[str, Any]
    chunk_info: Dict[str, Any] = None

@dataclass
class CompressionDecision:
    """Compression decision result"""
    should_compress: bool
    compression_type: CompressionType
    reason: str
    token_count: int
