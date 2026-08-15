# coding: utf-8
# Copyright (c) 2025 inclusionAI.

import time
import traceback
from typing import Dict, Any, List

from aworld.config.conf import ContextRuleConfig, ModelConfig
from aworld.core.context.base import Context
from aworld.core.context.processor import CompressionDecision, ContextProcessingResult, MessagesProcessingResult
from aworld.core.context.processor.chunk_utils import ChunkUtils, MessageChunk, MessageType
from aworld.core.context.processor.llm_compressor import LLMCompressor, CompressionType
from aworld.core.context.processor.llmlingua_compressor import LLMLinguaCompressor
from aworld.core.context.processor.truncate_compressor import TruncateCompressor
from aworld.logs.util import Color, color_log, logger
from aworld.models.utils import num_tokens_from_messages, truncate_tokens_from_messages


class PromptProcessor:
    """Agent context processor, processes context according to context_rule configuration"""
    
    def __init__(self, context_rule: ContextRuleConfig, model_config: ModelConfig):
        self.context_rule = context_rule
        self.model_config = model_config
        self.compress_pipeline = None
        self.llmlingua_compressor = None
        self.truncate_compressor = None
        self.chunk_pipeline = None
        self._init_pipelines()
    
    def _init_pipelines(self): 
        """Initialize processing pipelines"""
        # Initialize truncate compressor
        self.truncate_compressor = TruncateCompressor(
            config={},
            llm_config=self.model_config
        )
        
        if self.context_rule and self.context_rule.llm_compression_config and self.context_rule.llm_compression_config.enabled:
            # Initialize message splitting and compression pipeline
            self.chunk_pipeline = ChunkUtils(
                enable_chunking=True,
                preserve_order=True,
                merge_consecutive=True,
            )
            
            # Initialize compression pipeline based on compress_type configuration
            compress_type = self.context_rule.llm_compression_config.compress_type
            
            if compress_type == 'llmlingua':
                # Initialize LLMLingua compressor
                self.llmlingua_compressor = LLMLinguaCompressor(
                    config=getattr(self.context_rule.llm_compression_config, 'llmlingua_config', {}),
                    llm_config=self.context_rule.llm_compression_config.compress_model,
                )
            else:
                # Default to LLM-based compression
                self.compress_pipeline = LLMCompressor(
                    config=getattr(self.context_rule.llm_compression_config, 'llm_config', {}),
                    llm_config=self.context_rule.llm_compression_config.compress_model,
                )
    
    def _get_compression_type(self) -> CompressionType:
        """Get the compression type based on configuration"""
        if (not self.context_rule or 
            not self.context_rule.llm_compression_config or 
            not self.context_rule.llm_compression_config.enabled):
            return CompressionType.LLM_BASED
        
        compress_type = self.context_rule.llm_compression_config.compress_type
        if compress_type == 'llmlingua':
            return CompressionType.LLMLINGUA
        else:
            return CompressionType.LLM_BASED

    def get_max_tokens(self):
        return self.model_config.max_model_len * self.context_rule.optimization_config.max_token_budget_ratio

    def is_out_of_context(self, messages: List[Dict[str, Any]],
                          is_last_message_in_memory: bool) -> bool:
        return self._count_tokens_from_messages(messages) > self.get_max_tokens()

    def _count_tokens_from_messages(self, messages: List[Dict[str, Any]]) -> int:
        """Calculate token count for messages using utils.py method"""
        return num_tokens_from_messages(messages, model=self.model_config.model_type)

    def _count_tokens_from_message(self, msg: Dict[str, Any]) -> int:
        """Calculate token count for single message using utils.py method"""
        # Convert single message to list format for num_tokens_from_messages
        return num_tokens_from_messages([msg], model=self.model_config.model_type)

    def _count_chunk_tokens(self, chunk: MessageChunk) -> int:
        """Calculate token count for a chunk"""
        return num_tokens_from_messages(chunk.messages, model=self.model_config.model_type)
    
    def _count_content_tokens(self, content: str) -> int:
        """Calculate token count for content string"""
        return num_tokens_from_messages(content, model=self.model_config.model_type)

    def _truncate_tokens_from_messages(self, content: str, max_tokens: int, keep_both_sides: bool = False) -> str:
        """Calculate token count for messages using utils.py method"""
        return truncate_tokens_from_messages(content, max_tokens, keep_both_sides, model=self.model_config.model_type)

    def decide_compression_strategy(self, chunk: MessageChunk) -> CompressionDecision:
        """
        Decide compression strategy based on chunk token length
        
        Args:
            chunk: Message chunk to analyze
            
        Returns:
            CompressionDecision with compression strategy
        """
        compression_type = self._get_compression_type()
        
        if (not self.context_rule or 
            not self.context_rule.llm_compression_config or 
            not self.context_rule.llm_compression_config.enabled):
            return CompressionDecision(
                should_compress=False,
                compression_type=compression_type,
                reason="Compression disabled in config",
                token_count=0
            )
        
        token_count = self._count_chunk_tokens(chunk)
        trigger_compress_length = self.context_rule.llm_compression_config.trigger_compress_token_length
        
        # No compression needed
        if token_count < trigger_compress_length:
            return CompressionDecision(
                should_compress=False,
                compression_type=compression_type,
                reason=f"Token count {token_count} below threshold {trigger_compress_length}",
                token_count=token_count
            )
        
        # Use configured compression for content above threshold
        else:
            return CompressionDecision(
                should_compress=True,
                compression_type=compression_type,
                reason=f"Token count {token_count} exceeds threshold {trigger_compress_length}",
                token_count=token_count
            )

    def decide_content_compression_strategy(self, content: str) -> CompressionDecision:
        compression_type = self._get_compression_type()
        
        if (not self.context_rule or 
            not self.context_rule.llm_compression_config or 
            not self.context_rule.llm_compression_config.enabled):
            return CompressionDecision(
                should_compress=False,
                compression_type=compression_type,
                reason="Compression disabled in config",
                token_count=0
            )
        
        token_count = self._count_content_tokens(content)
        trigger_compress_length = self.context_rule.llm_compression_config.trigger_compress_token_length
        
        # No compression needed
        if token_count < trigger_compress_length:
            return CompressionDecision(
                should_compress=False,
                compression_type=compression_type,
                reason=f"Token count {token_count} below threshold {trigger_compress_length}",
                token_count=token_count
            )
        
        # Use configured compression for content above threshold
        else:
            return CompressionDecision(
                should_compress=True,
                compression_type=compression_type,
                reason=f"Token count {token_count} exceeds threshold {trigger_compress_length}",
                token_count=token_count
            )

    def should_compress_conversation(self, messages: List[Dict[str, Any]]) -> bool:
        """Determine whether conversation compression is needed (legacy method for compatibility)"""
        if (not self.context_rule or 
            not self.context_rule.llm_compression_config or 
            not self.context_rule.llm_compression_config.enabled):
            return False
        
        # Create temporary chunk for decision
        temp_chunk = MessageChunk(
            message_type=MessageType.TEXT,
            messages=messages,
            metadata={}
        )
        
        decision = self.decide_compression_strategy(temp_chunk)
        return decision.should_compress
    
    def should_compress_tool_result(self, result: str) -> bool:
        """Determine whether tool result compression is needed (legacy method for compatibility)"""
        if (not self.context_rule or 
            not self.context_rule.llm_compression_config or 
            not self.context_rule.llm_compression_config.enabled):
            return False
        
        decision = self.decide_content_compression_strategy(result)
        return decision.should_compress
    
    def process_message_chunks(self, 
                              chunks: List[MessageChunk], 
                              base_metadata: Dict[str, Any] = None) -> List[MessageChunk]:
        processed_chunks = []
        
        for chunk in chunks:
            try:
                if chunk.message_type == MessageType.TEXT:
                    # Process text message chunks
                    processed_chunk = self._process_text_chunk(chunk, base_metadata)
                elif chunk.message_type == MessageType.TOOL:
                    # Process tool message chunks
                    processed_chunk = self._process_tool_chunk(chunk, base_metadata)
                else:
                    # Unknown type, keep as is
                    processed_chunk = chunk
                    logger.warning(f"Unknown message chunk type: {chunk.message_type}")
                
                processed_chunks.append(processed_chunk)
                
            except Exception as e:
                logger.error(f"Processing message chunk failed: {traceback.format_exc()}")
                # Keep original chunk on failure
                processed_chunks.append(chunk)
        
        return processed_chunks
    
    def _process_text_chunk(self, 
                           chunk: MessageChunk, 
                           base_metadata: Dict[str, Any] = None) -> MessageChunk:
        decision = self.decide_compression_strategy(chunk)
        
        if not decision.should_compress:
            logger.debug(f"Skipping text chunk compression: {decision.reason}")
            return chunk
        
        try:
            processed_messages = []
            
            for message in chunk.messages:
                content = message.get("content", "")
                if not content or not isinstance(content, str):
                    processed_messages.append(message)
                    continue
                
                logger.info(f'Processing text chunk with LLM compression '
                            f'(tokens: {decision.token_count}, reason: {decision.reason})')
                
                # Use LLM compression
                compression_result = self.compress_pipeline.compress(content)
                
                # Create processed message
                processed_message = message.copy()
                processed_message["content"] = compression_result.compressed_content
                processed_messages.append(processed_message)
            
            # Update chunk metadata
            updated_metadata = chunk.metadata.copy()
            updated_metadata.update({
                "processed": True,
                "compression_applied": True,
                "compression_type": "llm_based",
                "compression_reason": decision.reason,
                "original_token_count": decision.token_count,
                "processing_method": "llm_compression",
                "original_message_count": len(chunk.messages),
                "processed_message_count": len(processed_messages)
            })
            
            return MessageChunk(
                message_type=chunk.message_type,
                messages=processed_messages,
                metadata=updated_metadata
            )
            
            return chunk
            
        except Exception as e:
            logger.warning(f"Text chunk compression failed: {traceback.format_exc()}")
            return chunk
    
    def _process_tool_chunk(self, 
                           chunk: MessageChunk, 
                           base_metadata: Dict[str, Any] = None) -> MessageChunk:
        """Process tool message chunks with LLM compression"""
        try:
            processed_messages = []
            
            for message in chunk.messages:
                content = message.get("content", "")
                
                # Decide compression strategy for this content
                decision = self.decide_content_compression_strategy(content)
                
                if decision.should_compress:
                    logger.info(f'Processing tool chunk with LLM compression '
                              f'(tokens: {decision.token_count}, reason: {decision.reason})')
                    
                    # Use LLM compression
                    compression_result = self.compress_pipeline.compress(
                        content,
                        # metadata={
                        #     "tool_name": message.get("name", "unknown_tool"),
                        #     "message_role": message.get("role", "tool"),
                        #     "content_token_count": decision.token_count,
                        #     "compression_reason": decision.reason
                        # },
                        compression_type=CompressionType.LLM_BASED
                    )
                    
                    # Create processed message
                    processed_message = message.copy()
                    processed_message["content"] = compression_result.compressed_content
                    processed_messages.append(processed_message)
                else:
                    # Messages that don't need compression are kept as is
                    logger.debug(f"Skipping tool content compression: {decision.reason}")
                    processed_messages.append(message)
            
            # Update chunk metadata with compression info
            updated_metadata = chunk.metadata.copy()
            updated_metadata.update({
                "processed": True,
                "tool_compression_applied": True,
                "processing_method": "llm_compression",
                "original_message_count": len(chunk.messages),
                "processed_message_count": len(processed_messages)
            })
            
            return MessageChunk(
                message_type=chunk.message_type,
                messages=processed_messages,
                metadata=updated_metadata
            )
            
        except Exception as e:
            logger.warning(f"Tool chunk compression failed: {traceback.format_exc()}")
            return chunk

    def truncate_messages(self, messages: List[Dict[str, Any]]) -> MessagesProcessingResult:
        """Truncate messages using TruncateCompressor"""
        max_tokens = self.get_max_tokens()
        optimization_enabled = self.context_rule.optimization_config.enabled if self.context_rule else True
        
        return self.truncate_compressor.truncate_messages(
            messages=messages,
            max_tokens=max_tokens,
            optimization_enabled=optimization_enabled
        )

    def compress_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if (not self.context_rule or 
            not self.context_rule.llm_compression_config or 
            not self.context_rule.llm_compression_config.enabled):
            return messages
        
        compression_type = self._get_compression_type()
        
        if compression_type == CompressionType.LLMLINGUA and self.llmlingua_compressor:
            # Use LLMLingua compression directly on messages
            logger.info("Using LLMLingua compression for messages")
            
            try:
                compression_result = self.llmlingua_compressor.compress_messages(messages)
                
                # Extract compressed messages from metadata
                compressed_messages = compression_result.metadata.get("compressed_messages", messages)
                
                logger.info(f"LLMLingua compression completed. "
                          f"Original: {len(messages)} messages, "
                          f"Compressed: {len(compressed_messages)} messages, "
                          f"Compression ratio: {compression_result.compression_ratio:.2f}")
                
                return compressed_messages
                
            except Exception as e:
                logger.error(f"LLMLingua compression failed: {e}")
                return messages
        
        elif compression_type == CompressionType.LLM_BASED and self.compress_pipeline:
            # Use original chunk-based LLM compression
            logger.info("Using LLM-based compression for messages")
            
            # 1. Re-split processed messages
            final_chunk_result = self.chunk_pipeline.split_messages(messages)

            # 2. Process each chunk
            processed_chunks = self.process_message_chunks(final_chunk_result.chunks)
            
            # 3. Re-merge messages
            return self.chunk_pipeline.merge_chunks(processed_chunks)
        
        else:
            # No appropriate compressor available
            logger.warning(f"No compressor available for type {compression_type}, returning original messages")
            return messages

    def process_messages(self, messages: List[Dict[str, Any]], context: Context) -> ContextProcessingResult:
        """Process complete context, return processing results and statistics"""
        start_time = time.time()
        if not self.context_rule.optimization_config.enabled:
            return ContextProcessingResult(
                processed_messages=messages,
                processed_tool_results=None,
                statistics={
                    "total_processing_time": 0,
                    "original_message_count": len(messages),
                },
            )

        # 1. Content compression
        compressed_messages = self.compress_messages(messages)
        
        # 2. Content length limit
        truncated_result = self.truncate_messages(compressed_messages)
        truncated_messages = truncated_result.processed_messages
        
        total_time = time.time() - start_time

        color_log(f"\nContext processing statistics: "
                   f"\nOriginal message count={truncated_result.original_messages_len}"
                   f"\nProcessed message count={truncated_result.processing_messaged_len}"
                   f"\nMax context length max_context_len={self.get_max_tokens()} = {self.model_config.max_model_len} * {self.context_rule.optimization_config.max_token_budget_ratio}"
                   f"\nOriginal token count={truncated_result.original_token_len}"
                   f"\nProcessed token count={truncated_result.processing_token_len}"
                   f"\nTruncation processing time={truncated_result.processing_time:.3f}s"
                   f"\nTotal processing time={total_time:.3f}s"
                   f"\nMethod used={truncated_result.method_used}"
                   f"\norigin_messages={num_tokens_from_messages(messages)}"
                   f"\ntruncated_messages={num_tokens_from_messages(truncated_messages)}",
                   color=Color.pink,)

        return ContextProcessingResult(
            processed_messages=truncated_messages,
            processed_tool_results=None,
            statistics={
                "total_processing_time": total_time,
                "original_message_count": len(messages),
                "truncated_message_count": len(truncated_messages),
            },
        ) 

