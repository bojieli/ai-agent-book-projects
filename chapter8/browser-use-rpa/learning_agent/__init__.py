"""
Learning Agent for Browser-Use RPA

A wrapper system that adds learning and experience-replay capabilities to browser-use.
This agent can learn from successful task executions and replay learned workflows efficiently.
"""

from .knowledge_base import KnowledgeBase
from .workflow import Workflow, WorkflowStep, StatePredicate, PredicateType, WorkflowStatus

__all__ = [
    'LearningAgent', 'KnowledgeBase', 'Workflow', 'WorkflowStep',
    'StatePredicate', 'PredicateType', 'WorkflowStatus'
]


def __getattr__(name):
    """Keep the data model usable in offline tests without browser-use."""
    if name == 'LearningAgent':
        from .agent import LearningAgent
        return LearningAgent
    raise AttributeError(name)
