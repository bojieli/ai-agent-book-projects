"""User Memory Evaluation Framework Package."""

# Import Config first to avoid conflicts
from .config import Config

# Then import models
from .models import (
    TestCase, 
    ConversationHistory, 
    ConversationMessage,
    EvaluationResult, 
    TestSuite, 
    TestCaseExporter, 
    MessageRole
)

# Then evaluator (which depends on config and models)
from .evaluator import LLMEvaluator, BatchEvaluator

# Finally framework (which depends on all above)
from .framework import UserMemoryEvaluationFramework

__all__ = [
    'UserMemoryEvaluationFramework',
    'TestCase',
    'ConversationHistory', 
    'ConversationMessage',
    'EvaluationResult',
    'TestSuite',
    'TestCaseExporter',
    'MessageRole',
    'LLMEvaluator',
    'BatchEvaluator',
    'Config'
]
