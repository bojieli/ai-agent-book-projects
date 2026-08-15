# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import re
import copy
from typing import Dict, Any, AsyncGenerator

from aworld.core.context.base import Context
from aworld.core.event.base import Message
from aworld.logs.util import logger
from aworld.models.model_response import ModelResponse
from aworld.output.base import Output, MessageOutput
from aworld.runners.hook.hook_factory import HookFactory
from aworld.runners.hook.hooks import OutputProcessHook
from aworld.utils.common import convert_to_snake


@HookFactory.register(name="ModelResponseProcessHook",
                      desc="Process ModelResponse type messages before sending to frontend display")
class ModelResponseProcessHook(OutputProcessHook):
    """Process ModelResponse type messages before sending to frontend display"""

    def name(self):
        return convert_to_snake("ModelResponseProcessHook")
    
    async def exec(self, message: Message, context: Context = None) -> Message:
        """Process ModelResponse type messages
        
        Args:
            message: Message object
            context: Context object
            
        Returns:
            Processed message object
        """
        # Get payload
        if not message or not message.payload:
            return message
        
        payload = message.payload
        
        # Process different types of payload
        if isinstance(payload, ModelResponse):
            # Directly process ModelResponse type
            processed_payload = self.process_model_response(payload)
            message.payload = processed_payload
            
            # Record processing results
            self._log_processing_result(payload, processed_payload, context)
            
        elif isinstance(payload, MessageOutput) and hasattr(payload, 'source'):
            # Process ModelResponse in MessageOutput
            source = payload.source
            if isinstance(source, ModelResponse):
                processed_source = self.process_model_response(source)
                payload.source = processed_source
                
                # Record processing results
                self._log_processing_result(source, processed_source, context)
        return message
    
    def process_model_response(self, model_response: ModelResponse) -> ModelResponse:
        """Process ModelResponse
        
        Args:
            model_response: ModelResponse object
            
        Returns:
            Processed ModelResponse object
        """
        if not model_response:
            return model_response
            
        # Create a new ModelResponse object to avoid modifying the original
        processed_response = copy.deepcopy(model_response)
        content = self.process_output_content(processed_response.content)
        processed_response.content = content
        return processed_response
    
    def _log_processing_result(self, original: ModelResponse, processed: ModelResponse, context: Context = None):
        """Record processing results
        
        Args:
            original: Original ModelResponse
            processed: Processed ModelResponse
            context: Context object
        """
        # Record content length before and after processing for analysis
        original_length = len(original.content) if original and original.content else 0
        processed_length = len(processed.content) if processed and processed.content else 0
        
        # Save processing results to context for later retrieval
        if context:
            if not hasattr(context, 'hook_results'):
                context.hook_results = {}
            if not hasattr(context.hook_results, 'output_process'):
                context.hook_results.output_process = {}
            
            # Save processing results
            context.hook_results.output_process = {
                'hook_name': self.name(),
                'original_length': original_length,
                'processed_length': processed_length,
                'removed_content': original_length - processed_length,
                'processed_at': context.get_current_timestamp() if hasattr(context, 'get_current_timestamp') else None,
                'processing_details': {
                    'removed_html_tags': True,
                    'removed_think_tags': True
                }
            }
        
        logger.info(f"ModelResponse processing result: Original length {original_length}, Processed length {processed_length}, Removed content {original_length - processed_length}")
