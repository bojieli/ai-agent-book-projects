
from abc import ABC, abstractmethod
from typing import Any, Dict

from aworld.config.conf import ModelConfig
from aworld.core.context.processor import CompressionResult


class BaseCompressor(ABC):
    """Base compressor class"""
    
    def __init__(self, config: Dict[str, Any] = None, llm_config: ModelConfig = None):
        self.config = config or {}
        self.llm_config = llm_config
    @abstractmethod
    def compress(self, content: str, metadata: Dict[str, Any] = None) -> CompressionResult:
        """Compress content"""
        pass
    
    def _calculate_compression_ratio(self, original: str, compressed: str) -> float:
        """Calculate compression ratio"""
        if len(original) == 0:
            return 1.0
        return len(compressed) / len(original)
