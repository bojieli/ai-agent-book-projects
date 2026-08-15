import logging
import re
from typing import Dict, Any, Optional, Callable, List

from aworld.core.context.base import Context
from aworld.core.context.prompts.dynamic_variables import create_simple_field_getter, create_multiple_field_getters, \
    get_field_values_from_list

# Import system_prompt directly from the module
try:
    from aworld.prompt.templates.prompt import system_prompt as default_system_prompt
except ImportError:
    default_system_prompt = ""

class Prompt:
    """
    Prompt processing class, responsible for loading templates and rendering variables
    """
    
    def __init__(self, template: str = None, context: Context = None) -> None:
        """
        Initialize Prompt class
        
        Args:
            template: Template content. If None, will load default system prompt.
        """
        if template is None:
            self.template_content = default_system_prompt
        else:
            self.template_content = template
            
        # Extract variables from the template
        self.prompt_variables = self._extract_variables(self.template_content)
        self.context = context
    
    def _extract_variables(self, template_content: str) -> List[str]:
        """
        Extract variables from the template
        
        Args:
            template_content: Template content
            
        Returns:
            List of variables
        """
        # Use regular expression to extract {{variable}} format variables
        pattern = r'\{\{([a-zA-Z0-9_]+)\}\}'
        if not template_content:
            return []
        try:
            matches = re.findall(pattern, template_content)
            # Remove duplicates
            return list(set(matches))
        except Exception as e:
            logging.warning(f"Error extracting variables from template: {str(e)}")
            return []

    
    def _get_variable_values_from_api(self, variables: List[str]) -> Dict[str, Any]:
        """
        Get variable values from API
        
        Args:
            variables: List of variables
            
        Returns:
            Dictionary of variable values, key is variable name, value is variable value
        """
        # This is a mock implementation, should be replaced with actual API calls in real use
        result = {}
        context = self.context
        #getter = create_multiple_field_getters(variables, context)
        if context and variables:
            field_paths = variables
            try:
                result = get_field_values_from_list(context=context, field_paths=field_paths,default="")
            except Exception as e:
                logging.warning(f"Error getting variable values from API: {str(e)}")
                return None
        return result
    
    def get_prompt(self, variables: Dict[str, Any] = None, variable_resolver: Optional[Callable[[List[str]], Dict[str, Any]]] = None) -> str:
        """
        Render template, replace variables
        
        Args:
            variables: Optional variable dictionary, if provided, will override API values
            variable_resolver: Optional variable resolver function, used to get variable values, higher priority than built-in API method
            
        Returns:
            Rendered content
        """
        if variables is None:
            variables = {}
        
        # Get variable values
        if variable_resolver:
            # If custom variable resolver is provided, use it
            resolved_variables = variable_resolver(self.prompt_variables)
        else:
            # Otherwise use the built-in API method
            resolved_variables = self._get_variable_values_from_api(self.prompt_variables)
        
        # Override API values with provided variables
        for var_name, var_value in variables.items():
            if var_value is not None:  # Only override when value is not None
                resolved_variables[var_name] = var_value
        
        # Render template
        rendered_content = self.template_content
        
        # Replace variables
        for var_name, var_value in resolved_variables.items():
            if  var_value:
                placeholder = f"{{{{{var_name}}}}}"
                rendered_content = rendered_content.replace(placeholder, str(var_value))
            
        return rendered_content

# Simplified API, only keep the prompt creation functionality
def create_prompt(template_content: str) -> Prompt:
    """
    Create Prompt from string
    
    Args:
        template_content: Template content
        
    Returns:
        Prompt object
    """
    return Prompt(template_content)