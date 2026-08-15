import re
import logging
from typing import Any, Dict, List, Optional, Pattern, Tuple

from aworld.config.conf import ModelConfig
from aworld.core.context.processor import CompressionResult, CompressionType
from aworld.core.context.processor.base_compressor import BaseCompressor

logger = logging.getLogger(__name__)

DEFAULT_LLM_LINGUA_INSTRUCTION = (
    "Given this conversation messages, please compress them while preserving key information"
)


class LLMLinguaCompressor(BaseCompressor):
    """
    Compress messages using LLMLingua Project.
    
    https://github.com/microsoft/LLMLingua
    """

    # Pattern to match ref tags at the beginning or end of the string,
    # allowing for malformed tags
    _pattern_beginning: Pattern = re.compile(r"\A(?:<#)?(?:ref)?(\d+)(?:#>?)?")
    _pattern_ending: Pattern = re.compile(r"(?:<#)?(?:ref)?(\d+)(?:#>?)?\Z")

    def __init__(self, config: Dict[str, Any] = None, llm_config: ModelConfig = None):
        super().__init__(config, llm_config)
        
        # LLMLingua specific configuration
        self.model_name = self.config.get("model_name", "NousResearch/Llama-2-7b-hf")
        self.device_map = self.config.get("device_map", "cuda")
        self.target_token = self.config.get("target_token", 300)
        self.rank_method = self.config.get("rank_method", "longllmlingua")
        self.model_configuration = self.config.get("model_configuration", {})
        self.open_api_config = self.config.get("open_api_config", {})
        self.instruction = self.config.get("instruction", DEFAULT_LLM_LINGUA_INSTRUCTION)
        self.additional_compress_kwargs = self.config.get("additional_compress_kwargs", {
            "condition_compare": True,
            "condition_in_question": "after",
            "context_budget": "+100",
            "reorder_context": "sort",
            "dynamic_context_compression_ratio": 0.4,
        })
        
        self.lingua = None
        self._initialize_lingua()

    def _initialize_lingua(self):
        """Initialize LLMLingua PromptCompressor"""
        try:
            from llmlingua import PromptCompressor
            
            self.lingua = PromptCompressor(
                model_name=self.model_name,
                device_map=self.device_map,
                model_config=self.model_configuration,
                open_api_config=self.open_api_config,
            )
            logger.info(f"LLMLingua compressor initialized with model: {self.model_name}")
            
        except ImportError:
            logger.error(
                "Could not import llmlingua python package. "
                "Please install it with `pip install llmlingua`."
            )
            self.lingua = None
        except Exception as e:
            logger.error(f"Failed to initialize LLMLingua compressor: {e}")
            self.lingua = None

    @staticmethod
    def _format_messages(messages: List[Dict[str, Any]]) -> List[str]:
        """
        Format messages by including special ref tags for tracking after compression
        """
        formatted_messages = []
        for i, message in enumerate(messages):
            role = message.get("role", "unknown")
            content = message.get("content", "").replace("\n\n", "\n")
            
            # Format as [ROLE] content with ref tags
            message_string = f"\n\n<#ref{i}#> [{role.upper()}] {content} <#ref{i}#>\n\n"
            formatted_messages.append(message_string)
        return formatted_messages

    def extract_ref_id_tuples_and_clean(self, contents: List[str]) -> List[Tuple[str, int]]:
        """
        Extracts reference IDs from the contents and cleans up the ref tags.
        
        Args:
            contents: A list of contents to be processed.

        Returns:
            List of tuples containing (cleaned_string, ref_id)
        """
        ref_id_tuples = []
        for content in contents:
            clean_string = content.strip()
            if not clean_string:
                continue

            # Search for ref tags at the beginning and the end of the string
            ref_id = None
            for pattern in [self._pattern_beginning, self._pattern_ending]:
                match = pattern.search(clean_string)
                if match:
                    ref_id = match.group(1)
                    clean_string = pattern.sub("", clean_string).strip()
            
            # Convert ref ID to int or use -1 if not found
            ref_id_to_use = int(ref_id) if ref_id and ref_id.isdigit() else -1
            ref_id_tuples.append((clean_string, ref_id_to_use))

        return ref_id_tuples

    def _parse_compressed_content_to_messages(self, compressed_content: str, original_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parse compressed content back to message format
        """
        # Split by double newlines and filter empty strings
        compressed_parts = [part.strip() for part in compressed_content.split("\n\n") if part.strip()]
        
        extracted_metadata = self.extract_ref_id_tuples_and_clean(compressed_parts)
        
        compressed_messages = []
        for content, index in extracted_metadata:
            if not content:
                continue
                
            # Parse role from content if present
            role_match = re.match(r'\[(\w+)\]\s*(.*)', content)
            if role_match:
                role = role_match.group(1).lower()
                message_content = role_match.group(2).strip()
            else:
                # Fallback to original message role if available
                role = "assistant"  # Default role
                message_content = content
                if index != -1 and index < len(original_messages):
                    role = original_messages[index].get("role", "assistant")
            
            compressed_messages.append({
                "role": role,
                "content": message_content
            })
        
        return compressed_messages

    def compress(self, content: str) -> CompressionResult:
        """
        Compress content using LLMLingua
        
        Note: This method expects content to be a JSON string representation of messages
        or will treat it as a single message.
        """
        original_content = content
        
        if self.lingua is None:
            logger.warning("LLMLingua compressor unavailable, returning original content")
            return CompressionResult(
                original_content=original_content,
                compressed_content=content,
                compression_ratio=1.0,
                metadata={"error": "LLMLingua compressor unavailable"},
                compression_type=CompressionType.LLMLINGUA
            )
        
        try:
            # Try to parse as messages format first
            import json
            try:
                messages = json.loads(content)
                if isinstance(messages, list) and all(isinstance(msg, dict) for msg in messages):
                    return self.compress_messages(messages)
            except (json.JSONDecodeError, TypeError):
                pass
            
            # Treat as plain text
            formatted_content = [f"\n\n<#ref0#> {content} <#ref0#>\n\n"]
            
            compressed_prompt = self.lingua.compress_prompt(
                context=formatted_content,
                instruction=self.instruction,
                question="",  # No specific question for plain text
                target_token=self.target_token,
                rank_method=self.rank_method,
                concate_question=False,
                add_instruction=False,
                **self.additional_compress_kwargs,
            )
            
            compressed_content = compressed_prompt["compressed_prompt"]
            compression_ratio = self._calculate_compression_ratio(original_content, compressed_content)
            
            return CompressionResult(
                original_content=original_content,
                compressed_content=compressed_content,
                compression_ratio=compression_ratio,
                metadata={
                    "origin_tokens": compressed_prompt.get("origin_tokens", 0),
                    "compressed_tokens": compressed_prompt.get("compressed_tokens", 0),
                    "ratio": compressed_prompt.get("ratio", "unknown"),
                },
                compression_type=CompressionType.LLMLINGUA
            )
            
        except Exception as e:
            logger.error(f"LLMLingua compression failed: {e}")
            return CompressionResult(
                original_content=original_content,
                compressed_content=content,
                compression_ratio=1.0,
                metadata={"error": str(e)},
                compression_type=CompressionType.LLMLINGUA
            )

    def compress_messages(self, messages: List[Dict[str, Any]]) -> CompressionResult:
        """
        Compress a list of messages using LLMLingua
        """
        if not messages:
            return CompressionResult(
                original_content="[]",
                compressed_content="[]",
                compression_ratio=1.0,
                metadata={},
                compression_type=CompressionType.LLMLINGUA
            )
        
        original_content = str(messages)
        
        if self.lingua is None:
            logger.warning("LLMLingua compressor unavailable, returning original messages")
            return CompressionResult(
                original_content=original_content,
                compressed_content=original_content,
                compression_ratio=1.0,
                metadata={"error": "LLMLingua compressor unavailable"},
                compression_type=CompressionType.LLMLINGUA
            )
        
        try:
            formatted_messages = self._format_messages(messages)
            
            compressed_prompt = self.lingua.compress_prompt(
                context=formatted_messages,
                instruction=self.instruction,
                question="",  # No specific question for conversation compression
                target_token=self.target_token,
                rank_method=self.rank_method,
                concate_question=False,
                add_instruction=False,
                **self.additional_compress_kwargs,
            )
            
            # Parse compressed content back to messages
            compressed_messages = self._parse_compressed_content_to_messages(
                compressed_prompt["compressed_prompt"], messages
            )
            
            compressed_content = str(compressed_messages)
            compression_ratio = self._calculate_compression_ratio(original_content, compressed_content)
            
            return CompressionResult(
                original_content=original_content,
                compressed_content=compressed_content,
                compression_ratio=compression_ratio,
                metadata={
                    "origin_tokens": compressed_prompt.get("origin_tokens", 0),
                    "compressed_tokens": compressed_prompt.get("compressed_tokens", 0),
                    "ratio": compressed_prompt.get("ratio", "unknown"),
                    "compressed_messages": compressed_messages,
                },
                compression_type=CompressionType.LLMLINGUA
            )
            
        except Exception as e:
            logger.error(f"LLMLingua message compression failed: {e}")
            return CompressionResult(
                original_content=original_content,
                compressed_content=original_content,
                compression_ratio=1.0,
                metadata={"error": str(e)},
                compression_type=CompressionType.LLMLINGUA
            )

    def compress_batch(self, contents: List[str]) -> List[CompressionResult]:
        """Compress multiple contents in batch"""
        results = []
        for content in contents:
            result = self.compress(content)
            results.append(result)
        return results
