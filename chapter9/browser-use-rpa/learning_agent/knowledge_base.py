"""
Knowledge Base for storing and retrieving learned workflows.

This module provides persistent storage and intelligent retrieval of workflows,
including intent matching and workflow selection.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass
import uuid

from .workflow import Workflow, WorkflowStep, WorkflowStatus


logger = logging.getLogger(__name__)


@dataclass
class IntentMatch:
    """Represents a match between a task intent and a stored workflow"""
    workflow: Workflow
    confidence: float  # 0.0 to 1.0
    match_reason: str


class KnowledgeBase:
    """
    Manages storage and retrieval of learned workflows.
    
    The knowledge base provides:
    - Persistent storage of workflows
    - Intent matching to find relevant workflows
    - Performance tracking and optimization
    """
    
    def __init__(self, storage_path: str = "./knowledge_base"):
        """
        Initialize the knowledge base.
        
        Args:
            storage_path: Directory path for storing workflow data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # In-memory cache of workflows
        self.workflows: Dict[str, Workflow] = {}
        
        # Intent index for fast matching
        self.intent_index: Dict[str, List[str]] = {}  # intent -> [workflow_ids]
        
        # Load existing workflows
        self.load_all_workflows()
    
    def save_workflow(self, workflow: Workflow) -> None:
        """
        Save a workflow to persistent storage.
        
        Args:
            workflow: The workflow to save
        """
        if workflow.validation_status != WorkflowStatus.VALIDATED:
            raise ValueError(
                "Only a workflow validated by complete replay in a reset environment may enter the ability store"
            )

        # Generate ID if not present
        if not workflow.workflow_id:
            workflow.workflow_id = str(uuid.uuid4())
        
        # Save to file
        workflow_file = self.storage_path / f"workflow_{workflow.workflow_id}.json"
        with open(workflow_file, 'w', encoding='utf-8') as f:
            f.write(workflow.to_json())
        
        # Update in-memory cache
        self.workflows[workflow.workflow_id] = workflow
        
        # Update intent index
        if workflow.intent not in self.intent_index:
            self.intent_index[workflow.intent] = []
        if workflow.workflow_id not in self.intent_index[workflow.intent]:
            self.intent_index[workflow.intent].append(workflow.workflow_id)
        
        logger.info(f"Saved workflow '{workflow.workflow_id}' for intent: {workflow.intent}")

    def save_candidate(self, workflow: Workflow) -> None:
        """Persist a candidate for audit without making it retrievable."""
        if not workflow.workflow_id:
            workflow.workflow_id = str(uuid.uuid4())
        workflow.validation_status = WorkflowStatus.CANDIDATE
        candidate_file = self.storage_path / f"candidate_{workflow.workflow_id}.json"
        candidate_file.write_text(workflow.to_json(), encoding="utf-8")

    def publish_validated(self, workflow: Workflow) -> None:
        """Move a replay-validated candidate into the retrievable store."""
        self.save_workflow(workflow)
        candidate_file = self.storage_path / f"candidate_{workflow.workflow_id}.json"
        if candidate_file.exists():
            candidate_file.unlink()

    def invalidate_workflow(self, workflow_id: str, reason: str) -> None:
        """Remove a broken workflow from retrieval and preserve it for audit."""
        workflow = self.workflows.pop(workflow_id, None)
        if not workflow:
            return
        workflow.mark_invalid(reason)
        stable_file = self.storage_path / f"workflow_{workflow_id}.json"
        if stable_file.exists():
            stable_file.unlink()
        invalid_file = self.storage_path / f"invalid_{workflow_id}.json"
        invalid_file.write_text(workflow.to_json(), encoding="utf-8")
        ids = self.intent_index.get(workflow.intent, [])
        self.intent_index[workflow.intent] = [item for item in ids if item != workflow_id]
    
    def load_all_workflows(self) -> None:
        """Load all workflows from storage into memory."""
        workflow_files = list(self.storage_path.glob("workflow_*.json"))
        
        for workflow_file in workflow_files:
            try:
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    workflow_data = json.load(f)
                    workflow = Workflow.from_dict(workflow_data)
                    
                    if workflow.validation_status != WorkflowStatus.VALIDATED:
                        logger.warning("Ignoring unvalidated workflow file: %s", workflow_file)
                        continue

                    # Add to cache
                    self.workflows[workflow.workflow_id] = workflow
                    
                    # Update intent index
                    if workflow.intent not in self.intent_index:
                        self.intent_index[workflow.intent] = []
                    self.intent_index[workflow.intent].append(workflow.workflow_id)
                    
            except Exception as e:
                logger.error(f"Failed to load workflow from {workflow_file}: {e}")
        
        logger.info(f"Loaded {len(self.workflows)} workflows from storage")
    
    def find_workflow_for_task(self, task_description: str) -> Optional[IntentMatch]:
        """
        Find the best matching workflow for a given task.
        
        Args:
            task_description: Natural language description of the task
        
        Returns:
            The best matching workflow with confidence score, or None if no match
        """
        matches = self.find_matching_workflows(task_description)
        
        if matches:
            # Return the highest confidence match
            return max(matches, key=lambda m: m.confidence)
        
        return None
    
    def find_matching_workflows(self, task_description: str) -> List[IntentMatch]:
        """
        Find all workflows that might match the given task.
        
        Args:
            task_description: Natural language description of the task
        
        Returns:
            List of matching workflows sorted by confidence
        """
        matches = []
        
        # Normalize task description for matching
        task_lower = task_description.lower()
        
        for workflow in self.workflows.values():
            if workflow.validation_status != WorkflowStatus.VALIDATED:
                continue
            confidence, reason = self._calculate_match_confidence(task_lower, workflow)
            
            if confidence > 0.3:  # Minimum threshold
                matches.append(IntentMatch(
                    workflow=workflow,
                    confidence=confidence,
                    match_reason=reason
                ))
        
        # Sort by confidence (highest first)
        matches.sort(key=lambda m: m.confidence, reverse=True)
        
        return matches
    
    def _calculate_match_confidence(self, task: str, workflow: Workflow) -> Tuple[float, str]:
        """
        Calculate how well a workflow matches a task description.
        
        Args:
            task: Normalized task description
            workflow: Workflow to match against
        
        Returns:
            Tuple of (confidence_score, match_reason)
        """
        confidence = 0.0
        reasons = []
        
        # Check intent match
        intent_lower = workflow.intent.lower()
        
        # Exact intent match
        if intent_lower in task:
            confidence += 0.5
            reasons.append("exact intent match")
        
        # Keyword matching for common patterns
        intent_keywords = set(intent_lower.split())
        task_keywords = set(task.split())
        
        # Calculate keyword overlap
        common_keywords = intent_keywords & task_keywords
        if common_keywords:
            keyword_score = len(common_keywords) / len(intent_keywords)
            confidence += keyword_score * 0.3
            reasons.append(f"keyword match: {', '.join(common_keywords)}")
        
        # Check for action verbs (send, write, compose, create, etc.)
        action_verbs = {
            'send': ['send', 'email', 'mail', 'message'],
            'write': ['write', 'compose', 'draft', 'create'],
            'search': ['search', 'find', 'look', 'query'],
            'check': ['check', 'verify', 'view', 'see'],
            'login': ['login', 'signin', 'authenticate', 'log in', 'sign in'],
            'order': ['order', 'buy', 'purchase', 'checkout'],
            'book': ['book', 'reserve', 'schedule']
        }
        
        for action_group, verbs in action_verbs.items():
            if any(verb in intent_lower for verb in verbs) and any(verb in task for verb in verbs):
                confidence += 0.2
                reasons.append(f"action verb match: {action_group}")
                break
        
        # Boost confidence for recently successful workflows
        if workflow.success_count > workflow.failure_count:
            success_rate = workflow.success_count / (workflow.success_count + workflow.failure_count)
            confidence *= (1 + success_rate * 0.2)
            if success_rate > 0.8:
                reasons.append(f"high success rate: {success_rate:.0%}")
        
        # Compile reason string
        reason = "; ".join(reasons) if reasons else "partial match"
        
        return confidence, reason
    
    def update_workflow_metrics(self, 
                               workflow_id: str, 
                               success: bool,
                               execution_time: float,
                               model_calls_saved: int = 0) -> None:
        """
        Update performance metrics for a workflow after execution.
        
        Args:
            workflow_id: ID of the workflow that was executed
            success: Whether the execution was successful
            execution_time: Time taken to execute the workflow
            model_calls_saved: Number of LLM calls saved by using this workflow
        """
        if workflow_id in self.workflows:
            workflow = self.workflows[workflow_id]
            
            # Update counters
            if success:
                workflow.success_count += 1
            else:
                workflow.failure_count += 1
            
            # Update timing
            workflow.last_used_at = datetime.now()
            
            # Update average execution time
            total_executions = workflow.success_count + workflow.failure_count
            workflow.average_execution_time = (
                (workflow.average_execution_time * (total_executions - 1) + execution_time) 
                / total_executions
            )
            
            # Track model calls saved
            workflow.model_calls_saved += model_calls_saved
            
            # Save updated workflow
            self.save_workflow(workflow)
            
            logger.info(f"Updated metrics for workflow {workflow_id}: "
                       f"success={success}, time={execution_time:.2f}s, "
                       f"total_saved_calls={workflow.model_calls_saved}")
    
    def get_statistics(self) -> Dict[str, any]:
        """
        Get statistics about the knowledge base.
        
        Returns:
            Dictionary containing knowledge base statistics
        """
        total_workflows = len(self.workflows)
        total_executions = sum(w.success_count + w.failure_count for w in self.workflows.values())
        total_successes = sum(w.success_count for w in self.workflows.values())
        total_model_calls_saved = sum(w.model_calls_saved for w in self.workflows.values())
        
        success_rate = (total_successes / total_executions * 100) if total_executions > 0 else 0
        
        return {
            "total_workflows": total_workflows,
            "total_executions": total_executions,
            "total_successes": total_successes,
            "success_rate": f"{success_rate:.1f}%",
            "total_model_calls_saved": total_model_calls_saved,
            "unique_intents": len(self.intent_index)
        }
    
    def clear_all(self) -> None:
        """Clear all workflows from the knowledge base (use with caution)."""
        # Clear files
        for workflow_file in self.storage_path.glob("workflow_*.json"):
            workflow_file.unlink()
        
        # Clear memory
        self.workflows.clear()
        self.intent_index.clear()
        
        logger.info("Cleared all workflows from knowledge base")
