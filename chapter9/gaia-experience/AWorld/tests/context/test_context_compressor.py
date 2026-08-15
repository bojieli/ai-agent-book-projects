import os
import sys
from pathlib import Path
import unittest

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from aworld.config.conf import AgentConfig, ModelConfig, ContextRuleConfig, OptimizationConfig, LlmCompressionConfig
from aworld.core.context.processor import CompressionResult, CompressionType
from aworld.core.context.processor.llm_compressor import LLMCompressor
from aworld.core.context.processor.prompt_processor import PromptProcessor


class TestPromptCompressor(unittest.TestCase):
    """Test cases for PromptCompressor.compress_batch function"""

    def test_compress_batch_basic(self):

        compressor = LLMCompressor(
            llm_config=ModelConfig(
                llm_model_name=os.environ["LLM_MODEL_NAME"],
                llm_base_url=os.environ["LLM_BASE_URL"],
                llm_api_key=os.environ["LLM_API_KEY"],
            )
        )

        # Test data
        contents = [
            "[SYSTEM]You are a helpful assistant.\n[USER]This is the first long text content that needs compression. This is the first long text content that needs compression.",
        ]

        # Execute compress_batch
        results = compressor.compress_batch(contents)

        # Assertions
        for result in results:
            self.assertIsInstance(result, CompressionResult)
            self.assertEqual(result.compression_type, CompressionType.LLM_BASED)
            self.assertTrue(
                'This is the first long text content that needs compression. This is the first long text content that needs compression.' not in result.compressed_content)

    def test_compress_messages(self):
        """Test compress_messages function from PromptProcessor"""

        # Create context rule with compression enabled
        context_rule = ContextRuleConfig(
            optimization_config=OptimizationConfig(
                enabled=True,
                max_token_budget_ratio=0.8
            ),
            llm_compression_config=LlmCompressionConfig(
                enabled=True,
                trigger_compress_token_length=10,  # Low threshold to trigger compression
                compress_model=ModelConfig(
                    llm_model_name=os.environ["LLM_MODEL_NAME"],
                    llm_base_url=os.environ["LLM_BASE_URL"],
                    llm_api_key=os.environ["LLM_API_KEY"],
                )
            )
        )

        # Create prompt processor with context_rule and model_config
        processor = PromptProcessor(context_rule=context_rule, model_config=ModelConfig(
            llm_model_name=os.environ["LLM_MODEL_NAME"],
            llm_base_url=os.environ["LLM_BASE_URL"],
            llm_api_key=os.environ["LLM_API_KEY"],
        ))

        # Test messages with repeated content that needs compression
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": "This is the first long text content that needs compression. This is the first long text content that needs compression."
            },
            {
                "role": "assistant",
                "content": "I understand you want me to help with compression."
            }
        ]

        # Execute compress_messages
        compressed_messages = processor.compress_messages(messages)

        # Assertions
        self.assertIsInstance(compressed_messages, list)
        self.assertEqual(len(compressed_messages), len(messages))

        # Find the user message and verify it was processed
        user_message = None
        for msg in compressed_messages:
            if msg.get("role") == "user":
                user_message = msg
                break

        self.assertIsNotNone(user_message)
        # The original repeated text should be compressed
        original_content = "This is the first long text content that needs compression. This is the first long text content that needs compression."
        self.assertNotEqual(user_message["content"], original_content)
        # The compressed content should be shorter than original
        self.assertLess(len(user_message["content"]), len(original_content))


if __name__ == "__main__":
    unittest.main()
