# coding: utf-8
# Copyright (c) 2025 inclusionAI.
"""
Dynamic Variables for Prompt Templates

This module provides dynamic variable functions that can be used as partial_variables
in PromptTemplate to inject runtime-generated values.
"""

import os
import platform
import uuid
import logging
logger = logging.getLogger("prompts")
from datetime import datetime, timezone
from typing import Callable, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from aworld.core.context.base import Context

# ==================== Time Functions ====================

def get_current_time() -> str:
    """Get current time in HH:MM:SS format."""
    try:
        return datetime.now().strftime("%H:%M:%S")
    except Exception as e:
        logger.warning(f"Error getting current time: {e}")
        return ""


def get_current_date() -> str:
    """Get current date in YYYY-MM-DD format."""
    try:
        return datetime.now().strftime("%Y-%m-%d")
    except Exception as e:
        logger.warning(f"Error getting current date: {e}")
        return ""


def get_current_datetime() -> str:
    """Get current datetime in YYYY-MM-DD HH:MM:SS format."""
    try:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.warning(f"Error getting current datetime: {e}")
        return ""


def get_current_timestamp() -> str:
    """Get current timestamp."""
    try:
        return str(int(datetime.now().timestamp()))
    except Exception as e:
        logger.warning(f"Error getting current timestamp: {e}")
        return ""


def get_current_weekday() -> str:
    """Get current weekday name."""
    try:
        return datetime.now().strftime("%A")
    except Exception as e:
        logger.warning(f"Error getting current weekday: {e}")
        return ""


def get_current_month() -> str:
    try:
        return datetime.now().strftime("%B")
    except Exception as e:
        logger.warning(f"Error getting current month: {e}")
        return ""


def get_current_year() -> str:
    try:
        return str(datetime.now().year)
    except Exception as e:
        logger.warning(f"Error getting current year: {e}")
        return ""

# ==================== System Information Functions ====================

def get_system_platform() -> str:
    try:
        return platform.platform()
    except Exception as e:
        logger.warning(f"Error getting system platform: {e}")
        return ""


def get_system_os() -> str:
    """Get operating system name."""
    try:
        return platform.system()
    except Exception as e:
        logger.warning(f"Error getting system OS: {e}")
        return ""


def get_python_version() -> str:
    """Get Python version."""
    try:
        return platform.python_version()
    except Exception as e:
        logger.warning(f"Error getting Python version: {e}")
        return ""


def get_hostname() -> str:
    """Get hostname."""
    try:
        return platform.node()
    except Exception as e:
        logger.warning(f"Error getting hostname: {e}")
        return ""


def get_username() -> str:
    """Get current username."""
    try:
        return os.getlogin()
    except Exception as e:
        logger.warning(f"Error getting username: {e}")
        return ""


def get_working_directory() -> str:
    """Get current working directory."""
    try:
        return os.getcwd()
    except Exception as e:
        logger.warning(f"Error getting working directory: {e}")
        return ""


def get_random_uuid() -> str:
    """Get a random UUID."""
    try:
        return str(uuid.uuid4())
    except Exception as e:
        logger.warning(f"Error generating UUID: {e}")
        return ""


def get_short_uuid() -> str:
    """Get a short UUID (first 8 characters)."""
    try:
        return str(uuid.uuid4())[:8]
    except Exception as e:
        logger.warning(f"Error generating short UUID: {e}")
        return ""

# ==================== Predefined Dynamic Variable Collections ====================

# All variable collections - includes time, system and Context variables
ALL_PREDEFINED_DYNAMIC_VARIABLES = {
    # time
    "current_time": get_current_time,
    "current_date": get_current_date,
    "current_datetime": get_current_datetime,
    "current_timestamp": get_current_timestamp,
    "current_weekday": get_current_weekday,
    "current_month": get_current_month,
    "current_year": get_current_year,
    # system
    "system_platform": get_system_platform,
    "system_os": get_system_os,
    "python_version": get_python_version,
    "hostname": get_hostname,
    "username": get_username,
    "working_directory": get_working_directory,
    "random_uuid": get_random_uuid,
    "short_uuid": get_short_uuid,
}

# ==================== Context Field Getter Function Factory ====================

def get_value_by_path(obj: Any, field_path: str) -> Any:
    """Generic function to get object member variables by path
    
    Args:
        obj: Object to get value from
        field_path: Field path, supports nested access with both '.' and '/' separators
                   Examples: "agent_name", "model_config.llm_model_name", "user/profile/name", "data.user/settings"
        
    Returns:
        Retrieved value, returns None if path doesn't exist
        
    Examples:
        >>> value = get_value_by_path(context, "agent_name")
        >>> model_name = get_value_by_path(context, "model_config.llm_model_name")
        >>> nested_value = get_value_by_path(obj, "a.b.c.d")
        >>> dict_value = get_value_by_path(data, "user.profile.name")  # supports dict access
        >>> slash_path = get_value_by_path(data, "user/profile/name")   # supports slash separator
        >>> mixed_path = get_value_by_path(data, "user.config/theme")   # supports mixed separators
    """
    if obj is None:
        return None
        
    try:
        current_value = obj
        # Normalize path by replacing '/' with '.' then split by '.'
        normalized_path = field_path.replace('/', '.')
        for field in normalized_path.split('.'):
            if not field:  # Skip empty parts (e.g., from leading/trailing separators)
                continue
                
            # Try attribute access first
            if hasattr(current_value, field):
                current_value = getattr(current_value, field)
            # If attribute access fails, try dictionary/mapping access
            elif hasattr(current_value, '__getitem__'):
                try:
                    current_value = current_value[field]
                except (KeyError, TypeError, IndexError):
                    return None
            else:
                return None
        return current_value
    except Exception:
        return None

def create_context_field_getter(
    field_path: str, 
    default_value: str = "",
    processor: Optional[Callable[[Any], str]] = None,
    fallback_getter: Optional[Callable[["Context"], Any]] = None
) -> Callable[["Context"], str]:
    """Create generic dynamic function to get specified Context field with enhanced retrieval
    
    Args:
        field_path: Field path, supports nested access with both '.' and '/' separators
                   Examples: "agent_name", "model_config.llm_model_name", "user/profile/name", "config.api/version"
        default_value: Default value when field doesn't exist
        processor: Optional value processing function, receives original value returns string
        fallback_getter: Optional fallback getter function, used when field path access fails
        
    Returns:
        Returns a callable function that accepts context parameter
        
    Examples:
        # Simple field
        get_agent_name = create_context_field_getter("agent_name", "Assistant")
        
        # Nested field with dot separator
        get_model = create_context_field_getter("model_config.llm_model_name", "")
        
        # Nested field with slash separator
        get_user_name = create_context_field_getter("user/profile/name", "")
        
        # Mixed separators
        get_api_version = create_context_field_getter("config.api/version", "v1.0")
        
        # With processing function
        get_prompt_preview = create_context_field_getter(
            "system_prompt", "No system prompt",
            processor=lambda p: p[:100] + "..." if len(p) > 100 else p
        )
        
        # With fallback getter function
        get_tools = create_context_field_getter(
            "tool_names", "No tools available",
            processor=lambda tools: ", ".join(tools) if tools else "No tools available"
        )
    """
    def field_getter(context: "Context" = None) -> str:
        if not context:
            return default_value
            
        try:
            value = None
            source = "default"
            
            # 1. First try to get value from context
            value = get_value_by_path(context, field_path)
            if value is not None:
                source = "context"
            
            # 2. If context access fails, try fallback getter
            if value is None and fallback_getter:
                try:
                    value = fallback_getter(context)
                    if value is not None:
                        source = "fallback_getter"
                except Exception as e:
                    logger.warning(f"Fallback getter failed for field '{field_path}': {e}")
            
            # 3. If still no value, try predefined dynamic variables
            if value is None and field_path in ALL_PREDEFINED_DYNAMIC_VARIABLES:
                try:
                    func = ALL_PREDEFINED_DYNAMIC_VARIABLES[field_path]
                    value = func()
                    if value is not None:
                        source = "predefined_variable"
                except Exception as e:
                    logger.warning(f"Predefined variable '{field_path}' failed: {e}")
            
            # 4. If still no value, use default
            if value is None:
                value = default_value
                source = "default"
            
            # 5. Apply processing function if provided
            if processor and value is not None:
                try:
                    value = processor(value)
                    source += "_processed"
                except Exception as e:
                    logger.warning(f"Processor failed for field '{field_path}': {e}")
                    value = default_value
                    source = "default_after_processor_fail"
            
            # 6. Auto-format based on type when no processor provided
            if not processor and value is not None:
                try:
                    if isinstance(value, dict):
                        value = format_ordered_dict_json(value)
                    elif isinstance(value, (list, tuple)):
                        value = format_list_items(value)
                    elif hasattr(value, '__dict__'):
                        value = format_object_summary(value)
                    else:
                        value = str(value)
                except Exception as e:
                    logger.warning(f"Auto-formatting failed for field '{field_path}': {e}")
                    value = str(value)
            
            result = str(value) if value is not None else default_value
            
            # Debug logging
            logger.debug(f"Field retrieval: '{field_path}' -> '{result}' (source: {source})")
            
            return result
            
        except Exception as e:
            logger.warning(f"Error getting field '{field_path}': {e}")
            return default_value
    
    # Set function attributes for better debugging
    safe_field_name = field_path.replace('.', '_').replace('/', '_')
    field_getter.__name__ = f"get_context_{safe_field_name}"
    field_getter.__doc__ = f"Get Context's {field_path} field"
    
    return field_getter


# ==================== Functions Supporting Runtime Context ====================

def create_simple_field_getter(
    field_path: str, 
    default: str = "",
    processor: Optional[Callable[[Any], str]] = None
) -> Callable[["Context"], str]:
    getter = create_context_field_getter(field_path, default, processor=processor)
    return getter

def get_simple_field_value(
    context: "Context", 
    field_path: str, 
    default: str = "",
    processor: Optional[Callable[[Any], str]] = None
) -> str:
    getter = create_simple_field_getter(field_path, default, processor)
    return getter(context)

def create_multiple_field_getters(
    field_configs: list[tuple[str, str, Optional[Callable[[Any], str]]]]
) -> dict[str, Callable[["Context"], str]]:
    getters = {}
    for config in field_configs:
        if len(config) == 2:
            field_path, default_value = config
            processor = None
        elif len(config) == 3:
            field_path, default_value, processor = config
        else:
            raise ValueError(f"Invalid config format: {config}")
            
        safe_key = field_path.replace('.', '_').replace('/', '_')
        getters[safe_key] = create_context_field_getter(field_path, default_value, processor=processor)
    return getters

def get_multiple_field_values(
    context: "Context",
    field_configs: list[tuple[str, str, Optional[Callable[[Any], str]]]]
) -> dict[str, str]:
    result = {}
    for config in field_configs:
        if len(config) == 2:
            field_path, default_value = config
            processor = None
        elif len(config) == 3:
            field_path, default_value, processor = config
        else:
            raise ValueError(f"Invalid config format: {config}")
            
        safe_key = field_path.replace('.', '_').replace('/', '_')
        getter = create_context_field_getter(field_path, default_value, processor=processor)
        result[safe_key] = getter(context)
    return result

def create_field_getters_from_list(field_paths: list[str], default: str = "") -> dict[str, Callable[["Context"], str]]:
    field_configs = [(path, default) for path in field_paths]
    return create_multiple_field_getters(field_configs)

def get_field_values_from_list(context: "Context", field_paths: list[str], default: str = "") -> dict[str, str]:
    field_configs = [(path, default) for path in field_paths]
    return get_multiple_field_values(context, field_configs)

# ==================== Predefined Formatter Functions ====================

def format_ordered_dict_json(od) -> str:
    """Format OrderedDict as JSON string"""
    import json
    if not od:
        return "{}"
    try:
        # Convert to regular dict then format as JSON
        regular_dict = dict(od) if hasattr(od, 'items') else od
        return json.dumps(regular_dict, ensure_ascii=False, indent=None)
    except Exception:
        return str(od)


def format_list_items(items) -> str:
    """Format list items"""
    if not items:
        return "Empty list"
    if isinstance(items, (list, tuple)):
        return f"[{', '.join(str(item) for item in items)}]"
    return str(items)


def format_dict_keys(d) -> str:
    """Format dictionary keys"""
    if not d or not hasattr(d, 'keys'):
        return "No keys"
    return f"Keys: {', '.join(str(k) for k in d.keys())}"


def format_object_summary(obj) -> str:
    """Format object as JSON-like string"""
    import json
    
    if obj is None:
        return "null"
    
    # Try to format as JSON first
    try:
        # Handle common JSON-serializable types
        if isinstance(obj, (dict, list, tuple, str, int, float, bool)):
            return json.dumps(obj, ensure_ascii=False, indent=None)
    except Exception:
        pass
    
    # Handle objects with __dict__ - convert to dict and format as JSON
    if hasattr(obj, '__dict__'):
        try:
            obj_dict = {}
            for key, value in vars(obj).items():
                # Skip private attributes
                if not key.startswith('_'):
                    try:
                        # Try to make value JSON serializable
                        if isinstance(value, (str, int, float, bool, type(None))):
                            obj_dict[key] = value
                        elif isinstance(value, (list, tuple)):
                            obj_dict[key] = list(value)
                        elif isinstance(value, dict):
                            obj_dict[key] = dict(value)
                        else:
                            obj_dict[key] = str(value)
                    except Exception:
                        obj_dict[key] = str(value)
            
            return json.dumps(obj_dict, ensure_ascii=False, indent=None)
        except Exception:
            pass
    
    # Fallback to string representation
    return json.dumps(str(obj), ensure_ascii=False)

