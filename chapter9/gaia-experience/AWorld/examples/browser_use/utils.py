# coding: utf-8
import requests
import json
from io import BytesIO
import os
from typing import Any, Optional, Type
import base64

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from aworld.logs.util import logger


def extract_json_from_model_output(content: str) -> dict:
    """Extract JSON from model output, handling both plain JSON and code-block-wrapped JSON."""
    try:
        # If content is wrapped in code blocks, extract just the JSON part
        if '```' in content:
            # Find the JSON content between code blocks
            content = content.split('```')[1]
            # Remove language identifier if present (e.g., 'json\n')
            if '\n' in content:
                content = content.split('\n', 1)[1]
        # Parse the cleaned content
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.warning(f'Failed to parse model output: {content} {str(e)}')
        raise ValueError('Could not parse response.')


def convert_input_messages(input_messages: list[BaseMessage], model_name: Optional[str]) -> list[BaseMessage]:
    """Convert input messages to a format that is compatible with the planner model"""
    if model_name is None:
        return input_messages
    if model_name == 'deepseek-reasoner' or model_name.startswith('deepseek-r1'):
        converted_input_messages = _convert_messages_for_non_function_calling_models(input_messages)
        merged_input_messages = _merge_successive_messages(converted_input_messages, HumanMessage)
        merged_input_messages = _merge_successive_messages(merged_input_messages, AIMessage)
        return merged_input_messages
    return input_messages


def _convert_messages_for_non_function_calling_models(input_messages: list[BaseMessage]) -> list[BaseMessage]:
    """Convert messages for non-function-calling models"""
    output_messages = []
    for message in input_messages:
        if isinstance(message, HumanMessage):
            output_messages.append(message)
        elif isinstance(message, SystemMessage):
            output_messages.append(message)
        elif isinstance(message, ToolMessage):
            output_messages.append(HumanMessage(content=message.content))
        elif isinstance(message, AIMessage):
            # check if tool_calls is a valid JSON object
            if message.tool_calls:
                tool_calls = json.dumps(message.tool_calls)
                output_messages.append(AIMessage(content=tool_calls))
            else:
                output_messages.append(message)
        else:
            raise ValueError(f'Unknown message type: {type(message)}')
    return output_messages


def _merge_successive_messages(messages: list[BaseMessage], class_to_merge: Type[BaseMessage]) -> list[BaseMessage]:
    """Some models like deepseek-reasoner dont allow multiple human messages in a row. This function merges them into one."""
    merged_messages = []
    streak = 0
    for message in messages:
        if isinstance(message, class_to_merge):
            streak += 1
            if streak > 1:
                if isinstance(message.content, list):
                    merged_messages[-1].content += message.content[0]['text']  # type:ignore
                else:
                    merged_messages[-1].content += message.content
            else:
                merged_messages.append(message)
        else:
            merged_messages.append(message)
            streak = 0
    return merged_messages


def save_conversation(input_messages: list[BaseMessage], response: Any, target: str,
                      encoding: Optional[str] = None) -> None:
    """Save conversation history to file."""

    # create folders if not exists
    os.makedirs(os.path.dirname(target), exist_ok=True)

    with open(
            target,
            'w',
            encoding=encoding,
    ) as f:
        _write_messages_to_file(f, input_messages)
        _write_response_to_file(f, response)


def _write_messages_to_file(f: Any, messages: list[BaseMessage]) -> None:
    """Write messages to conversation file"""
    for message in messages:
        f.write(f' {message.__class__.__name__} \n')

        if isinstance(message.content, list):
            for item in message.content:
                if isinstance(item, dict) and item.get('type') == 'text':
                    f.write(item['text'].strip() + '\n')
        elif isinstance(message.content, str):
            try:
                content = json.loads(message.content)
                f.write(json.dumps(content, indent=2) + '\n')
            except json.JSONDecodeError:
                f.write(message.content.strip() + '\n')

        f.write('\n')


def _write_response_to_file(f: Any, response: Any) -> None:
    """Write model response to conversation file"""
    f.write(' RESPONSE\n')
    f.write(json.dumps(json.loads(response.model_dump_json(exclude_unset=True)), indent=2))


# Add token counting related functions
# Note: These functions have been moved from memory.py and agent.py to utils.py, removing the dependency on MessageManager class

def estimate_text_tokens(text: str, estimated_characters_per_token: int = 3) -> int:
    """Roughly estimate token count in text
    
    Args:
        text: The text to estimate tokens for
        estimated_characters_per_token: Estimated characters per token, default is 3
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    # Use character count divided by average characters per token to estimate tokens
    return len(text) // estimated_characters_per_token


def estimate_message_tokens(message: BaseMessage, image_tokens: int = 800, 
                       estimated_characters_per_token: int = 3) -> int:
    """Roughly estimate token count for a single message
    
    Args:
        message: The message to estimate tokens for
        image_tokens: Estimated tokens per image, default is 800
        estimated_characters_per_token: Estimated characters per token, default is 3
        
    Returns:
        Estimated token count
    """
    tokens = 0
    # Handle tuple case
    if isinstance(message, tuple):
        # Convert to string and estimate tokens
        message_str = str(message)
        return estimate_text_tokens(message_str, estimated_characters_per_token)
        
    if isinstance(message.content, list):
        for item in message.content:
            if 'image_url' in item:
                tokens += image_tokens
            elif isinstance(item, dict) and 'text' in item:
                tokens += estimate_text_tokens(item['text'], estimated_characters_per_token)
    else:
        msg = message.content
        if hasattr(message, 'tool_calls'):
            msg += str(message.tool_calls)  # type: ignore
        tokens += estimate_text_tokens(msg, estimated_characters_per_token)
    return tokens


def estimate_messages_tokens(messages: list[BaseMessage], image_tokens: int = 800,
                        estimated_characters_per_token: int = 3) -> int:
    """Roughly estimate total token count for a list of messages
    
    Args:
        messages: The list of messages to estimate tokens for
        image_tokens: Estimated tokens per image, default is 800
        estimated_characters_per_token: Estimated characters per token, default is 3
        
    Returns:
        Estimated total token count
    """
    total_tokens = 0
    for msg in messages:
        total_tokens += estimate_message_tokens(msg, image_tokens, estimated_characters_per_token)
    return total_tokens
