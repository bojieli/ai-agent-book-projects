# coding: utf-8
# Copyright (c) 2025 inclusionAI.

import functools
import inspect
import logging
from typing import Dict, Any, Callable, Optional, Union, Awaitable

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("callback_registry")


class CallbackRegistry:
    """Callback function registry, used to manage and execute callback functions"""
    
    # Registry for storing decorated callback functions
    _registry: Dict[str, Callable] = {}
    
    @classmethod
    def register(cls, key_name: str, func: Callable) -> Callable:
        """Register callback function to the registry
        
        Args:
            key_name: Unique identifier for the callback function
            func: Callback function to register
            
        Returns:
            Registered callback function
        """
        # Check if a callback function with the same key_name already exists
        if key_name in cls._registry:
            existing_func = cls._registry[key_name]
            logger.warning(
                f"Callback function '{key_name}' already exists and will be overwritten! "
                f"Original function: {existing_func.__name__ if hasattr(existing_func, '__name__') else str(existing_func)}, "
                f"New function: {func.__name__ if hasattr(func, '__name__') else str(func)}"
            )
        
        cls._registry[key_name] = func
        return func
    
    @classmethod
    def get(cls, key_name: str) -> Optional[Callable]:
        """Get registered callback function by key_name
        
        Args:
            key_name: Unique identifier for the callback function
            
        Returns:
            Registered callback function, or None if not found
        """
        return cls._registry.get(key_name)
    
    @classmethod
    async def execute(
        cls,
        key_name: str, 
        tool: Any, 
        args: Dict[str, Any], 
        tool_context: Any, 
        tool_response: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Execute registered callback function
        
        Args:
            key_name: Unique identifier for the callback function
            tool: Tool object
            args: Tool arguments
            tool_context: Tool context
            tool_response: Tool response (for post-callbacks)
            
        Returns:
            Return value of the callback function, or None if the callback function doesn't exist
        """
        callback = cls.get(key_name)
        if not callback:
            return None
        
        # Determine parameters based on callback type
        if tool_response is not None:
            # Post-callback
            result = callback(tool, args, tool_context, tool_response)
        else:
            # Pre-callback
            result = callback(tool, args, tool_context)
        
        # Handle asynchronous callbacks
        if inspect.isawaitable(result):
            result = await result
            
        return result
    
    @classmethod
    def list(cls) -> Dict[str, str]:
        """List all registered callback functions
        
        Returns:
            Dictionary containing callback function names and descriptions
        """
        return {
            key: func.__name__ if hasattr(func, '__name__') else str(func)
            for key, func in cls._registry.items()
        }


def reg_callback(key_name: str):
    """Decorator for registering callback functions
    
    Args:
        key_name: Unique identifier for the callback function
        
    Returns:
        Decorator function
    """
    def decorator(func):
        # Register function to the global registry
        CallbackRegistry.register(key_name, func)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# For backward compatibility, keep these functions
def get_callback(key_name: str) -> Optional[Callable]:
    """Get registered callback function by key_name
    
    Args:
        key_name: Unique identifier for the callback function
        
    Returns:
        Registered callback function, or None if not found
    """
    return CallbackRegistry.get(key_name)


async def execute_callback(
    key_name: str, 
    tool: Any, 
    args: Dict[str, Any], 
    tool_context: Any, 
    tool_response: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """Execute registered callback function
    
    Args:
        key_name: Unique identifier for the callback function
        tool: Tool object
        args: Tool arguments
        tool_context: Tool context
        tool_response: Tool response (for post-callbacks)
        
    Returns:
        Return value of the callback function, or None if the callback function doesn't exist
    """
    return await CallbackRegistry.execute(key_name, tool, args, tool_context, tool_response)


def list_callbacks() -> Dict[str, str]:
    """List all registered callback functions
    
    Returns:
        Dictionary containing callback function names and descriptions
    """
    return CallbackRegistry.list() 