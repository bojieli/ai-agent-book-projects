# coding: utf-8
# Copyright (c) 2025 inclusionAI.
"""Base classes for prompt templates."""
import traceback
from abc import ABC, abstractmethod
import logging
logger = logging.getLogger("prompts")
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

from aworld.core.context.prompts.formatters import TemplateFormat, get_template_variables

if TYPE_CHECKING:
    from aworld.core.context.base import Context

class PromptValue(ABC):
    """Base class for prompt values that can be passed to language models."""
    
    @abstractmethod
    def to_string(self) -> str:
        """Convert the prompt value to a string."""
        pass
    
    @abstractmethod
    def to_messages(self) -> List[Dict[str, Any]]:
        """Convert the prompt value to a list of messages."""
        pass


class StringPromptValue(PromptValue):
    """String-based prompt value."""
    
    def __init__(self, text: str):
        self.text = text
    
    def to_string(self) -> str:
        return self.text
    
    def to_messages(self) -> List[Dict[str, Any]]:
        return [{"role": "user", "content": self.text}]
    
    def __str__(self) -> str:
        return self.text
    
    def __repr__(self) -> str:
        return f"StringPromptValue(text={self.text!r})"


class ChatPromptValue(PromptValue):
    """Chat-based prompt value with multiple messages."""
    
    def __init__(self, messages: List[Dict[str, Any]]):
        self.messages = messages
    
    def to_string(self) -> str:
        """Convert messages to a single string."""
        parts = []
        for message in self.messages:
            role = message.get("role", "unknown")
            content = message.get("content", "")
            parts.append(f"{role}: {content}")
        return "\n".join(parts)
    
    def to_messages(self) -> List[Dict[str, Any]]:
        return self.messages.copy()
    
    def __str__(self) -> str:
        return self.to_string()
    
    def __repr__(self) -> str:
        return f"ChatPromptValue(messages={self.messages!r})"


class BasePromptTemplate(ABC):
    """Base class for all prompt templates."""
    
    def __init__(self, 
                 input_variables: Optional[List[str]] = None, 
                 template_format: TemplateFormat = TemplateFormat.F_STRING,
                 partial_variables: Optional[Dict[str, Any]] = None):
        self.input_variables = input_variables or []
        self.template_format = template_format
        self.partial_variables = partial_variables or {}
    
    @abstractmethod
    def format(self, context: 'Context' = None, **kwargs: Any) -> str:
        pass
    
    @abstractmethod
    def format_prompt(self, context: 'Context' = None, **kwargs: Any) -> PromptValue:
        pass
    
    def _merge_partial_and_user_variables(self, context: 'Context' = None, **kwargs: Any) -> Dict[str, Any]:
        merged = {}
        try:
            for key, value in self.partial_variables.items():
                try:
                    if callable(value):
                        # If it's a function, try to pass context as a parameter
                        try:
                            # Check if the function accepts context parameter
                            import inspect
                            sig = inspect.signature(value)
                            if ("context" in sig.parameters.keys()) == True:
                                # If function accepts context parameter, pass the context
                                merged[key] = value(context=context)
                                logger.debug(f"prompt template parameter={sig.parameters} {sig.parameters.keys()} {'context' in sig.parameters.keys()}\nkey={key} value={merged[key]}")
                            else:
                                # Otherwise call directly
                                merged[key] = value()
                        except Exception as e:
                            # If error occurs, fallback to no-parameter call
                            try:
                                logger.error(f"Error calling function {key}: {e}")
                                merged[key] = value()
                            except Exception as e2:
                                # If still error, use default value or placeholder
                                logger.error(f"Error calling function {key} even without parameters: {e2}, using placeholder, traceback is {traceback.format_exc()}")
                                merged[key] = f"<Error calling function {key}: {e}>"
                    else:
                        merged[key] = value
                except Exception as e:
                    # If any error processing this variable, use placeholder
                    logger.warning(f"Error processing partial variable {key}: {e}, using placeholder")
                    merged[key] = f"<Error processing {key}: {e}>"
            
            merged.update(kwargs)
        except Exception as e:
            # If any error in the whole process, at least return kwargs
            logger.error(f"Error in _merge_partial_and_user_variables: {e}, returning only kwargs")
            merged = kwargs.copy()
        
        return merged
    
    def _validate_input_variables(self, variables: Dict[str, Any]) -> None:
        """Validate that all required input variables are provided."""
        missing_vars = set(self.input_variables) - set(variables.keys())
    
    def partial(self, **kwargs: Any) -> 'BasePromptTemplate':
        """Create a new prompt template with some variables pre-filled."""
        conflicts = set(kwargs.keys()) & set(self.input_variables)
        if conflicts:
            new_input_variables = [v for v in self.input_variables if v not in kwargs]
            new_partial_variables = {**self.partial_variables, **kwargs}
        else:
            new_input_variables = self.input_variables.copy()
            new_partial_variables = {**self.partial_variables, **kwargs}
        
        return self.__class__(
            input_variables=new_input_variables,
            template_format=self.template_format,
            partial_variables=new_partial_variables,
            **self._get_additional_kwargs()
        )
    
    def _get_additional_kwargs(self) -> Dict[str, Any]:
        """Get additional kwargs needed for creating new instances."""
        return {}
    
    @property
    def _prompt_type(self) -> str:
        """Return the prompt type identifier."""
        return "base"
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(input_variables={self.input_variables})"
    
    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}("
                f"input_variables={self.input_variables}, "
                f"template_format={self.template_format}, "
                f"partial_variables={self.partial_variables})") 