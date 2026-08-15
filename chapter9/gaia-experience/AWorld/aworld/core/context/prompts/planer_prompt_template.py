# coding: utf-8
# Copyright (c) 2025 inclusionAI.
"""
PlanerPromptTemplate Implementation

Specialized prompt template for Plan-and-Execute agents that handles:
1. Unified planning and replanning prompt generation
2. JSON response parsing with error handling
3. Plan output validation and structuring
4. Integration with PlanerContext for state-aware template rendering
"""

import json
import traceback
from typing import Dict, Any, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field

from aworld.core.context.prompts.string_prompt_template import PromptTemplate
from aworld.logs.util import logger

# Import type hints
if TYPE_CHECKING:
    from aworld.core.context.base import PlanerContext


class PlanOutputParser(BaseModel):
    """
    Parser component for handling LLM planning responses.
    
    This parser handles JSON extraction, validation, and error recovery
    for planning agent responses.
    """
    
    def parse_llm_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM with error handling."""
        try:
            # Try to extract JSON from response
            response = response.strip()
            
            # Handle common cases where LLM adds extra text
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end]
            elif "{" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                response = response[start:end]
            
            parsed_data = json.loads(response)
            
            # Validate required fields
            if not self._validate_plan_response(parsed_data):
                logger.warning("Plan response validation failed, using fallback")
                return self._create_fallback_response(response)
            
            return parsed_data
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM JSON response: {str(e)}")
            logger.warning(f"Raw response: {response}")
            return self._create_fallback_response(response)
        except Exception as e:
            logger.error(f"Unexpected error parsing plan response: {str(e)}")
            return self._create_fallback_response(response)
    
    def _validate_plan_response(self, data: Dict[str, Any]) -> bool:
        """Validate that the parsed response has required fields."""
        required_fields = ["status", "reason"]
        
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # If status is continue, steps should be present
        if data.get("status") == "continue" and not data.get("steps"):
            logger.warning("Status is 'continue' but no steps provided")
            return False
        
        # Validate steps structure if present
        if "steps" in data:
            for i, step in enumerate(data["steps"]):
                if not self._validate_step_structure(step, i):
                    return False
        
        return True
    
    def _validate_step_structure(self, step: Dict[str, Any], index: int) -> bool:
        """Validate individual step structure."""
        required_step_fields = ["step_id", "description", "action"]
        
        for field in required_step_fields:
            if field not in step:
                logger.warning(f"Step {index} missing required field: {field}")
                return False
        
        # Validate action structure
        action = step.get("action", {})
        required_action_fields = ["tool_name", "action_name", "params"]
        
        for field in required_action_fields:
            if field not in action:
                logger.warning(f"Step {index} action missing required field: {field}")
                return False
        
        return True
    
    def _create_fallback_response(self, raw_response: str) -> Dict[str, Any]:
        """Create a fallback response when parsing fails."""
        return {
            "status": "error",
            "reason": "Failed to parse LLM response",
            "error": "JSON parsing failed",
            "raw_response": raw_response[:500],  # Truncate long responses
            "steps": []
        }


class PlanerPromptTemplate(PromptTemplate):
    """
    Specialized prompt template for Plan-and-Execute agents.
    
    This template provides unified planning and replanning capabilities
    with integrated response parsing through PlanOutputParser and
    state-aware rendering using PlanerContext.
    """
    
    def __init__(self, 
                 template: Optional[str] = None, 
                 planer_context: Optional["PlanerContext"] = None,
                 **kwargs):
        """Initialize PlanerPromptTemplate with optional PlanerContext."""
        if template is None:
            template = self._get_default_planning_template()
        
        super().__init__(template=template, **kwargs)
        
        # Store reference to PlanerContext
        self.planer_context = planer_context
        
        # Initialize the output parser
        self.output_parser = PlanOutputParser()
        
        logger.debug(f"PlanerPromptTemplate initialized with integrated output parser and context: {planer_context is not None}")
    
    def set_planer_context(self, planer_context: "PlanerContext"):
        """Set or update the PlanerContext reference."""
        self.planer_context = planer_context
        logger.debug("PlanerContext reference updated in PlanerPromptTemplate")
    
    def _get_default_planning_template(self) -> str:
        """Get the default unified planning template."""
        return """You are an expert task planner and replanner. Analyze the current situation and determine the next steps.

**Available Tools:** {available_tools}

**Current Situation:**
- Original Goal: {original_goal}
- User Input: {user_input}
- Is Initial Planning: {is_initial}
- Current Iteration: {current_iteration}
- Previous Execution Results: {execution_results}
- Completed Steps: {completed_steps}
- Failed Steps: {failed_steps}
- Execution History: {execution_history}

**Instructions:**
1. If this is initial planning (is_initial=true), create a complete plan for the user input
2. If this is replanning (is_initial=false), analyze execution results and determine next actions
3. Each step should use one of the available tools and be independently executable
4. Consider dependencies between steps
5. If goal is achieved, set status to "completed"

**Output Format (JSON):**
{{
    "status": "continue" | "completed",
    "reason": "Brief explanation of the decision",
    "goal": "Overall goal description", 
    "steps": [
        {{
            "step_id": <unique_id>,
            "description": "What this step accomplishes",
            "action": {{
                "tool_name": "tool_name",
                "action_name": "specific_action",
                "params": {{"param1": "value1", "param2": "value2"}}
            }},
            "dependencies": []
        }}
    ]
}}

Response with valid JSON only."""
    
    def parse_response(self, llm_response: str) -> Dict[str, Any]:
        """Parse LLM response using the integrated output parser."""
        return self.output_parser.parse_llm_json_response(llm_response)
    
    def create_planning_context(self, 
                                user_input: str,
                                available_tools: list,
                                is_initial: bool = True,
                                execution_results: str = "No previous execution",
                                **kwargs) -> str:
        # Extract information from PlanerContext
        context_data = {
            "user_input": user_input,
            "original_goal": self.planer_context.original_goal or user_input,
            "available_tools": ", ".join(available_tools) if available_tools else "No tools available",
            "is_initial": str(is_initial).lower(),
            "current_iteration": self.planer_context.current_iteration,
            "execution_results": execution_results,
            "completed_steps": self._extract_completed_steps(),
            "failed_steps": self._extract_failed_steps(),
            "execution_history": self._format_execution_history(),
            **kwargs
        }
        
        logger.debug(f"Creating planning context from PlanerContext: iteration={self.planer_context.current_iteration}")
        return self.format(**context_data)
    
    def _extract_completed_steps(self) -> str:
        """Extract completed steps from PlanerContext."""
        if not self.planer_context or not self.planer_context.current_step:
            return "None"
        
        completed_steps = []
        for step in self.planer_context.current_step.steps:
            if step.status == "completed":
                completed_steps.append(str(step.step_id))
        
        return ", ".join(completed_steps) if completed_steps else "None"
    
    def _extract_failed_steps(self) -> str:
        """Extract failed steps from PlanerContext."""
        if not self.planer_context or not self.planer_context.current_step:
            return "None"
        
        failed_steps = []
        for step in self.planer_context.current_step.steps:
            if step.status == "failed":
                failed_steps.append(str(step.step_id))
        
        return ", ".join(failed_steps) if failed_steps else "None"
    
    def _format_execution_history(self) -> str:
        """Format execution history from PlanerContext."""
        if not self.planer_context or not self.planer_context.step_history:
            return "No previous execution history"
        
        history_summary = []
        for i, plan in enumerate(self.planer_context.step_history):
            plan_summary = f"Plan {i+1} (Iteration {plan.iteration}): {plan.goal}"
            step_count = len(plan.steps)
            completed_count = len([s for s in plan.steps if s.status == "completed"])
            plan_summary += f" - {completed_count}/{step_count} steps completed"
            history_summary.append(plan_summary)
        
        return "\n".join(history_summary)
    
    def validate_and_parse_response(self, llm_response: str) -> tuple[bool, Dict[str, Any]]:
        try:
            parsed_data = self.parse_response(llm_response)
            
            # Check if parsing was successful
            if parsed_data.get("status") == "error":
                return False, parsed_data
            
            return True, parsed_data
            
        except Exception as e:
            logger.error(f"Error in validate_and_parse_response: {str(e)}")
            return False, {
                "status": "error",
                "reason": f"Parsing error: {str(e)}",
                "error": str(e)
            }
    
    @classmethod
    def create_with_custom_template(cls, custom_template: str, planer_context: Optional["PlanerContext"] = None) -> "PlanerPromptTemplate":
        """Create PlanerPromptTemplate with a custom template and optional PlanerContext."""
        return cls(template=custom_template, planer_context=planer_context)
    
    @classmethod
    def create_default(cls, planer_context: Optional["PlanerContext"] = None) -> "PlanerPromptTemplate":
        """Create PlanerPromptTemplate with default settings and optional PlanerContext."""
        return cls(planer_context=planer_context)
    
    @classmethod
    def create_with_context(cls, planer_context: "PlanerContext", custom_template: Optional[str] = None) -> "PlanerPromptTemplate":
        """Create PlanerPromptTemplate with PlanerContext and optional custom template."""
        return cls(template=custom_template, planer_context=planer_context)
