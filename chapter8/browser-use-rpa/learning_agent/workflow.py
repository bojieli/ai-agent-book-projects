"""
Workflow data structures for capturing and storing browser action sequences.

This module defines the structures used to represent learned workflows,
including individual steps and complete action sequences.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import json


class ActionType(Enum):
    """Types of actions that can be recorded in a workflow"""
    NAVIGATE = "navigate"
    CLICK = "click"
    INPUT_TEXT = "input_text"
    SELECT_OPTION = "select_option"
    SCROLL = "scroll"
    WAIT = "wait"
    SWITCH_TAB = "switch_tab"
    CLOSE_TAB = "close_tab"
    UPLOAD_FILE = "upload_file"


class PredicateType(Enum):
    """Machine-checkable browser state predicates."""
    URL_CONTAINS = "url_contains"
    ELEMENT_VISIBLE = "element_visible"
    ELEMENT_TEXT_CONTAINS = "element_text_contains"
    PAGE_STATE_EQUALS = "page_state_equals"


class WorkflowStatus(Enum):
    CANDIDATE = "candidate"
    VALIDATED = "validated"
    INVALID = "invalid"


@dataclass
class StatePredicate:
    """A precondition, postcondition or final-state assertion."""

    predicate_type: PredicateType
    expected: Any = True
    selector: Optional[str] = None
    state_key: Optional[str] = None
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "predicate_type": self.predicate_type.value,
            "expected": self.expected,
            "selector": self.selector,
            "state_key": self.state_key,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StatePredicate':
        values = dict(data)
        values["predicate_type"] = PredicateType(values["predicate_type"])
        return cls(**values)


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow"""
    
    action_type: ActionType
    
    # Stable selectors for element identification
    xpath: Optional[str] = None
    css_selector: Optional[str] = None
    
    # Action parameters
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Additional context
    element_attributes: Dict[str, str] = field(default_factory=dict)
    description: str = ""
    
    # Timing information
    wait_before: float = 0.0  # Seconds to wait before executing this step
    timeout: float = 15.0  # Maximum time to wait for element to be ready
    
    # Validation
    expected_outcome: Optional[str] = None
    preconditions: List[StatePredicate] = field(default_factory=list)
    postconditions: List[StatePredicate] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary for serialization"""
        return {
            "action_type": self.action_type.value,
            "xpath": self.xpath,
            "css_selector": self.css_selector,
            "parameters": self.parameters,
            "element_attributes": self.element_attributes,
            "description": self.description,
            "wait_before": self.wait_before,
            "timeout": self.timeout,
            "expected_outcome": self.expected_outcome,
            "preconditions": [item.to_dict() for item in self.preconditions],
            "postconditions": [item.to_dict() for item in self.postconditions],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowStep':
        """Create step from dictionary"""
        data = data.copy()
        data['action_type'] = ActionType(data['action_type'])
        data['preconditions'] = [StatePredicate.from_dict(item) for item in data.get('preconditions', [])]
        data['postconditions'] = [StatePredicate.from_dict(item) for item in data.get('postconditions', [])]
        return cls(**data)
    
    @classmethod
    def from_browser_action(cls, action_type: str, element: Optional[Any] = None, **params) -> 'WorkflowStep':
        """Create a workflow step from browser-use action and element info"""
        step = cls(
            action_type=ActionType(action_type.lower()),
            parameters=params
        )
        
        if element:
            # Extract stable selectors from DOMInteractedElement
            if hasattr(element, 'x_path'):
                step.xpath = element.x_path
            
            # Store relevant attributes for fallback identification
            if hasattr(element, 'attributes') and element.attributes:
                step.element_attributes = {
                    k: v for k, v in element.attributes.items()
                    if k in ['id', 'name', 'class', 'type', 'role', 'aria-label', 'data-testid']
                }
        
        return step


@dataclass
class Workflow:
    """Represents a complete workflow that can be learned and replayed"""
    
    # Identification
    workflow_id: str
    intent: str  # The task intent this workflow accomplishes
    
    # Steps
    steps: List[WorkflowStep] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_used_at: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0
    
    # Learning context
    initial_url: Optional[str] = None
    example_parameters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    
    # Performance metrics
    average_execution_time: float = 0.0
    model_calls_saved: int = 0

    # Validation lifecycle. New workflows are candidates until a complete
    # replay succeeds in a reset environment.
    validation_status: WorkflowStatus = WorkflowStatus.CANDIDATE
    final_predicates: List[StatePredicate] = field(default_factory=list)
    validated_at: Optional[datetime] = None
    invalid_reason: Optional[str] = None
    
    def add_step(self, step: WorkflowStep) -> None:
        """Add a step to the workflow"""
        self.steps.append(step)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary for serialization"""
        return {
            "workflow_id": self.workflow_id,
            "intent": self.intent,
            "steps": [step.to_dict() for step in self.steps],
            "created_at": self.created_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "initial_url": self.initial_url,
            "example_parameters": self.example_parameters,
            "description": self.description,
            "average_execution_time": self.average_execution_time,
            "model_calls_saved": self.model_calls_saved,
            "validation_status": self.validation_status.value,
            "final_predicates": [item.to_dict() for item in self.final_predicates],
            "validated_at": self.validated_at.isoformat() if self.validated_at else None,
            "invalid_reason": self.invalid_reason,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Workflow':
        """Create workflow from dictionary"""
        data = data.copy()
        data['steps'] = [WorkflowStep.from_dict(s) for s in data.get('steps', [])]
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('last_used_at'):
            data['last_used_at'] = datetime.fromisoformat(data['last_used_at'])
        # Old files had no lifecycle field. Treat them as candidates so they
        # cannot silently bypass the new validation protocol.
        data['validation_status'] = WorkflowStatus(data.get('validation_status', 'candidate'))
        data['final_predicates'] = [StatePredicate.from_dict(item) for item in data.get('final_predicates', [])]
        if data.get('validated_at'):
            data['validated_at'] = datetime.fromisoformat(data['validated_at'])
        return cls(**data)
    
    def to_json(self) -> str:
        """Serialize workflow to JSON string"""
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Workflow':
        """Deserialize workflow from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def parameterize(self, parameters: Dict[str, Any]) -> 'Workflow':
        """
        Create a parameterized copy of this workflow with specific values.
        
        Args:
            parameters: Dictionary mapping parameter names to values
        
        Returns:
            A new Workflow instance with parameters applied
        """
        import copy
        parameterized = copy.deepcopy(self)
        
        # Apply parameters to each step
        for step in parameterized.steps:
            for param_key, param_value in parameters.items():
                # Replace placeholders in step parameters
                for key, value in step.parameters.items():
                    if isinstance(value, str) and f"{{{param_key}}}" in value:
                        step.parameters[key] = value.replace(f"{{{param_key}}}", str(param_value))
                for predicate in (*step.preconditions, *step.postconditions):
                    if isinstance(predicate.expected, str) and f"{{{param_key}}}" in predicate.expected:
                        predicate.expected = predicate.expected.replace(f"{{{param_key}}}", str(param_value))
        for predicate in parameterized.final_predicates:
            for param_key, param_value in parameters.items():
                if isinstance(predicate.expected, str) and f"{{{param_key}}}" in predicate.expected:
                    predicate.expected = predicate.expected.replace(f"{{{param_key}}}", str(param_value))
        
        return parameterized

    def mark_validated(self) -> None:
        self.validation_status = WorkflowStatus.VALIDATED
        self.validated_at = datetime.now()
        self.invalid_reason = None

    def mark_invalid(self, reason: str) -> None:
        self.validation_status = WorkflowStatus.INVALID
        self.invalid_reason = reason
