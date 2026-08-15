# coding: utf-8
# Copyright (c) 2025 inclusionAI.

import time
import logging
from typing import Any, Dict, List

from aworld.config.conf import ModelConfig
from aworld.core.context.processor import CompressionResult, CompressionType, MessagesProcessingResult
from aworld.core.context.processor.base_compressor import BaseCompressor
from aworld.logs.util import Color, color_log
from aworld.models.utils import num_tokens_from_messages
from aworld.utils import import_package

logger = logging.getLogger(__name__)


class TruncateCompressor(BaseCompressor):
    """
    Truncate messages compressor for content length management
    """

    def __init__(self, config: Dict[str, Any] = None, llm_config: ModelConfig = None):
        super().__init__(config, llm_config)
        self.model_type = llm_config.model_type if llm_config else "gpt-3.5-turbo"
        self._init_tokenizer()

    def _init_tokenizer(self):
        """Initialize tokenizer for text truncation"""
        try:
            import_package("tiktoken")
            import tiktoken
            
            if self.model_type.lower() == "qwen":
                from aworld.models.qwen_tokenizer import qwen_tokenizer
                self.tokenizer = qwen_tokenizer
            elif self.model_type.lower() == "openai":
                from aworld.models.openai_tokenizer import openai_tokenizer
                self.tokenizer = openai_tokenizer
            else:
                try:
                    self.encoding = tiktoken.encoding_for_model(self.model_type)
                    self.tokenizer = None  # Use tiktoken directly
                except KeyError:
                    logger.warning(f"{self.model_type} model not found. Using cl100k_base encoding.")
                    self.encoding = tiktoken.get_encoding("cl100k_base")
                    self.tokenizer = None
        except ImportError:
            logger.error("tiktoken not available, text truncation may not work properly")
            self.tokenizer = None
            self.encoding = None

    def _count_tokens_from_messages(self, messages: List[Dict[str, Any]]) -> int:
        """Calculate token count for messages using utils.py method"""
        return num_tokens_from_messages(messages, model=self.model_type)

    def _count_tokens_from_message(self, msg: Dict[str, Any]) -> int:
        """Calculate token count for single message using utils.py method"""
        # Convert single message to list format for num_tokens_from_messages
        return num_tokens_from_messages([msg], model=self.model_type)

    def _truncate_text(self, text: str, max_tokens: int, keep_both_sides: bool = False) -> str:
        """Truncate text content using appropriate tokenizer"""
        if not text:
            return text
        
        # Ensure max_tokens is an integer
        max_tokens = int(max_tokens)
        if max_tokens <= 0:
            return ""
            
        try:
            if self.tokenizer:
                # Use custom tokenizer (qwen/openai)
                return self.tokenizer.truncate(text, max_tokens, keep_both_sides=keep_both_sides)
            elif self.encoding:
                # Use tiktoken encoding directly
                tokens = self.encoding.encode(text)
                if len(tokens) <= max_tokens:
                    return text
                
                if keep_both_sides:
                    ellipsis = "..."
                    ellipsis_tokens = self.encoding.encode(ellipsis)
                    ellipsis_len = len(ellipsis_tokens)
                    available = max_tokens - ellipsis_len
                    if available <= 0:
                        # Not enough space for ellipsis
                        truncated_tokens = tokens[:max_tokens]
                    else:
                        left_len = int(available // 2)
                        right_len = int(available - left_len)
                        truncated_tokens = tokens[:left_len] + ellipsis_tokens + tokens[-right_len:]
                else:
                    truncated_tokens = tokens[:max_tokens]
                
                return self.encoding.decode(truncated_tokens)
            else:
                # Fallback: simple character truncation
                logger.warning("No tokenizer available, using character-based truncation")
                target_len = max_tokens * 4  # Rough estimate: 1 token = 4 chars
                target_len = int(target_len)
                
                if len(text) <= target_len:
                    return text
                
                if keep_both_sides:
                    ellipsis = "..."
                    available = target_len - len(ellipsis)
                    if available <= 0:
                        return text[:target_len]
                    left_len = int(available // 2)
                    right_len = int(available - left_len)
                    return text[:left_len] + ellipsis + text[-right_len:]
                else:
                    return text[:target_len]
        except Exception as e:
            logger.error(f"Text truncation failed: {e}")
            return text

    def _truncate_message(self, msg: Dict[str, Any], max_tokens: int, keep_both_sides: bool = False):
        """Truncate single message content"""
        # Ensure max_tokens is an integer
        max_tokens = int(max_tokens)
        
        content = msg.get("content", "")
        if isinstance(content, str):
            truncated_content = self._truncate_text(content, max_tokens, keep_both_sides)
        else:
            # Handle complex content formats
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("text"):
                        text_parts.append(item["text"])
                    elif isinstance(item, str):
                        text_parts.append(item)
                if not text_parts:
                    return None
                text = '\n'.join(text_parts)
            else:
                text = str(content)
            truncated_content = self._truncate_text(text, max_tokens, keep_both_sides)
        
        new_msg = msg.copy()
        new_msg["content"] = truncated_content
        return new_msg

    def is_out_of_context(self, messages: List[Dict[str, Any]], max_tokens: int) -> bool:
        """Check if messages exceed token limit"""
        max_tokens = int(max_tokens)
        return self._count_tokens_from_messages(messages) > max_tokens

    def truncate_messages(self, messages: List[Dict[str, Any]], max_tokens: int, 
                         optimization_enabled: bool = True) -> MessagesProcessingResult:
        """Truncate messages based on _truncate_input_messages_roughly logic"""
        start_time = time.time()
        original_messages_len = len(messages)
        original_token_len = self._count_tokens_from_messages(messages)
        
        # Ensure max_tokens is an integer
        max_tokens = int(max_tokens)
        
        if not optimization_enabled:
            processing_time = time.time() - start_time
            return MessagesProcessingResult(
                original_token_len=original_token_len,
                processing_token_len=original_token_len,
                original_messages_len=original_messages_len,
                processing_messaged_len=original_messages_len,
                processing_time=processing_time,
                method_used="no_optimization",
                processed_messages=messages
            )
        
        if not self.is_out_of_context(messages=messages, max_tokens=max_tokens):
            processing_time = time.time() - start_time
            return MessagesProcessingResult(
                original_token_len=original_token_len,
                processing_token_len=original_token_len,
                original_messages_len=original_messages_len,
                processing_messaged_len=original_messages_len,
                processing_time=processing_time,
                method_used="within_context_limit",
                processed_messages=messages
            )

        # Group messages by conversation turns
        turns = []
        for m in messages:
            if m.get("role") == "system":
                continue
            elif m.get("role") == "user":
                turns.append([m])
            else:
                if turns:
                    turns[-1].append(m)
                else:
                    raise Exception('The input messages (excluding the system message) must start with a user message.')

        # Process system messages
        if messages and messages[0].get("role") == "system":
            sys_msg = messages[0]
            available_token = max_tokens - self._count_tokens_from_message(sys_msg)
        else:
            sys_msg = None
            available_token = max_tokens
        
        # Process messages from back to front, keep the latest conversations
        token_cnt = 0
        new_messages = []
        user_message_count = 0
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].get("role") == "system":
                continue
            
            cur_token_cnt = self._count_tokens_from_message(messages[i])
            if cur_token_cnt <= available_token:
                if messages[i].get("role") == "user":
                    user_message_count += 1
                new_messages = [messages[i]] + new_messages
                available_token -= cur_token_cnt
            else:
                # Try to truncate message
                if (messages[i].get("role") == "user"):
                    # Truncate user message (not the last one)
                    # color_log(f"to truncate message {messages[i]}", color=Color.pink)
                    _msg = self._truncate_message(messages[i], max_tokens=int(available_token))
                    # color_log(f"truncated message {messages[i]}, {_msg}", color=Color.pink)
                    if _msg:
                        new_messages = [_msg] + new_messages
                    break
                elif messages[i].get("role") == "function" or messages[i].get("role") == "assistant" or messages[i].get("role") == "system":
                    # Truncate function message, keep both ends
                    _msg = self._truncate_message(messages[i], max_tokens=int(available_token), keep_both_sides=True)
                    logger.debug(f"truncated message {messages[i]}, {_msg}")
                    if _msg:
                        new_messages = [_msg] + new_messages
                    # Edge case: if the last message is a very long tool message, it might end up with only system+tool without user message, which will cause LLM call to fail
                    elif user_message_count == 0:
                        continue
                    else:
                        break
                else:
                    # Cannot truncate, record token count and exit
                    token_cnt = (max_tokens - available_token) + cur_token_cnt
                    break
        
        # Re-add system message
        if sys_msg is not None:
            new_messages = [sys_msg] + new_messages
        
        # Calculate processed statistics
        processing_time = time.time() - start_time
        processing_token_len = self._count_tokens_from_messages(new_messages)
        processing_messaged_len = len(new_messages)
        
        return MessagesProcessingResult(
            original_token_len=original_token_len,
            processing_token_len=processing_token_len,
            original_messages_len=original_messages_len,
            processing_messaged_len=processing_messaged_len,
            processing_time=processing_time,
            method_used="truncate_messages",
            processed_messages=new_messages
        )

    def compress(self, content: str) -> CompressionResult:
        """
        Compress content by truncating it (for compatibility with BaseCompressor interface)
        """
        # This is a simple truncation, not actual compression
        # For consistency with other compressors, we provide this method
        original_content = content
        
        # Use a reasonable default max_tokens for single content truncation
        max_tokens = self.config.get("max_tokens", 2000)
        
        try:
            truncated_content = self._truncate_text(content, max_tokens, False)
            compression_ratio = len(truncated_content) / len(original_content) if original_content else 1.0
            
            return CompressionResult(
                original_content=original_content,
                compressed_content=truncated_content,
                compression_ratio=compression_ratio,
                metadata={"method": "truncation", "max_tokens": max_tokens},
                compression_type=CompressionType.LLM_BASED  # Default type
            )
            
        except Exception as e:
            logger.error(f"Truncation failed: {e}")
            return CompressionResult(
                original_content=original_content,
                compressed_content=content,
                compression_ratio=1.0,
                metadata={"error": str(e)},
                compression_type=CompressionType.LLM_BASED
            )

    def compress_messages(self, messages: List[Dict[str, Any]]) -> CompressionResult:
        """
        Compress messages by truncating them (for compatibility with BaseCompressor interface)
        """
        if not messages:
            return CompressionResult(
                original_content="[]",
                compressed_content="[]",
                compression_ratio=1.0,
                metadata={},
                compression_type=CompressionType.LLM_BASED
            )
        
        original_content = str(messages)
        max_tokens = self.config.get("max_tokens", 4000)
        
        try:
            result = self.truncate_messages(messages, max_tokens, optimization_enabled=True)
            
            compressed_content = str(result.processed_messages)
            compression_ratio = result.processing_token_len / result.original_token_len if result.original_token_len > 0 else 1.0
            
            return CompressionResult(
                original_content=original_content,
                compressed_content=compressed_content,
                compression_ratio=compression_ratio,
                metadata={
                    "method": "truncation",
                    "max_tokens": max_tokens,
                    "truncated_messages": result.processed_messages,
                    "original_message_count": result.original_messages_len,
                    "processed_message_count": result.processing_messaged_len,
                    "method_used": result.method_used
                },
                compression_type=CompressionType.LLM_BASED
            )
            
        except Exception as e:
            logger.error(f"Message truncation failed: {e}")
            return CompressionResult(
                original_content=original_content,
                compressed_content=original_content,
                compression_ratio=1.0,
                metadata={"error": str(e)},
                compression_type=CompressionType.LLM_BASED
            )

    def compress_batch(self, contents: List[str]) -> List[CompressionResult]:
        """Compress multiple contents in batch"""
        results = []
        for content in contents:
            result = self.compress(content)
            results.append(result)
        return results
