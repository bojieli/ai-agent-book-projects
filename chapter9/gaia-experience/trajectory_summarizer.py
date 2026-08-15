"""
Trajectory Summarizer for Learning from Experience
This module summarizes successful task trajectories into reusable experiences.
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional
from AWorld.aworld.models.llm import get_llm_model
from AWorld.aworld.config.conf import AgentConfig

logger = logging.getLogger(__name__)


class TrajectorySummarizer:
    """
    Summarizes task execution trajectories into natural language experiences.
    """
    
    def __init__(
        self,
        llm_config: Optional[AgentConfig] = None,
        model_name: str = "gpt-5.6-luna",
        temperature: float = 0.3
    ):
        """
        Initialize the trajectory summarizer.
        
        Args:
            llm_config: LLM configuration
            model_name: Model to use for summarization
            temperature: Temperature for generation
        """
        self.llm_config = llm_config
        self.model_name = model_name
        self.temperature = temperature
        
        # Initialize LLM for summarization
        if llm_config:
            self.llm = get_llm_model(
                provider=llm_config.llm_provider,
                model_name=model_name,
                api_key=llm_config.llm_api_key,
                base_url=llm_config.llm_base_url
            )
        else:
            self.llm = None
    
    async def summarize(
        self,
        question: str,
        response: Any,
        trajectory: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Summarize a successful trajectory into reusable experience.
        
        Args:
            question: The original question
            response: The successful response
            trajectory: The execution trajectory
            
        Returns:
            Summarized experience dictionary
        """
        if not self.llm:
            # Fallback to rule-based summarization
            return self._rule_based_summary(question, response, trajectory)
        
        try:
            # Prepare trajectory for LLM
            trajectory_text = self._format_trajectory(trajectory)
            
            # Create summarization prompt
            prompt = self._create_summary_prompt(question, response.answer, trajectory_text)
            
            # Get summary from LLM
            summary_response = await self.llm.acompletion(
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing task execution trajectories and extracting key insights for future problem-solving."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature
            )
            
            # Parse the response
            summary = self._parse_llm_summary(summary_response)
            
            # Extract tools used from trajectory
            tools_used = self._extract_tools_from_trajectory(trajectory)
            summary['tools_used'] = tools_used
            
            return summary
            
        except Exception as e:
            logger.error(f"LLM summarization failed: {e}")
            # Fallback to rule-based
            return self._rule_based_summary(question, response, trajectory)
    
    def _create_summary_prompt(self, question: str, answer: str, trajectory_text: str) -> str:
        """
        Create a prompt for LLM summarization.
        
        Args:
            question: The original question
            answer: The final answer
            trajectory_text: Formatted trajectory
            
        Returns:
            Prompt string
        """
        prompt = f"""Analyze this successful task execution and extract key insights for solving similar problems in the future.

Question: {question}
Final Answer: {answer}

Execution Trajectory:
{trajectory_text}

Please provide a concise summary with the following structure:
1. APPROACH: Describe the high-level approach taken to solve this problem (2-3 sentences)
2. KEY INSIGHTS: What are the critical insights or patterns that made this solution successful? (2-3 bullet points)
3. GENERAL STRATEGY: How could this approach be generalized to similar problems? (1-2 sentences)

Format your response as JSON with keys: "summary", "approach", "key_insights" (list), "general_strategy"
"""
        return prompt
    
    def _parse_llm_summary(self, response: Any) -> Dict[str, Any]:
        """
        Parse LLM response into structured summary.
        
        Args:
            response: LLM response object
            
        Returns:
            Parsed summary dictionary
        """
        try:
            # Extract JSON from response
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                summary_json = json.loads(json_match.group())
                
                return {
                    'summary': summary_json.get('summary', ''),
                    'approach': summary_json.get('approach', ''),
                    'key_insights': summary_json.get('key_insights', []),
                    'general_strategy': summary_json.get('general_strategy', '')
                }
        except Exception as e:
            logger.error(f"Failed to parse LLM summary: {e}")
        
        # Fallback: treat entire response as summary
        return {
            'summary': content,
            'approach': 'See summary for details',
            'key_insights': [],
            'general_strategy': ''
        }
    
    def _rule_based_summary(
        self,
        question: str,
        response: Any,
        trajectory: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a rule-based summary when LLM is not available.
        
        Args:
            question: The original question
            response: The successful response
            trajectory: The execution trajectory
            
        Returns:
            Summary dictionary
        """
        # Extract tools used
        tools_used = self._extract_tools_from_trajectory(trajectory)
        
        # Analyze trajectory patterns
        action_types = self._analyze_action_types(trajectory)
        
        # Create basic summary
        summary = {
            'summary': f"Successfully answered question using {len(tools_used)} tools with {len(trajectory)} steps.",
            'approach': self._infer_approach(action_types, tools_used),
            'key_insights': self._extract_key_patterns(trajectory),
            'general_strategy': f"Use combination of {', '.join(tools_used[:3])} for similar tasks",
            'tools_used': tools_used
        }
        
        return summary
    
    def _format_trajectory(self, trajectory: List[Dict[str, Any]]) -> str:
        """
        Format trajectory for readability.
        
        Args:
            trajectory: Raw trajectory data
            
        Returns:
            Formatted trajectory string
        """
        formatted_steps = []
        
        for i, step in enumerate(trajectory, 1):
            action = step.get('action', {})
            
            # Extract key information
            tool_name = action.get('tool_name') or 'unknown'
            action_name = action.get('action_name', '')
            params = action.get('params', {})
            
            # Format step
            step_text = f"Step {i}: {tool_name}"
            if action_name:
                step_text += f".{action_name}"
            
            if params:
                # Simplify params for readability
                param_str = ', '.join([f"{k}={self._truncate_value(v)}" for k, v in params.items()])
                step_text += f"({param_str})"
            
            formatted_steps.append(step_text)
        
        return '\n'.join(formatted_steps)
    
    def _truncate_value(self, value: Any, max_length: int = 50) -> str:
        """
        Truncate long values for display.
        
        Args:
            value: Value to truncate
            max_length: Maximum length
            
        Returns:
            Truncated string representation
        """
        str_value = str(value)
        if len(str_value) > max_length:
            return str_value[:max_length] + "..."
        return str_value
    
    def _extract_tools_from_trajectory(self, trajectory: List[Dict[str, Any]]) -> List[str]:
        """
        Extract unique tools used from trajectory.
        
        Args:
            trajectory: Execution trajectory
            
        Returns:
            List of unique tool names
        """
        tools = set()
        
        for step in trajectory:
            action = step.get('action', {})
            tool_name = action.get('tool_name')
            
            if tool_name:
                # Clean tool name
                base_tool = tool_name.split('__')[0] if '__' in tool_name else tool_name
                tools.add(base_tool)
        
        return sorted(list(tools))
    
    def _analyze_action_types(self, trajectory: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Analyze types of actions in trajectory.
        
        Args:
            trajectory: Execution trajectory
            
        Returns:
            Count of each action type
        """
        action_types = {}
        
        for step in trajectory:
            action = step.get('action', {})
            tool_name = action.get('tool_name') or 'unknown'
            
            # Categorize action
            if 'search' in tool_name.lower():
                category = 'search'
            elif 'browser' in tool_name.lower() or 'web' in tool_name.lower():
                category = 'web_interaction'
            elif 'file' in tool_name.lower() or 'read' in tool_name.lower():
                category = 'file_operation'
            elif 'calculate' in tool_name.lower() or 'compute' in tool_name.lower():
                category = 'computation'
            else:
                category = 'other'
            
            action_types[category] = action_types.get(category, 0) + 1
        
        return action_types
    
    def _infer_approach(self, action_types: Dict[str, int], tools_used: List[str]) -> str:
        """
        Infer the approach based on action types.
        
        Args:
            action_types: Count of action types
            tools_used: List of tools used
            
        Returns:
            Inferred approach description
        """
        # Determine dominant strategy
        if action_types.get('search', 0) > 2:
            approach = "Information gathering through multiple searches"
        elif action_types.get('web_interaction', 0) > 3:
            approach = "Web-based research and navigation"
        elif action_types.get('file_operation', 0) > 1:
            approach = "File analysis and processing"
        elif action_types.get('computation', 0) > 0:
            approach = "Computational problem solving"
        else:
            approach = "Multi-step problem decomposition"
        
        # Add tool specifics
        if tools_used:
            approach += f" using {', '.join(tools_used[:2])}"
        
        return approach
    
    def _extract_key_patterns(self, trajectory: List[Dict[str, Any]]) -> List[str]:
        """
        Extract key patterns from trajectory.
        
        Args:
            trajectory: Execution trajectory
            
        Returns:
            List of key patterns/insights
        """
        patterns = []
        
        # Check for search refinement pattern
        search_count = sum(1 for step in trajectory 
                          if 'search' in str(step.get('action', {})).lower())
        if search_count > 1:
            patterns.append("Multiple searches refined the query")
        
        # Check for verification pattern
        if len(trajectory) > 5:
            patterns.append("Thorough verification of results")
        
        # Check for tool combination
        tools = self._extract_tools_from_trajectory(trajectory)
        if len(tools) > 2:
            patterns.append(f"Combined {len(tools)} different tools effectively")
        
        # Limit to 3 patterns
        return patterns[:3] if patterns else ["Direct problem solving approach"]
