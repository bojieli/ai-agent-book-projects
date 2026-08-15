"""AWorld Prompt Templates Module.

This module provides a simplified implementation of prompt templates inspired by LangChain.
It supports string formatting, chat message templates, and various formatting options.

**Class hierarchy:**

.. code-block::

    BasePromptTemplate --> StringPromptTemplate (PromptTemplate)

    BaseMessagePromptTemplate --> HumanMessagePromptTemplate
                              --> AIMessagePromptTemplate  
                              --> SystemMessagePromptTemplate
                              --> MessagesPlaceholder

**Main components:**

- **StringPromptTemplate**: For simple string-based prompts with variable substitution
- **MessagesPlaceholder**: For injecting lists of messages into chat templates

**Example usage:**

.. code-block:: python

    from aworld.core.context.prompts import PromptTemplate
    
    # Simple string template
    prompt = PromptTemplate.from_template("Hello {name}, how are you?")
    result = prompt.format(name="Alice")

"""

import logging
from aworld.core.context.prompts.base_prompt_template import BasePromptTemplate
from aworld.core.context.prompts.string_prompt_template import StringPromptTemplate, PromptTemplate
from aworld.core.context.prompts.formatters import (
    TemplateFormat,
    format_template,
    get_template_variables,
)

__all__ = [
    # Base classes
    "BasePromptTemplate",

    # Prompt templates
    "StringPromptTemplate",
    "PromptTemplate",  # Backward compatibility alias

    # Formatters and utilities
    "TemplateFormat",
    "format_template",
    "get_template_variables",
] 


