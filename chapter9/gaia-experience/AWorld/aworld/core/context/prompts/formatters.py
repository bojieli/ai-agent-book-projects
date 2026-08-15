# coding: utf-8
# Copyright (c) 2025 inclusionAI.
"""Template formatters for prompt templates."""

import re
from enum import Enum
from typing import Any, Dict, List, Mapping, Set
import logging
logger = logging.getLogger("prompts")

class TemplateFormat(str, Enum):
    """Template format enumeration."""
    F_STRING = "f-string"
    DOUBLE_BRACE = "double-brace"


def format_template(template: str, template_format: TemplateFormat, **kwargs: Any) -> str:
    try:
        if template_format == TemplateFormat.F_STRING:
            return _format_f_string(template, **kwargs)
        elif template_format == TemplateFormat.DOUBLE_BRACE:
            return _format_double_brace(template, **kwargs)
        else:
            # Unsupported format, return original template
            logger.warning(f"Unsupported template format: {template_format}, returning original template")
            return template
    except Exception as e:
        # Any error, return original template
        logger.warning(f"Error formatting template: {e}, returning original template")
        return template


def get_template_variables(template: str, template_format: TemplateFormat) -> List[str]:
    if not template:
        return []
    try:
        if template_format == TemplateFormat.F_STRING:
            return _get_f_string_variables(template)
        elif template_format == TemplateFormat.DOUBLE_BRACE:
            return _get_double_brace_variables(template)
        else:
            # Unsupported format, return empty list
            logger.warning(f"Unsupported template format: {template_format}, returning empty variable list")
            return []
    except Exception as e:
        # Any error, return empty list
        logger.warning(f"Error extracting template variables: {e}, returning empty variable list")
        return []


def _format_double_brace(template: str, **kwargs: Any) -> str:
    """Format using double brace {{variable}} style."""
    try:
        return _format_double_brace_safe(template, **kwargs)
    except Exception as e:
        # Any error, return original template
        logger.warning(f"Error in double-brace formatting: {e}, returning original template")
        return template


def _format_double_brace_safe(template: str, **kwargs: Any) -> str:
    """Safe format that preserves missing placeholders instead of raising errors."""
    try:
        import re
        
        def replace_placeholder(match):
            try:
                placeholder = match.group(1)
                # Handle format specifiers like {{name:>10}} -> name
                var_name = placeholder.split(':')[0].split('!')[0].strip()
                
                if var_name in kwargs:
                    # If variable exists, replace with its value
                    try:
                        value = kwargs[var_name]
                        # Handle format specifiers if present
                        if ':' in placeholder:
                            format_spec = placeholder.split(':', 1)[1]
                            return f"{value:{format_spec}}"
                        else:
                            return str(value)
                    except Exception as e:
                        # If formatting fails, return the original placeholder
                        logger.debug(f"Failed to format placeholder '{{{{placeholder}}}}': {e}, keeping original")
                        return match.group(0)
                else:
                    # If variable doesn't exist, keep the original placeholder
                    logger.debug(f"Variable '{var_name}' not found in kwargs, keeping placeholder")
                    return match.group(0)
            except Exception as e:
                # If any error in processing the match, return original
                logger.debug(f"Error processing placeholder match: {e}, keeping original")
                return match.group(0)
        
        # Find all {{variable}} patterns
        pattern = r'\{\{([^{}]+)\}\}'
        return re.sub(pattern, replace_placeholder, template)
    except Exception as e:
        # If any error, return original template
        logger.warning(f"Error in safe double-brace formatting: {e}, returning original template")
        return template


def _get_double_brace_variables(template: str) -> List[str]:
    """Extract variables from double-brace style template."""
    try:
        # Find all {{variable}} patterns
        pattern = r'\{\{([^{}]+)\}\}'
        matches = re.findall(pattern, template)
        
        variables = []
        for match in matches:
            try:
                # Handle format specifiers like {{name:>10}} -> name
                var_name = match.split(':')[0].split('!')[0].strip()
                if var_name:
                    variables.append(var_name)
            except Exception as e:
                # If error processing this match, skip it
                logger.debug(f"Error processing variable match '{match}': {e}, skipping")
                continue
        
        return list(set(variables))  # Remove duplicates
    except Exception as e:
        # If any error, return empty list
        logger.warning(f"Error extracting double-brace variables: {e}, returning empty list")
        return []


def _format_f_string(template: str, **kwargs: Any) -> str:
    """Format using Python f-string style."""
    try:
        return _format_f_string_safe(template, **kwargs)
    except Exception as e:
        # Any error, return original template
        logger.warning(f"Error in f-string formatting: {e}, returning original template")
        return template


def _format_f_string_safe(template: str, **kwargs: Any) -> str:
    """Safe format that preserves missing placeholders instead of raising errors."""
    try:
        import re
        
        def replace_placeholder(match):
            try:
                placeholder = match.group(1)
                # Handle format specifiers like {name:>10} -> name
                var_name = placeholder.split(':')[0].split('!')[0].strip()
                
                if var_name in kwargs:
                    # If variable exists, format it properly
                    try:
                        return f"{{{placeholder}}}".format(**kwargs)
                    except Exception as e:
                        # If formatting fails, return the original placeholder
                        logger.debug(f"Failed to format placeholder '{placeholder}': {e}, keeping original")
                        return match.group(0)
                else:
                    # If variable doesn't exist, keep the original placeholder
                    logger.debug(f"Variable '{var_name}' not found in kwargs, keeping placeholder")
                    return match.group(0)
            except Exception as e:
                # If any error in processing the match, return original
                logger.debug(f"Error processing placeholder match: {e}, keeping original")
                return match.group(0)
        
        # Find all {variable} patterns, excluding escaped {{ and }}
        pattern = r'(?<!\{)\{([^{}]+)\}(?!\})'
        return re.sub(pattern, replace_placeholder, template)
    except Exception as e:
        # If any error, return original template
        logger.warning(f"Error in safe f-string formatting: {e}, returning original template")
        return template


def _get_f_string_variables(template: str) -> List[str]:
    """Extract variables from f-string style template."""
    try:
        # Find all {variable} patterns, excluding escaped {{ and }}
        pattern = r'(?<!\{)\{([^{}]+)\}(?!\})'
        matches = re.findall(pattern, template)
        
        variables = []
        for match in matches:
            try:
                # Handle format specifiers like {name:>10} -> name
                var_name = match.split(':')[0].split('!')[0].strip()
                if var_name:
                    variables.append(var_name)
            except Exception as e:
                # If error processing this match, skip it
                logger.debug(f"Error processing variable match '{match}': {e}, skipping")
                continue
        
        return list(set(variables))  # Remove duplicates
    except Exception as e:
        # If any error, return empty list
        logger.warning(f"Error extracting f-string variables: {e}, returning empty list")
        return []


def escape_template_string(text: str, template_format: TemplateFormat) -> str:
    """Escape special characters in text to prevent template interpretation.
    
    Args:
        text: Text to escape
        template_format: The template format being used
        
    Returns:
        Escaped text safe for use in templates
    """
    if template_format == TemplateFormat.F_STRING:
        # Escape curly braces by doubling them
        return text.replace('{', '{{').replace('}', '}}')
    elif template_format == TemplateFormat.DOUBLE_BRACE:
        # Escape double braces by adding extra braces
        return text.replace('{{', '{{{{').replace('}}', '}}}}')
    else:
        return text 