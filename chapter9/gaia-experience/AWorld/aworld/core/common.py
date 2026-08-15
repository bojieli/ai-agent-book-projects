# coding: utf-8
# Copyright (c) 2025 inclusionAI.

from pydantic import BaseModel
from typing import Dict, Any, Optional, Union, List
from enum import Enum

from aworld.config import ConfigDict
from aworld.core.memory import MemoryItem

Config = Union[Dict[str, Any], ConfigDict, BaseModel]


class ActionResult(BaseModel):
    """Result of executing an action by use tool."""
    is_done: bool = False
    success: bool = False
    content: Any = None
    error: str = None
    keep: bool = False
    action_name: str = None
    tool_name: str = None
    # llm tool call id
    tool_call_id: str = None
    metadata: Optional[Dict[str, Any]] = {}
    parameter: Optional[Dict[str, Any]] = {}


class Observation(BaseModel):
    """Observation information is obtained from the tools or transformed from the actions made by agents.

    It can be an agent(as a tool) in the swarm or a tool in the virtual environment.
    """
    # default is None, means the main virtual environment or swarm
    container_id: Optional[str] = None
    # Observer who obtains observation, default is None for compatible, means an agent name or a tool name
    observer: Optional[str] = None
    # default is None for compatible, means with its action/ability name of an agent or a tool
    # NOTE: The only ability of an agent as a tool is handoffs
    ability: Optional[str] = None
    # The agent wants the observation to be created, default is None for compatible.
    from_agent_name: Optional[str] = None
    # To which agent should the observation be given, default is None for compatible.
    to_agent_name: Optional[str] = None
    # general info for agent
    content: Optional[Any] = None
    # dom_tree is a str or DomTree object
    dom_tree: Optional[Union[str, Any]] = None
    image: Optional[str] = None  # base64
    action_result: Optional[List[ActionResult]] = []
    # for video or image list
    images: Optional[List[str]] = []
    # extend key value pair. `done` is an internal key
    info: Optional[Dict[str, Any]] = {}

    @property
    def is_tool_result(self) -> bool:
        return self.action_result is not None and len(self.action_result) > 0


class StatefulObservation(Observation):
    """Observations with contextual states."""
    context: List[MemoryItem]


class ParamInfo(BaseModel):
    name: str | None = None
    type: str = "str"
    required: bool = False
    desc: str = None
    default_value: Any = None


class ToolActionInfo(BaseModel):
    name: str
    input_params: Dict[str, ParamInfo] = {}
    desc: str = None


class ActionModel(BaseModel):
    tool_name: Optional[str] = None
    tool_call_id: Optional[str] = None
    # agent name
    agent_name: Optional[str] = None
    # action_name is a tool action name by agent policy.
    action_name: Optional[str] = None
    params: Optional[Dict[str, Any]] = {}
    policy_info: Optional[Any] = None


class TaskItem(BaseModel):
    data: Optional[Any]
    msg: Optional[str] = None
    stop: bool = False
    success: bool = False
    action_name: Optional[str] = None
    params: Optional[Dict[str, Any]] = {}
    policy_info: Optional[Any] = None

class CallbackItem(BaseModel):
    data: Any
    node_id: str = None
    actions: List[ActionModel] = []

class CallbackActionType(str, Enum):
    BYPASS = "bypass"
    OVERRIDE = "override"

class CallbackResult(BaseModel):
    success: bool = False
    result_data: Any = None
    callback_action_type: CallbackActionType = None