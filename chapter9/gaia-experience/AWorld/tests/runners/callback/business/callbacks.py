# coding: utf-8
# Copyright (c) 2025 inclusionAI.

"""
Callback function registration module, used for centralized management and registration of all callback functions.
"""

from aworld.runners.callback.decorator import reg_callback, CallbackRegistry


# Register a simple callback function
@reg_callback("print_content")
def simple_callback(content):
    """Simple callback function that prints content and returns it
    
    Args:
        content: Content to print
        
    Returns:
        The input content
    """
    print(f"Callback function received content: {content}")
    return content


# You can register more callback functions here
@reg_callback("uppercase_content")
def uppercase_callback(content):
    """Callback function that converts content to uppercase
    
    Args:
        content: Content to process
        
    Returns:
        Content converted to uppercase
    """
    if isinstance(content, str):
        result = content.upper()
        print(f"Callback function converted content to uppercase: {result}")
        return result
    return content


# Provide a function to check all registered callback functions
def list_all_callbacks():
    """List all registered callback functions"""
    callbacks = CallbackRegistry.list()
    print("Registered callback functions:")
    for key, func_name in callbacks.items():
        print(f"  - {key}: {func_name}")
    return callbacks 