# coding: utf-8

import json
import traceback
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Dict, List

from openai import RateLimitError
from pydantic import BaseModel, ConfigDict, Field

from aworld.core.common import ActionResult


class PolicyMetadata(BaseModel):
    """Metadata for a single step including timing information"""
    start_time: float
    end_time: float
    number: int
    input_tokens: int

    @property
    def duration_seconds(self) -> float:
        """Calculate step duration in seconds"""
        return self.end_time - self.start_time


class AgentBrain(BaseModel):
    """Current state of the agent"""
    evaluation_previous_goal: str = None
    memory: str = None
    thought: str = None
    next_goal: str = None


class AgentHistory(BaseModel):
    """History item for agent actions"""
    model_output: Optional[BaseModel] = None
    result: List[ActionResult]
    metadata: Optional[PolicyMetadata] = None
    content: Optional[str] = None
    base64_img: Optional[str] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Custom serialization handling"""
        return {
            'model_output': self.model_output.model_dump() if self.model_output else None,
            'result': [r.model_dump(exclude_none=True) for r in self.result],
            'metadata': self.metadata.model_dump() if self.metadata else None,
            'content': self.xml_content,
            'base64_img': self.base64_img
        }


class AgentHistoryList(BaseModel):
    """List of agent history items"""
    history: List[AgentHistory]

    def total_duration_seconds(self) -> float:
        """Get total duration of all steps in seconds"""
        total = 0.0
        for h in self.history:
            if h.metadata:
                total += h.metadata.duration_seconds
        return total

    def save_to_file(self, filepath: str | Path) -> None:
        """Save history to JSON file with proper serialization"""
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            data = self.model_dump()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            raise e

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Custom serialization that properly uses AgentHistory's model_dump"""
        return {
            'history': [h.model_dump(**kwargs) for h in self.history],
        }

    @classmethod
    def load_from_file(cls, filepath: str | Path) -> 'AgentHistoryList':
        """Load history from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.model_validate(data)


class AgentError:
    """Container for agent error handling"""
    VALIDATION_ERROR = 'Invalid model output format. Please follow the correct schema.'
    RATE_LIMIT_ERROR = 'Rate limit reached. Waiting before retry.'
    NO_VALID_ACTION = 'No valid action found'

    @staticmethod
    def format_error(error: Exception, include_trace: bool = False) -> str:
        """Format error message based on error type and optionally include trace"""
        if isinstance(error, RateLimitError):
            return AgentError.RATE_LIMIT_ERROR
        if include_trace:
            return f'{str(error)}\nStacktrace:\n{traceback.format_exc()}'
        return f'{str(error)}'


class AgentState(BaseModel):
    """Holds all state information for an Agent"""

    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    n_steps: int = 1
    consecutive_failures: int = 0
    last_result: Optional[List['ActionResult']] = None
    history: AgentHistoryList = Field(default_factory=lambda: AgentHistoryList(history=[]))
    last_plan: Optional[str] = None
    paused: bool = False
    stopped: bool = False


@dataclass
class AgentStepInfo:
    number: int
    max_steps: int

    def is_last_step(self) -> bool:
        """Check if this is the last step"""
        return self.number >= self.max_steps - 1
