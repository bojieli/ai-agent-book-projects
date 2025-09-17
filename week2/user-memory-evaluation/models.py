"""Data models for the User Memory Evaluation Framework."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class MessageRole(str, Enum):
    """Message roles in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationMessage(BaseModel):
    """A single message in a conversation."""
    role: MessageRole
    content: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        return {"role": self.role.value, "content": self.content}


class ConversationHistory(BaseModel):
    """A conversation history containing multiple messages."""
    conversation_id: str = Field(description="Unique identifier for the conversation")
    timestamp: str = Field(description="Timestamp of the conversation")
    messages: List[ConversationMessage] = Field(description="List of messages in the conversation")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata about the conversation")
    
    @property
    def rounds(self) -> int:
        """Get the number of conversation rounds (user-assistant pairs)."""
        user_messages = sum(1 for msg in self.messages if msg.role == MessageRole.USER)
        return user_messages
    
    def validate_rounds(self, min_rounds: int = 45) -> bool:
        """Validate that the conversation has at least the minimum required rounds."""
        return self.rounds >= min_rounds


class TestCase(BaseModel):
    """A single test case for memory evaluation."""
    test_id: str = Field(description="Unique identifier for the test case")
    category: str = Field(description="Test category (layer1, layer2, or layer3)")
    title: str = Field(description="Title of the test case")
    description: str = Field(description="Description of what this test case evaluates")
    conversation_histories: List[ConversationHistory] = Field(description="Previous conversation histories")
    user_question: str = Field(description="User's question in the new conversation")
    evaluation_criteria: str = Field(description="Text criteria for evaluating the response")
    expected_behavior: Optional[str] = Field(default=None, description="Expected behavior from the agent (optional)")
    
    def validate(self) -> bool:
        """Validate the test case structure."""
        # Check category
        if self.category not in ["layer1", "layer2", "layer3"]:
            return False
        
        # Check conversation history requirements
        if self.category == "layer1" and len(self.conversation_histories) != 1:
            return False
        elif self.category in ["layer2", "layer3"] and len(self.conversation_histories) < 2:
            return False
        
        # Validate each conversation has at least 10 rounds
        for history in self.conversation_histories:
            if not history.validate_rounds(10):
                return False
        
        return True


class EvaluationResult(BaseModel):
    """Result of evaluating an agent's response."""
    test_id: str = Field(description="ID of the test case")
    reward: float = Field(description="Continuous reward score (0.0-1.0)")
    passed: Optional[bool] = Field(default=None, description="Optional binary pass/fail for backward compatibility")
    reasoning: str = Field(description="Detailed reasoning for the evaluation")
    required_info_found: Dict[str, float] = Field(description="Score for each required information piece (0.0-1.0)")
    suggestions: Optional[str] = Field(default=None, description="Suggestions for improvement")
    
    def to_summary(self) -> str:
        """Generate a summary of the evaluation result."""
        # Determine pass/fail based on reward threshold if not explicitly set
        if self.passed is not None:
            status = "PASSED" if self.passed else "FAILED"
        else:
            # Use 0.6 as default threshold for backward compatibility
            status = "PASSED" if self.reward >= 0.6 else "FAILED"
        summary = f"Test {self.test_id}: {status} (Reward: {self.reward:.2f})\n"
        summary += f"Reasoning: {self.reasoning}\n"
        if self.suggestions:
            summary += f"Suggestions: {self.suggestions}\n"
        return summary


class TestSuite(BaseModel):
    """A collection of test cases."""
    name: str = Field(description="Name of the test suite")
    version: str = Field(description="Version of the test suite")
    test_cases: List[TestCase] = Field(description="List of test cases")
    
    def get_by_category(self, category: str) -> List[TestCase]:
        """Get all test cases in a specific category."""
        return [tc for tc in self.test_cases if tc.category == category]
    
    def get_by_id(self, test_id: str) -> Optional[TestCase]:
        """Get a specific test case by ID."""
        for tc in self.test_cases:
            if tc.test_id == test_id:
                return tc
        return None
