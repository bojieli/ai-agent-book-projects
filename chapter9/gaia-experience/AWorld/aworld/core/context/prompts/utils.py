# coding: utf-8
# Copyright (c) 2025 inclusionAI.
"""
Prompt Template Utilities

Utility functions for working with prompt templates.
"""

from typing import Any, Dict, List

from aworld.core.context.prompts.formatters import TemplateFormat
from aworld.core.context.prompts.string_prompt_template import PromptTemplate

def create_few_shot_prompt(examples: List[Dict[str, str]],
                          example_template: str,
                          suffix: str,
                          input_variables: List[str],
                          example_separator: str = "\n\n",
                          prefix: str = "") -> PromptTemplate:
    # Format all examples
    formatted_examples = []
    for example in examples:
        formatted_example = example_template.format(**example)
        formatted_examples.append(formatted_example)
    
    # Combine everything
    full_template = ""
    if prefix:
        full_template += prefix + "\n\n"
    
    full_template += example_separator.join(formatted_examples)
    
    if formatted_examples and suffix:
        full_template += example_separator + suffix
    elif suffix:
        full_template += suffix
    
    return PromptTemplate.from_template(full_template)


def chain_prompts(*prompts: PromptTemplate) -> PromptTemplate:
    if not prompts:
        raise ValueError("At least one prompt is required")
    
    if len(prompts) == 1:
        return prompts[0]
    
    # Check that all prompts are the same type
    first_type = type(prompts[0])
    if not all(isinstance(p, first_type) for p in prompts):
        raise ValueError("All prompts must be of the same type")
    
    # Chain prompts
    result = prompts[0]
    for prompt in prompts[1:]:
        result = result + prompt
    
    return result


def extract_variables_from_text(text: str, 
                               template_format: TemplateFormat = TemplateFormat.F_STRING) -> List[str]:
    from aworld.core.context.prompts.formatters import get_template_variables
    return get_template_variables(text, template_format)


def validate_prompt_inputs(prompt: PromptTemplate, **kwargs: Any) -> bool:
    try:
        # Merge with partial variables
        merged_vars = prompt._merge_partial_and_user_variables(**kwargs)
        prompt._validate_input_variables(merged_vars)
        return True
    except ValueError:
        raise 