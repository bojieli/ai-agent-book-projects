# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import abc
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, TypeVar, List, Optional, Union

from pydantic import BaseModel

from aworld.config.conf import ConfigDict
from aworld.core.common import Config, Observation, ActionModel, TaskItem
from aworld.core.context.base import Context


class Constants:
    AGENT = "agent"
    TOOL = "tool"
    TASK = "task"
    PLAN = "plan"
    OUTPUT = "output"
    TOOL_CALLBACK = "tool_callback"
    AGENT_CALLBACK = "agent_callback"
    GROUP = "group"
    HUMAN = "human"
    HUMAN_RESPONSE = "human_response"


class TopicType:
    START = "__start"
    FINISHED = "__finished"
    OUTPUT = "__output"
    ERROR = "__error"
    RERUN = "__rerun"
    HUMAN_CONFIRM = "__human_confirm"
    CANCEL = "__cancel"
    # for dynamic subscribe
    SUBSCRIBE_TOOL = "__subscribe_tool"
    SUBSCRIBE_AGENT = "__subscribe_agent"
    GROUP_ACTIONS = "__group_actions"
    GROUP_RESULTS = "__group_results"


DataType = TypeVar('DataType')


@dataclass
class Message(Generic[DataType]):
    """The message structure for event transmission.

    Each message has a unique ID, and the actual data is carried through the `payload` attribute,
    peer to peer(p2p) message transmission is achieved by setting the `receiver`, and topic based
    message transmission is achieved by setting the `topic`.

    Specific message recognition and processing can be achieved through the type of `payload`
    or by extending `Message`.
    """
    session_id: str = field(default_factory=str)
    payload: Optional[DataType] = field(default_factory=object, repr=False)
    # Current caller
    sender: str = field(default_factory=str)
    # event type
    category: str = field(default_factory=str)
    # Next caller
    receiver: str = field(default=None)
    # The previous caller
    caller: str = field(default=None)
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    priority: int = field(default=0)
    # Topic of message
    topic: str = field(default=None)
    headers: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: time.time())

    def __post_init__(self):
        context = self.headers.get("context")
        if not context:
            self.headers['context'] = Context()

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Message):
            raise RuntimeError
        return self.priority < other.priority

    def key(self) -> str:
        category = self.category if self.category else ''
        if self.topic:
            return f'{category}_{self.topic}'
        else:
            return f'{category}_{self.sender if self.sender else ""}'

    def is_error(self):
        return self.topic == TopicType.ERROR

    @property
    def task_id(self):
        return self.context.get_task().id

    @property
    def context(self) -> Context:
        return self.headers.get('context')

    @context.setter
    def context(self, context: Context):
        self.headers['context'] = context

    @property
    def group_id(self) -> str:
        return self.headers.get('group_id')

    @group_id.setter
    def group_id(self, group_id: str):
        self.headers['group_id'] = group_id


@dataclass
class TaskEvent(Message[TaskItem]):
    """Task message is oriented towards applications, can interact with third-party entities independently."""
    category: str = 'task'


@dataclass
class AgentMessage(Message[Observation]):
    """Agent event is oriented towards applications, can interact with third-party entities independently.

    For example, `agent` event can interact with other agents through the A2A protocol.
    """
    category: str = 'agent'


@dataclass
class ToolMessage(Message[List[ActionModel]]):
    """Tool event is oriented towards applications, can interact with third-party entities independently.

    For example, `tool` event can interact with other tools through the MCP protocol.
    """
    category: str = 'tool'


@dataclass
class CancelMessage(Message[TaskItem]):
    """Cancel event of the task, has higher priority."""
    category: str = 'task'
    priority: int = -1
    topic: str = TopicType.CANCEL

@dataclass
class GroupMessage(Message[Union[Dict[str, Any], List[ActionModel]]]):
    category: str = 'group'
    group_id: str = None

    def __post_init__(self):
        super().__post_init__()
        self.headers['group_id'] = self.group_id


@dataclass
class HumanMessage(Message[Any]):
    """Human interaction message for human-in-the-loop scenarios.
    
    This message type is used to handle human input, confirmations, and responses
    in interactive AI systems.
    """
    category: str = 'human'


class Messageable(object):
    """Top-level API for data reception, transmission and transformation."""
    __metaclass__ = abc.ABCMeta

    def __init__(self, conf: Config = None, **kwargs):
        self.conf = conf
        if isinstance(conf, Dict):
            self.conf = ConfigDict(conf)
        elif isinstance(conf, BaseModel):
            # To add flexibility
            self.conf = ConfigDict(conf.model_dump())

    @abc.abstractmethod
    async def send(self, message: Message, **kwargs):
        """Send a message to the receiver.

        Args:
            message: Message structure that carries the data that needs to be processed.
        """

    @abc.abstractmethod
    async def receive(self, message: Message, **kwargs):
        """Receive a message from the sender.

        Mainly used for request-driven (call), event-driven is generally handled using `Eventbus`.

        Args:
            message: Message structure that carries the data that needs to be processed.
        """

    async def transform(self, message: Message, **kwargs):
        """Transforms a message into a standardized format  from the sender.

        Args:
            message: Message structure that carries the data that needs to be processed.
        """


class Recordable(Messageable):
    """Top-level API for recording data."""

    async def send(self, message: Message, **kwargs):
        return await self.write(message, **kwargs)

    async def receive(self, message: Message, **kwargs):
        return await self.read(message, **kwargs)

    @abc.abstractmethod
    async def read(self, message: Message, **kwargs):
        """Read a message from the store.

        Args:
            message: Message structure that carries the data that needs to be read.
        """

    @abc.abstractmethod
    async def write(self, message: Message, **kwargs):
        """Write a message to the store.

        Args:
            message: Message structure that carries the data that needs to be write.
        """
