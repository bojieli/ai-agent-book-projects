"""
Experience Learning Agent for GAIA
This module extends the AWorld Agent with learning from experience capabilities.
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib

from AWorld.aworld.agents.llm_agent import Agent
from AWorld.aworld.config.conf import AgentConfig
from AWorld.aworld.core.task import Task, TaskResponse
from AWorld.aworld.runner import Runners

logger = logging.getLogger(__name__)


class ExperienceAgent(Agent):
    """
    Extended Agent that can learn from successful trajectories and apply learned experiences.
    """
    
    def __init__(
        self,
        conf: AgentConfig,
        name: str = "experience_agent",
        system_prompt: str = "",
        learning_mode: bool = False,
        apply_experience: bool = False,
        experience_db_path: str = "./experience_db.json",
        knowledge_base: Optional['KnowledgeBase'] = None,
        summarizer: Optional['TrajectorySummarizer'] = None,
        **kwargs
    ):
        """
        Initialize the Experience Agent.
        
        Args:
            conf: Agent configuration
            name: Agent name
            system_prompt: Base system prompt
            learning_mode: Whether to capture and learn from successful trajectories
            apply_experience: Whether to apply learned experiences to new tasks
            experience_db_path: Path to store learned experiences
            knowledge_base: Knowledge base for retrieval
            summarizer: Trajectory summarizer instance
            **kwargs: Additional arguments for base Agent
        """
        super().__init__(conf=conf, name=name, system_prompt=system_prompt, **kwargs)
        
        self.learning_mode = learning_mode
        self.apply_experience = apply_experience
        self.experience_db_path = experience_db_path
        self.knowledge_base = knowledge_base
        self.summarizer = summarizer
        self.base_system_prompt = system_prompt
        
        # Load existing experiences if available
        self.experiences = self._load_experiences()
        
        # Track current task trajectory
        self.current_trajectory = []
        
    def _load_experiences(self) -> Dict[str, Any]:
        """Load existing experiences from file."""
        if os.path.exists(self.experience_db_path):
            try:
                with open(self.experience_db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load experiences: {e}")
        return {}
    
    def _save_experiences(self):
        """Save experiences to file."""
        try:
            with open(self.experience_db_path, 'w', encoding='utf-8') as f:
                json.dump(self.experiences, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save experiences: {e}")
    
    def _get_task_hash(self, question: str) -> str:
        """Generate a hash for a question to use as key."""
        return hashlib.md5(question.encode()).hexdigest()
    
    async def execute_task(self, task: Task) -> TaskResponse:
        """
        Execute a task with experience learning/application.
        
        Args:
            task: The task to execute
            
        Returns:
            TaskResponse with result
        """
        question = task.input
        original_prompt = self.system_prompt
        
        # Apply experience if enabled
        if self.apply_experience:
            relevant_experiences = self._get_relevant_experiences(question)
            if relevant_experiences:
                experience_text = self._format_experiences(relevant_experiences)
                self.system_prompt = f"{self.base_system_prompt}\n\n# Relevant Past Experiences:\n{experience_text}"
                logger.info(f"Applied {len(relevant_experiences)} relevant experiences to prompt")
        
        # Reset the manual-capture buffer for the new task. The real trajectory
        # is captured by AWorld and read back from the TaskResponse below.
        self.current_trajectory = []

        try:
            # Execute the task
            result = await Runners.run_task(task)
            task_response = result.get(task.id)

            # Recover the actual execution trajectory produced by AWorld's replay
            # buffer (TaskResponse.trajectory). Falls back to manually captured
            # actions when the framework did not record a trajectory.
            trajectory = self._extract_trajectory(task_response)

            # Process result for learning if enabled
            if self.learning_mode and task_response and self._is_successful(task_response, task):
                await self._learn_from_success(question, task_response, trajectory)

            return task_response
        finally:
            # Restore in a finally: if run_task raises and the caller moves on
            # to the next task, the injected experiences of THIS task must not
            # leak into later tasks that have no matching experiences of
            # their own.
            self.system_prompt = original_prompt
    
    def _extract_trajectory(self, task_response: Optional[TaskResponse]) -> List[Dict[str, Any]]:
        """
        Normalize the trajectory recorded by AWorld into the step format the
        TrajectorySummarizer expects: ``{'action': {'tool_name', 'action_name',
        'params'}}``.

        AWorld stores each step as a serialized replay-buffer ``DataRow`` whose
        ``exp_data.actions`` field holds the ``ActionModel`` objects taken at
        that step. When no framework trajectory is available (e.g. the runner
        did not populate it), we fall back to any actions that were captured
        manually via :meth:`capture_action`.

        Args:
            task_response: The response returned by ``Runners.run_task``.

        Returns:
            A list of normalized trajectory steps.
        """
        raw = getattr(task_response, "trajectory", None) if task_response else None
        if not raw:
            return list(self.current_trajectory)

        steps: List[Dict[str, Any]] = []
        for row in raw:
            actions = []
            if isinstance(row, dict):
                exp_data = row.get("exp_data") or {}
                if isinstance(exp_data, dict):
                    actions = exp_data.get("actions") or []
            for action in actions:
                if not isinstance(action, dict):
                    continue
                steps.append({
                    "action": {
                        "tool_name": action.get("tool_name") or "unknown",
                        "action_name": action.get("action_name") or "",
                        "params": action.get("params") or {},
                    }
                })

        # If normalization yielded nothing usable, keep the raw rows so the
        # summarizer at least reflects the correct step count.
        return steps or list(self.current_trajectory) or list(raw)

    def _get_relevant_experiences(self, question: str) -> List[Dict[str, Any]]:
        """
        Retrieve relevant experiences for a given question.
        
        Args:
            question: The current question
            
        Returns:
            List of relevant experiences
        """
        relevant = []
        
        # First check if knowledge base has preloaded experiences
        if self.knowledge_base:
            kb_experiences = self.knowledge_base.search(question, top_k=3)
            relevant.extend(kb_experiences)
        
        # Then check learned experiences
        if self.experiences:
            # Simple similarity check - can be enhanced with embeddings
            for exp_id, exp_data in self.experiences.items():
                if self._is_similar(question, exp_data.get('question', '')):
                    relevant.append(exp_data)
                    if len(relevant) >= 5:  # Limit to top 5 experiences
                        break
        
        return relevant
    
    def _is_similar(self, q1: str, q2: str) -> bool:
        """
        Simple similarity check between questions.
        Can be enhanced with semantic similarity using embeddings.
        
        Args:
            q1: First question
            q2: Second question
            
        Returns:
            True if questions are similar
        """
        # Simple keyword overlap for now
        if q1 is None or q2 is None:
            return False
        q1_words = set(q1.lower().split())
        q2_words = set(q2.lower().split())
        
        overlap = len(q1_words & q2_words)
        total = len(q1_words | q2_words)
        
        if total == 0:
            return False
            
        similarity = overlap / total
        return similarity > 0.3  # Threshold for similarity
    
    def _format_experiences(self, experiences: List[Dict[str, Any]]) -> str:
        """
        Format experiences for inclusion in system prompt.
        
        Args:
            experiences: List of experience dictionaries
            
        Returns:
            Formatted experience text
        """
        formatted = []
        for i, exp in enumerate(experiences, 1):
            exp_text = f"## Experience {i}:\n"
            
            if 'question' in exp:
                exp_text += f"- Similar Question: {exp['question']}\n"
            
            if 'summary' in exp:
                exp_text += f"- Key Insights: {exp['summary']}\n"
            
            if 'approach' in exp:
                exp_text += f"- Approach: {exp['approach']}\n"
                
            if 'tools_used' in exp:
                exp_text += f"- Tools Used: {', '.join(exp['tools_used'])}\n"
            
            formatted.append(exp_text)
        
        return "\n".join(formatted)
    
    def _is_successful(self, response: TaskResponse, task: Task) -> bool:
        """
        Determine if a task execution was successful.
        
        Args:
            response: The task response
            task: The original task
            
        Returns:
            True if the task was successful
        """
        # Check if answer exists and is not empty
        if not response or not response.answer:
            return False

        # Honor AWorld's own success signal when the framework provides one.
        success_flag = getattr(response, "success", None)
        status = getattr(response, "status", None)
        if success_flag is False:
            return False
        if status and str(status).lower() in {"failed", "cancelled"}:
            return False

        # Additional success criteria can be added here
        # For GAIA, we might check against known answers if available

        return True
    
    async def _learn_from_success(self, question: str, response: TaskResponse, trajectory: List[Dict[str, Any]]):
        """
        Learn from a successful task execution.
        
        Args:
            question: The original question
            response: The successful response
            trajectory: The execution trajectory
        """
        if not self.summarizer:
            logger.warning("No summarizer configured, skipping learning")
            return
        
        try:
            # Summarize the trajectory
            summary = await self.summarizer.summarize(question, response, trajectory)
            
            # Store the experience
            exp_id = self._get_task_hash(question)
            self.experiences[exp_id] = {
                'question': question,
                'answer': response.answer,
                'summary': summary.get('summary', ''),
                'approach': summary.get('approach', ''),
                'tools_used': summary.get('tools_used', []),
                'key_insights': summary.get('key_insights', []),
                'general_strategy': summary.get('general_strategy', ''),
                'num_steps': len(trajectory),
                'timestamp': datetime.now().isoformat(),
                'success': True
            }
            
            # Save to disk
            self._save_experiences()
            
            logger.info(f"Learned from successful execution: {exp_id[:8]}")
            
        except Exception as e:
            logger.error(f"Failed to learn from success: {e}")
    
    def capture_action(self, action: Dict[str, Any]):
        """
        Capture an action in the current trajectory.
        
        Args:
            action: The action to capture
        """
        if self.learning_mode:
            self.current_trajectory.append({
                'timestamp': datetime.now().isoformat(),
                'action': action
            })
