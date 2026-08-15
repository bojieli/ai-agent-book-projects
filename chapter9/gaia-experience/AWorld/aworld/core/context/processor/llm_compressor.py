import asyncio
import logging
import re
from abc import ABC, abstractmethod
import traceback
from typing import Any, Dict, List

from aworld.config.conf import ModelConfig
from aworld.core.context.processor import CompressionResult, CompressionType
from aworld.core.context.processor.base_compressor import BaseCompressor
from aworld.models.llm import get_llm_model
from aworld.config import ConfigDict
                
logger = logging.getLogger(__name__)

class LLMCompressor(BaseCompressor):
    """LLM-based prompt compressor"""
    
    def __init__(self, config: Dict[str, Any] = None, llm_config: ModelConfig = None):
        super().__init__(config, llm_config)
        self.compression_prompt = self.config.get("compression_prompt", self._default_compression_prompt())
        # Lazy import to avoid circular dependencies
        self._llm_client = self._create_llm_client(llm_config)
    
    @staticmethod
    def _remove_think_blocks(content: str) -> str:
        """Remove <think>...</think> blocks from content"""
        # Use regex to remove all <think>...</think> blocks (case insensitive, multiline)
        pattern = r'<think>.*?</think>'
        cleaned_content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
        return cleaned_content

    def _create_llm_client(self, llm_config: ModelConfig):
        if llm_config is None:
            return None
        config = ConfigDict(llm_config)
        return get_llm_model(config)

    def _default_compression_prompt(self) -> str:
        """Default compression prompt"""
        return """## Task
You are a text compression expert. Please intelligently compress the following text, retaining core information and key content while removing redundancy and unimportant parts.

## Compression Requirements
1. Keep the position and count of [SYSTEM], [USER], [ASSISTANT], and [TOOL] tags unchanged in the output
2. Maintain the main meaning and logical structure of the original text, retain key information and important details, use more concise expressions
3. Remove repetitive, redundant statements, ensure the compressed text remains coherent and readable

## Original Text:
{content}

Please output the compressed text:"""
    
    def compress(self, content: str) -> CompressionResult:
        """Compress content using LLM"""
        original_content = content
        
        # Get LLM client
        llm_client = self._llm_client
        if llm_client is None:
            logger.warning("LLM client unavailable, returning original content")
            return CompressionResult(
                original_content=original_content,
                compressed_content=content,
                compression_ratio=1.0,
                metadata={"error": "LLM client unavailable"},
                compression_type=CompressionType.LLM_BASED
            )
        
        try:
            # Build prompt
            prompt = self.compression_prompt.format(content=content)
            messages = [{"role": "user", "content": prompt}]
            
            # Call LLM
            response = llm_client.completion(
                messages=messages,
                temperature=0.3
            )
            
            # Remove <think>...</think> blocks first, then strip whitespace
            compressed_content = self._remove_think_blocks(response.content).strip()
            compression_ratio = self._calculate_compression_ratio(original_content, compressed_content)
            
            return CompressionResult(
                original_content=original_content,
                compressed_content=compressed_content,
                compression_ratio=compression_ratio,
                metadata={
                    "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0),
                    "completion_tokens": getattr(response.usage, 'completion_tokens', 0),
                },
                compression_type=CompressionType.LLM_BASED
            )
            
        except Exception as e:
            logger.error(f"LLM compression failed: {traceback.format_exc()}")
            return CompressionResult(
                original_content=original_content,
                compressed_content=content,
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
    