# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import copy
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, TYPE_CHECKING

from aworld.config import ConfigDict
from aworld.core.context.context_state import ContextState
from aworld.core.context.session import Session
from aworld.logs.util import logger
from aworld.utils.common import nest_dict_counter

if TYPE_CHECKING:
    from aworld.core.task import Task, TaskResponse
    from aworld.core.agent.swarm import Swarm
    from aworld.events.manager import EventManager
    from aworld.core.agent import BaseAgent


@dataclass
class ContextUsage:
    total_context_length: int = 128000
    used_context_length: int = 0

    def __init__(self, total_context_length: int = 128000, used_context_length: int = 0):
        self.total_context_length = total_context_length
        self.used_context_length = used_context_length


class Context:
    """Context is the core context management class in the AWorld architecture, used to store and manage
    the complete state information of an Agent, including configuration data and runtime state.

    Context serves as both a session-level context manager and agent-level context manager, providing:

    1. **State Restoration**: Save all state information during Agent execution, supporting Agent state restoration and recovery
    2. **Configuration Management**: Store Agent's immutable configuration information (such as agent_id, system_prompt, etc.)
    3. **Runtime State Tracking**: Manage Agent's mutable state during execution (such as messages, step, tools, etc.)
    4. **LLM Prompt Management**: Manage and maintain the complete prompt context required for LLM calls, including system prompts, historical messages, etc.
    5. **LLM Call Intervention**: Provide complete control over the LLM call process through Hook and ContextProcessor
    6. **Multi-task State Management**: Support fork_new_task and context merging for complex multi-task scenarios

    ## Lifecycle
    The lifecycle of Context is completely consistent with the Agent instance:
    - **Creation**: Created during Agent initialization, containing initial configuration
    - **Runtime**: Continuously update runtime state during Agent execution
    - **Destruction**: Destroyed along with Agent instance destruction
    ```
    ┌─────────────────────── AWorld Runner ─────────────────────────┐
    |  ┌──────────────────── Agent Execution ────────────────────┐  │
    │  │  ┌────────────── Step 1 ─────────────┐ ┌── Step 2 ──┐   │  │
    │  │  │  [LLM Call]     [Tool Call(s)]    │
    │  │  │  [       Context Update      ]    │
    ```

    ## Field Classification
    - **Immutable Configuration Fields**: agent_id, agent_name, agent_desc, system_prompt, 
      agent_prompt, tool_names, context_rule
    - **Mutable Runtime Fields**: tools, step, messages, context_usage, llm_output, trajectories

    ## LLM Call Intervention Mechanism
    Context implements complete control over LLM calls through the following mechanisms:

    1. **Hook System**:
       - pre_llm_call_hook: Context preprocessing before LLM call
       - post_llm_call_hook: Result post-processing after LLM call
       - pre_tool_call_hook: Context adjustment before tool call
       - post_tool_call_hook: State update after tool call

    2. **PromptProcessor**:
       - Prompt Optimization: Optimize prompt content based on context length limitations
       - Message Compression: Intelligently compress historical messages to fit model context window
       - Context Rules: Apply context_rule for customized context processing

    ## Usage Scenarios
    1. **Agent Initialization**: Create Context containing configuration information
    2. **LLM Call Control**: Pass as info parameter in policy(), async_policy() methods to control LLM behavior
    3. **Hook Callbacks**: Access and modify LLM call context in various Hooks, use PromptProcessor for prompt optimization and context processing
    4. **State Recovery**: Recover Agent's complete state from persistent storage
    5. **Multi-task Management**: Use fork_new_task to create child contexts and merge_context to consolidate results

    Examples:
        >>> context = Context()
        >>> context.set_state("key", "value")
        >>> child_context = context.deep_copy()
        >>> context.merge_context(child_context)
    """

    def __init__(self,
                 user: str = None,
                 task_id: str = None,
                 trace_id: str = None,
                 session: Session = None,
                 engine: str = None,
                 **kwargs):

        super().__init__()
        self._user = user
        self._init(task_id=task_id, trace_id=trace_id,
                   session=session, engine=engine, **kwargs)

    def _init(self, *, task_id: str = None, trace_id: str = None, session: Session = None, engine: str = None):
        self._task_id = task_id
        self._task = None
        self._engine = engine
        self._trace_id = trace_id
        self._session: Session = session
        self.context_info = ContextState()
        self.agent_info = ConfigDict()
        self.trajectories = OrderedDict()
        self._token_usage = {
            "completion_tokens": 0,
            "prompt_tokens": 0,
            "total_tokens": 0,
        }
        # TODO workspace
        self._swarm = None
        self._event_manager = None

    def add_token(self, usage: Dict[str, int]):
        self._token_usage = nest_dict_counter(self._token_usage, usage)

    def reset(self, **kwargs):
        self._init(**kwargs)

    def set_task(self, task: 'Task'):
        self._task = task

    def get_task(self) -> 'Task':
        return self._task

    @property
    def trace_id(self):
        return self._trace_id

    @trace_id.setter
    def trace_id(self, trace_id):
        self._trace_id = trace_id

    @property
    def token_usage(self):
        return self._token_usage

    @property
    def engine(self):
        return self._engine

    @engine.setter
    def engine(self, engine: str):
        self._engine = engine

    @property
    def user(self):
        return self._user

    @user.setter
    def user(self, user):
        if user is not None:
            self._user = user

    @property
    def task_id(self):
        return self._task_id

    @task_id.setter
    def task_id(self, task_id):
        if task_id is not None:
            self._task_id = task_id

    @property
    def session_id(self):
        if self.session:
            return self.session.session_id
        else:
            return None

    @property
    def session(self):
        return self._session

    @session.setter
    def session(self, session: Session):
        self._session = session

    @property
    def swarm(self):
        return self._swarm

    @swarm.setter
    def swarm(self, swarm: 'Swarm'):
        self._swarm = swarm

    @property
    def event_manager(self):
        return self._event_manager

    @event_manager.setter
    def event_manager(self, event_manager: 'EventManager'):
        self._event_manager = event_manager

    @property
    def task_input(self):
        return self._task.input

    @task_input.setter
    def task_input(self, task_input):
        if self._task:
            self._task.input = task_input

    @property
    def outputs(self):
        return self._task.outputs

    def get_state(self, key: str, default: Any = None) -> Any:
        return self.context_info.get(key, default)

    def set_state(self, key: str, value: Any):
        self.context_info[key] = value

    async def build_sub_context(self, sub_task_content: Any, sub_task_id: str = None, **kwargs):
        # Create a new Context instance without calling __init__ to avoid singleton issues
        new_context = object.__new__(Context)
        self._deep_copy(new_context)
        new_context.task_id = sub_task_id
        new_context.task_input = sub_task_content
        return new_context

    def merge_sub_context(self, sub_task_context: 'ApplicationContext', **kwargs):
        self.merge_context(sub_task_context)

    def deep_copy(self) -> 'Context':
        # Create a new Context instance without calling __init__ to avoid singleton issues
        new_context = object.__new__(Context)
        return self._deep_copy(new_context)

    def _deep_copy(self, new_context) -> 'Context':
        """Create a deep copy of this Context instance with all attributes copied.

        Returns:
            Context: A new Context instance with deeply copied attributes
        """


        # Manually copy all important instance attributes
        # Basic attributes
        new_context._user = self._user
        new_context._task_id = self._task_id
        new_context._engine = self._engine
        new_context._trace_id = self._trace_id

        # Session - shallow copy to maintain reference
        new_context._session = self._session

        # Task - set to None to avoid circular references
        new_context._task = None

        # Deep copy complex state objects
        try:
            new_context.context_info = copy.deepcopy(self.context_info)
        except Exception:
            new_context.context_info = copy.copy(self.context_info)

        try:
            # Use standard deep copy and then convert to ConfigDict if needed
            new_context.agent_info = copy.deepcopy(self.agent_info)
            # If the result is not ConfigDict but original was, convert it
            if isinstance(self.agent_info, ConfigDict) and not isinstance(new_context.agent_info, ConfigDict):
                new_context.agent_info = ConfigDict(new_context.agent_info)
        except Exception:
            # Fallback: manual deep copy for ConfigDict
            if isinstance(self.agent_info, ConfigDict):
                import json
                # Use JSON serialization for deep copy (if data is JSON-serializable)
                try:
                    serialized = json.dumps(dict(self.agent_info))
                    deserialized = json.loads(serialized)
                    new_context.agent_info = ConfigDict(deserialized)
                except Exception:
                    # Final fallback to shallow copy
                    new_context.agent_info = copy.copy(self.agent_info)
            else:
                new_context.agent_info = copy.copy(self.agent_info)

        try:
            new_context.trajectories = copy.deepcopy(self.trajectories)
        except Exception:
            new_context.trajectories = copy.copy(self.trajectories)

        try:
            new_context._token_usage = copy.deepcopy(self._token_usage)
        except Exception:
            new_context._token_usage = copy.copy(self._token_usage)

        # Copy other attributes if they exist
        if hasattr(self, '_swarm'):
            new_context._swarm = self._swarm  # Shallow copy for complex objects
        if hasattr(self, '_event_manager'):
            new_context._event_manager = self._event_manager  # Shallow copy for complex objects

        return new_context

    def merge_context(self, other_context: 'Context') -> None:
        if not other_context:
            return

        # 1. Merge context_info state
        if hasattr(other_context, 'context_info') and other_context.context_info:
            try:
                # Get local state from child context (excluding inherited parent state)
                if hasattr(other_context.context_info, 'local_dict'):
                    local_state = other_context.context_info.local_dict()
                    if local_state:
                        self.context_info.update(local_state)
                else:
                    # If no local_dict method, directly update all states
                    self.context_info.update(other_context.context_info)
            except Exception as e:
                logger.warning(f"Failed to merge context_info: {e}")

        # 2. Merge trajectories
        if hasattr(other_context, 'trajectories') and other_context.trajectories:
            try:
                # Use timestamp or step number to avoid key conflicts
                for key, value in other_context.trajectories.items():
                    # If key already exists, add suffix to avoid overwriting
                    merge_key = key
                    counter = 1
                    while merge_key in self.trajectories:
                        merge_key = f"{key}_merged_{counter}"
                        counter += 1
                    self.trajectories[merge_key] = value
            except Exception as e:
                logger.warning(f"Failed to merge trajectories: {e}")

        # 3. Merge token usage statistics
        if hasattr(other_context, '_token_usage') and other_context._token_usage:
            try:
                # Calculate net token usage increment from child context (avoid double counting tokens inherited from parent context)
                # If child context was created through deep_copy, it already contains parent context's tokens
                # We need to calculate the net increment
                parent_tokens = self._token_usage.copy()
                child_tokens = other_context._token_usage.copy()

                # Calculate net increment: child context tokens - parent context tokens
                net_tokens = {}
                for key in child_tokens:
                    child_value = child_tokens.get(key, 0)
                    parent_value = parent_tokens.get(key, 0)
                    net_value = child_value - parent_value
                    if net_value > 0:  # Only merge net increment
                        net_tokens[key] = net_value

                # Add net increment to parent context
                if net_tokens:
                    self.add_token(net_tokens)
            except Exception as e:
                logger.warning(f"Failed to merge token usage: {e}")
                # If calculating net increment fails, directly add child context's tokens (may result in double counting)
                try:
                    self.add_token(other_context._token_usage)
                except Exception:
                    pass

        # 4. Merge agent_info configuration (only merge new configuration items)
        if hasattr(other_context, 'agent_info') and other_context.agent_info:
            try:
                # Only merge configuration items that don't exist in parent context
                for key, value in other_context.agent_info.items():
                    if key not in self.agent_info:
                        self.agent_info[key] = value
            except Exception as e:
                logger.warning(f"Failed to merge agent_info: {e}")

        # Record merge operation
        try:
            merge_info = {
                "merged_at": datetime.now().isoformat(),
                "merged_from_task_id": getattr(other_context, '_task_id', 'unknown'),
                "merged_trajectories_count": len(other_context.trajectories) if hasattr(other_context,
                                                                                        'trajectories') else 0,
                "merged_token_usage": other_context._token_usage if hasattr(other_context, '_token_usage') else {},
            }
            self.context_info.set('last_merge_info', merge_info)
        except Exception as e:
            logger.warning(f"Failed to record merge info: {e}")

    def save_action_trajectory(self,
                               step,
                               result: str,
                               agent_name: str = None,
                               tool_name: str = None,
                               params: str = None):
        step_key = f"step_{step}"
        step_data = {
            "step": step,
            "params": params,
            "result": result,
            "timestamp": datetime.now().isoformat(),
            "agent_name": agent_name,
            "tool_name": tool_name
        }
        self.trajectories[step_key] = step_data

    async def update_task_after_run(self, task_response: 'TaskResponse'):
        pass