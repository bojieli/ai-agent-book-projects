# coding: utf-8
# Copyright (c) 2025 inclusionAI.

import abc
import os
import uuid
from typing import Any, Dict, Generic, List, Tuple, TypeVar, Union

from pydantic import BaseModel

from aworld.config.conf import AgentConfig, ConfigDict, load_config
from aworld.core.common import ActionModel
from aworld.core.context.base import Context
from aworld.core.event import eventbus
from aworld.core.event.base import Constants, Message, AgentMessage
from aworld.core.factory import Factory
from aworld.events.util import send_message
from aworld.logs.util import logger
from aworld.output.base import StepOutput
from aworld.sandbox.base import Sandbox
from aworld.utils.common import convert_to_snake, replace_env_variables, sync_exec

INPUT = TypeVar("INPUT")
OUTPUT = TypeVar("OUTPUT")

# Forward declaration
AgentFactory = None


def is_agent_by_name(name: str) -> bool:
    return name in AgentFactory if AgentFactory else False


def is_agent(policy: ActionModel) -> bool:
    return is_agent_by_name(policy.tool_name) or (
        not policy.tool_name and not policy.action_name
    )


class AgentStatus:
    # Init status
    START = 0
    # Agent is running for monitor or collection
    RUNNING = 1
    # Agent reject the task
    REJECT = 2
    # Agent is idle
    IDLE = 3
    # Agent meets exception
    ERROR = 4
    # End of one agent step
    DONE = 5
    # End of one task step
    FINISHED = 6


class AgentResult(BaseModel):
    current_state: Any
    actions: List[ActionModel]
    is_call_tool: bool = True


class MemoryModel(BaseModel):
    # TODO: memory module
    message: Dict = {}
    tool_calls: Any = None
    content: Any = None


class BaseAgent(Generic[INPUT, OUTPUT]):
    __metaclass__ = abc.ABCMeta

    def __init__(
        self,
        name: str,
        conf: Union[Dict[str, Any], ConfigDict, AgentConfig, None] = None,
        desc: str = None,
        agent_id: str = None,
        *,
        task: Any = None,
        tool_names: List[str] = None,
        agent_names: List[str] = None,
        mcp_servers: List[str] = None,
        mcp_config: Dict[str, Any] = None,
        black_tool_actions: Dict[str, List[str]] = None,
        feedback_tool_result: bool = True,
        wait_tool_result: bool = False,
        sandbox: Sandbox = None,
        **kwargs,
    ):
        """Base agent init.

        Args:
            conf: Agent config for internal processes.
            name: Agent name as identifier.
            desc: Agent description as tool description.
            task: The original task of the agent, will be automatically merged into messages after setting.
            tool_names: Tool names of local that agents can use.
            agent_names: Agents as tool name list.
            mcp_servers: Mcp names that the agent can use.
            mcp_config: Mcp config for mcp servers.
            feedback_tool_result: Whether feedback on the results of the tool.
                Agent1 uses tool1 when the value is True, it does not go to the other agent after obtaining the result of tool1.
                Instead, Agent1 uses the tool's result and makes a decision again.
            wait_tool_result: Whether wait on the results of the tool.
            sandbox: Sandbox instance for tool execution, advanced usage.
        """
        if conf is None:
            model_name = os.getenv("LLM_MODEL_NAME")
            api_key = os.getenv("LLM_API_KEY")
            base_url = os.getenv("LLM_BASE_URL")

            assert api_key and model_name, (
                "LLM_MODEL_NAME and LLM_API_KEY (environment variables) must be set, "
                "or pass AgentConfig explicitly"
            )
            logger.info(f"AgentConfig is empty, using env variables:\n"
                           f"LLM_API_KEY={'*' * min(len(api_key), 8) if api_key else 'Not set'}\n"
                           f"LLM_BASE_URL={base_url}\n"
                           f"LLM_MODEL_NAME={model_name}")

            conf = AgentConfig(
                llm_provider=os.getenv("LLM_PROVIDER", "openai"),
                llm_model_name=model_name,
                llm_api_key=api_key,
                llm_base_url=base_url,
                llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            )
        else:
            self.conf = conf

        if isinstance(conf, ConfigDict):
            pass
        elif isinstance(conf, Dict):
            self.conf = ConfigDict(conf)
        elif isinstance(conf, AgentConfig):
            # To add flexibility
            self.conf = ConfigDict(conf.model_dump())
        else:
            logger.warning(f"Unknown conf type: {type(conf)}")

        self._name = name if name else convert_to_snake(self.__class__.__name__)
        self._desc = desc if desc else self._name
        # Unique flag based agent name
        self._id = (
            agent_id if agent_id else f"{self._name}---uuid{uuid.uuid1().hex[0:6]}uuid"
        )
        self.task: Any = task
        # An agent can use the tool list
        self.tool_names: List[str] = tool_names or []
        human_tools = self.conf.get("human_tools", [])
        for tool in human_tools:
            self.tool_names.append(tool)
        # An agent can delegate tasks to other agent
        self.handoffs: List[str] = agent_names or []
        # Supported MCP server
        self.mcp_servers: List[str] = mcp_servers or []
        self.mcp_config: Dict[str, Any] = replace_env_variables(mcp_config or {})
        self.black_tool_actions: Dict[str, List[str]] = black_tool_actions or {}
        self.trajectory: List[Tuple[INPUT, Dict[str, Any], AgentResult]] = []
        # all tools that the agent can use. note: string name/id only
        self.tools = []
        self.context = None
        self.state = AgentStatus.START
        self._finished = True
        self.hooks: Dict[str, List[str]] = {}
        self.feedback_tool_result = feedback_tool_result
        self.wait_tool_result = wait_tool_result
        self.sandbox = None
        if self.mcp_servers or self.tool_names:
            self.sandbox = sandbox or Sandbox(
                mcp_servers=self.mcp_servers, mcp_config=self.mcp_config,
                black_tool_actions = self.black_tool_actions
            )
        self.loop_step = 0
        self.max_loop_steps = kwargs.pop("max_loop_steps", 20)

    def _init_context(self, context: Context):
        self.context = context

    def id(self) -> str:
        return self._id

    def name(self):
        return self._name

    def desc(self) -> str:
        return self._desc

    def run(self, message: Message, **kwargs) -> Message:
        self._init_context(message.context)
        caller = message.caller
        if caller and caller == self.id():
            self.loop_step += 1
        else:
            self.loop_step = 0
        should_term = self.sync_should_terminate_loop(message)
        if should_term:
            return AgentMessage(
                payload=message.payload,
                caller=message.sender,
                sender=self.id(),
                session_id=message.context.session_id,
                headers=message.headers
            )
        observation = message.payload
        sync_exec(
            send_message,
            Message(
                category=Constants.OUTPUT,
                payload=StepOutput.build_start_output(
                    name=f"{self.id()}", alias_name=self.name(), step_num=0
                ),
                sender=self.id(),
                session_id=self.context.session_id,
                headers={"context": self.context},
            ),
        )
        self.pre_run()
        result = self.policy(observation, message=message, **kwargs)
        final_result = self.post_run(result, observation, message)
        return final_result

    async def async_run(self, message: Message, **kwargs) -> Message:
        self._init_context(message.context)
        caller = message.caller
        if caller and caller == self.id():
            self.loop_step += 1
        else:
            self.loop_step = 0
        should_term = await self.should_terminate_loop(message)
        if should_term:
            return AgentMessage(
                payload=message.payload,
                caller=message.sender,
                sender=self.id(),
                session_id=message.context.session_id,
                headers=message.headers
            )
        observation = message.payload
        if eventbus is not None:
            await send_message(
                Message(
                    category=Constants.OUTPUT,
                    payload=StepOutput.build_start_output(
                        name=f"{self.id()}", alias_name=self.name(), step_num=0
                    ),
                    sender=self.id(),
                    session_id=self.context.session_id,
                    headers={"context": self.context},
                )
            )
        await self.async_pre_run()
        result = await self.async_policy(observation, message=message, **kwargs)
        final_result = await self.async_post_run(result, observation, message)
        return final_result

    @abc.abstractmethod
    def policy(
        self, observation: INPUT, info: Dict[str, Any] = None, **kwargs
    ) -> OUTPUT:
        """The strategy of an agent can be to decide which tools to use in the environment, or to delegate tasks to other agents.

        Args:
            observation: The state observed from tools in the environment.
            info: Extended information is used to assist the agent to decide a policy.
        """

    @abc.abstractmethod
    async def async_policy(
        self, observation: INPUT, info: Dict[str, Any] = None, **kwargs
    ) -> OUTPUT:
        """The strategy of an agent can be to decide which tools to use in the environment, or to delegate tasks to other agents.

        Args:
            observation: The state observed from tools in the environment.
            info: Extended information is used to assist the agent to decide a policy.
        """

    def reset(self, options: Dict[str, Any] = None):
        """Clean agent instance state and reset."""
        if options is None:
            options = {}
        self.tool_names = options.get("tool_names", self.tool_names)
        self.handoffs = options.get("agent_names", self.handoffs)
        self.mcp_servers = options.get("mcp_servers", self.mcp_servers)
        self.tools = []
        self.trajectory = []
        self._finished = True

    async def async_reset(self, options: Dict[str, Any] = None):
        """Clean agent instance state and reset."""
        self.reset(options)

    @property
    def finished(self) -> bool:
        """Agent finished the thing, default is True."""
        return self._finished

    def pre_run(self):
        pass

    def post_run(
        self, policy_result: OUTPUT, input: INPUT, message: Message = None
    ) -> Message:
        return policy_result

    async def async_pre_run(self):
        pass

    async def async_post_run(
        self, policy_result: OUTPUT, input: INPUT, message: Message = None
    ) -> Message:
        return policy_result

    def sync_should_terminate_loop(self, message: Message) -> bool:
        return sync_exec(self.should_terminate_loop, message)

    async def should_terminate_loop(self, message: Message) -> bool:
        return False


class AgentManager(Factory):
    def __init__(self, type_name: str = None):
        super(AgentManager, self).__init__(type_name)
        self._agent_conf = {}
        self._agent_instance = {}

    def __call__(self, name: str = None, *args, **kwargs):
        if name is None:
            return self

        conf = self._agent_conf.get(name)
        if not conf:
            logger.warning(f"{name} not find conf in agent factory")
            conf = dict()
        elif isinstance(conf, BaseModel):
            conf = conf.model_dump()

        user_conf = kwargs.pop("conf", None)
        if user_conf:
            if isinstance(user_conf, BaseModel):
                conf.update(user_conf.model_dump())
            elif isinstance(user_conf, dict):
                conf.update(user_conf)
            else:
                logger.warning(f"Unknown conf type: {type(user_conf)}, ignored!")

        conf["name"] = name
        conf = ConfigDict(conf)
        if name in self._cls:
            agent = self._cls[name](conf=conf, **kwargs)
            self._agent_instance[name] = agent
        else:
            raise ValueError(f"Can not find {name} agent!")
        return agent

    def desc(self, name: str) -> str:
        if self._agent_instance.get(name, None) and self._agent_instance[name].desc():
            return self._agent_instance[name].desc()
        return self._desc.get(name, "")

    def agent_instance(self, name: str) -> BaseAgent | None:
        if self._agent_instance.get(name, None):
            return self._agent_instance[name]
        return None

    def register(self, name: str, desc: str, conf_file_name: str = None, **kwargs):
        """Register a tool to tool factory.

        Args:
            name: Tool name
            desc: Tool description
            supported_action: Tool abilities
            conf_file_name: Default tool config
        """
        res = super(AgentManager, self).register(name, desc, **kwargs)
        conf_file_name = conf_file_name if conf_file_name else f"{name}.yaml"
        conf = load_config(conf_file_name, kwargs.get("dir"))
        if not conf:
            logger.warning(f"{conf_file_name} not find, will use default")
            # use general tool config
            conf = AgentConfig().model_dump()
        self._agent_conf[name] = conf
        return res


AgentFactory = AgentManager("agent_type")
