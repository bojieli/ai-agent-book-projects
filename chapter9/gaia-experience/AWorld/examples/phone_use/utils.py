# coding: utf-8

import json
import traceback
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Dict, List

from langchain_core.load import dumpd, load
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage, SystemMessage, HumanMessage
from openai import RateLimitError
from pydantic import BaseModel, ConfigDict, Field, model_serializer, model_validator

from aworld.core.agent.base import AgentResult
from aworld.core.common import ActionResult, Observation


class MessageMetadata(BaseModel):
    """Metadata for a message"""

    tokens: int = 0


class ManagedMessage(BaseModel):
    """A message with its metadata"""

    message: BaseMessage
    metadata: MessageMetadata = Field(default_factory=MessageMetadata)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # https://github.com/pydantic/pydantic/discussions/7558
    @model_serializer(mode='wrap')
    def to_json(self, original_dump):
        """
        Returns the JSON representation of the model.

        It uses langchain's `dumps` function to serialize the `message`
        property before encoding the overall dict with json.dumps.
        """
        data = original_dump(self)

        # NOTE: We override the message field to use langchain JSON serialization.
        data['message'] = dumpd(self.message)

        return data

    @model_validator(mode='before')
    @classmethod
    def validate(
            cls,
            value: Any,
            *,
            strict: bool | None = None,
            from_attributes: bool | None = None,
            context: Any | None = None,
    ) -> Any:
        """
        Custom validator that uses langchain's `loads` function
        to parse the message if it is provided as a JSON string.
        """
        if isinstance(value, dict) and 'message' in value:
            # NOTE: We use langchain's load to convert the JSON string back into a BaseMessage object.
            value['message'] = load(value['message'])
        return value


class MessageHistory(BaseModel):
    """History of messages with metadata"""

    messages: list[ManagedMessage] = Field(default_factory=list)
    current_tokens: int = 0

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def add_message(self, message: BaseMessage, metadata: MessageMetadata, position: int | None = None) -> None:
        """Add message with metadata to history"""
        if position is None:
            self.messages.append(ManagedMessage(message=message, metadata=metadata))
        else:
            self.messages.insert(position, ManagedMessage(message=message, metadata=metadata))
        self.current_tokens += metadata.tokens

    def add_model_output(self, output) -> None:
        """Add model output as AI message"""
        tool_calls = [
            {
                'name': 'AgentOutput',
                'args': output.model_dump(mode='json', exclude_unset=True),
                'id': '1',
                'type': 'tool_call',
            }
        ]

        msg = AIMessage(
            content='',
            tool_calls=tool_calls,
        )
        self.add_message(msg, MessageMetadata(tokens=100))  # Estimate tokens for tool calls

        # Empty tool response
        tool_message = ToolMessage(content='', tool_call_id='1')
        self.add_message(tool_message, MessageMetadata(tokens=10))  # Estimate tokens for empty response

    def get_messages(self) -> list[BaseMessage]:
        """Get all messages"""
        return [m.message for m in self.messages]

    def get_total_tokens(self) -> int:
        """Get total tokens in history"""
        return self.current_tokens

    def remove_oldest_message(self) -> None:
        """Remove oldest non-system message"""
        for i, msg in enumerate(self.messages):
            if not isinstance(msg.message, SystemMessage):
                self.current_tokens -= msg.metadata.tokens
                self.messages.pop(i)
                break

    def remove_last_state_message(self) -> None:
        """Remove last state message from history"""
        if len(self.messages) > 2 and isinstance(self.messages[-1].message, HumanMessage):
            self.current_tokens -= self.messages[-1].metadata.tokens
            self.messages.pop()


class MessageManagerState(BaseModel):
    """Holds the state for MessageManager"""

    history: MessageHistory = Field(default_factory=MessageHistory)
    tool_id: int = 1

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AgentSettings(BaseModel):
    """Options for the agent"""
    max_failures: int = 3
    retry_delay: int = 10
    save_history: bool = True
    history_path: Optional[str] = None
    max_actions_per_step: int = 10
    validate_output: bool = False
    message_context: Optional[str] = None


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
    evaluation_previous_goal: str
    memory: str
    next_goal: str


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
    message_manager_state: MessageManagerState = Field(default_factory=MessageManagerState)


@dataclass
class AgentStepInfo:
    number: int
    max_steps: int

    def is_last_step(self) -> bool:
        """Check if this is the last step"""
        return self.number >= self.max_steps - 1


@dataclass
class Trajectory:
    """Stores the agent's history, including all observations, info, and AgentResults."""
    history: List[tuple[Observation, Dict[str, Any], AgentResult]] = field(default_factory=list)

    def add_step(self, observation: Observation, info: Dict[str, Any], agent_result: AgentResult):
        """Add a step to the history"""
        self.history.append((observation, info, agent_result))

    def get_history(self) -> List[tuple[Observation, Dict[str, Any], AgentResult]]:
        """Retrieve the complete history"""
        return self.history
