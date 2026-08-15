# coding: utf-8
# Copyright (c) 2025 inclusionAI.

import abc
import traceback
from typing import Dict, Tuple, Any, TypeVar, Generic, List, Union

from pydantic import BaseModel

from aworld.config.conf import ToolConfig, load_config, ConfigDict
from aworld.core.event import eventbus
from aworld.core.tool.action import ToolAction
from aworld.core.tool.action_factory import ActionFactory
from aworld.core.common import Observation, ActionModel, ActionResult, CallbackItem, CallbackResult, CallbackActionType
from aworld.core.context.base import Context
from aworld.core.event.base import Message, ToolMessage, AgentMessage, Constants
from aworld.core.factory import Factory
from aworld.events.util import send_message
from aworld.logs.util import logger
from aworld.models.model_response import ToolCall
from aworld.output import ToolResultOutput
from aworld.output.base import StepOutput
from aworld.utils.common import convert_to_snake, sync_exec

AgentInput = TypeVar("AgentInput")
ToolInput = TypeVar("ToolInput")

# Forward declaration of action_executor to fix NameError
action_executor = None


class BaseTool(Generic[AgentInput, ToolInput]):
    """The basic generic classes of tools in the environment, with two parameterized types: AgentInput and ToolInput.

    We follow the gym/gymnasium protocol to be compatible with gym games, can also build special env tool in the framework.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, conf: Union[Dict[str, Any], ConfigDict, ToolConfig], **kwargs) -> None:
        self.conf = conf
        if isinstance(conf, ConfigDict):
            pass
        elif isinstance(conf, Dict):
            self.conf = ConfigDict(conf)
        elif isinstance(conf, ToolConfig):
            # To add flexibility
            self.conf = ConfigDict(conf.model_dump())
        else:
            logger.warning(f"Unknown conf type: {type(conf)}")
        self._finished = False

        self._name = kwargs.pop('name', self.conf.get(
            "name", convert_to_snake(self.__class__.__name__)))
        action_executor.register(name=self.name(), tool=self)
        self.action_executor = action_executor
        self.event_driven = kwargs.pop(
            'event_driven', self.conf.get('event_driven', False))
        self.handler = kwargs.get('handler', self.conf.get('handler', None))

        for k, v in kwargs.items():
            setattr(self, k, v)

    def _init_context(self, context: Context):
        self.context = context

    def name(self):
        """Tool unique name."""
        return self._name

    def pre_step(self, action: ToolInput, **kwargs):
        pass

    def post_step(self,
                  step_res: Tuple[AgentInput, float, bool, bool, Dict[str, Any]],
                  action: ToolInput,
                  **kwargs) -> Message:
        pass

    def step(self, message: Message, **kwargs) -> Message:
        self._init_context(message.context)
        action = message.payload
        self.pre_step(action, **kwargs)
        res = self.do_step(action, **kwargs)
        final_res = self.post_step(res, action, **kwargs)
        return final_res

    @abc.abstractmethod
    def reset(self, *, seed: int | None = None, options: Dict[str, str] | None = None) -> Tuple[
            AgentInput, dict[str, Any]]:
        """Resets the initial internal state, returning an initial state and extended info."""

    @abc.abstractmethod
    def do_step(self, action: ToolInput, **kwargs) -> Tuple[AgentInput, float, bool, bool, Dict[str, Any]]:
        """Run one step of the tool's in env using the actions.

        Args:
            action(ToolInput): Actions provided by the agent to update the observation.
        Return:
            Quintuple，key information: AgentInput and extended info dict.
        """

    @property
    def finished(self) -> bool:
        """The final execution status of the task from agent instructions."""
        return self._finished

    @abc.abstractmethod
    def close(self) -> None:
        """Close the tool resources in the environment."""

    def render(self):
        """For interface compatibility."""
        pass


class AsyncBaseTool(Generic[AgentInput, ToolInput]):
    """The basic generic classes of tools in the environment, with two parameterized types: AgentInput and ToolInput.

    We follow the gym/gymnasium protocol to be compatible with gym games, can also build special env tool in the framework.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, conf: Union[Dict[str, Any], ConfigDict, ToolConfig], **kwargs) -> None:
        self.conf = conf
        if isinstance(conf, ConfigDict):
            pass
        elif isinstance(conf, Dict):
            self.conf = ConfigDict(conf)
        elif isinstance(conf, ToolConfig):
            # To add flexibility
            self.conf = ConfigDict(conf.model_dump())
        else:
            logger.warning(f"Unknown conf type: {type(conf)}")
        self._finished = False

        self._name = kwargs.pop('name', self.conf.get(
            "name", convert_to_snake(self.__class__.__name__)))
        action_executor.register(name=self.name(), tool=self)
        self.action_executor = action_executor
        self.event_driven = kwargs.pop(
            'event_driven', self.conf.get('event_driven', False))
        self.handler = kwargs.get('handler', self.conf.get('handler', None))

        for k, v in kwargs.items():
            setattr(self, k, v)

    def _init_context(self, context: Context):
        self.context = context

    def name(self):
        """Tool unique name."""
        return self._name

    async def pre_step(self, action: ToolInput, **kwargs):
        pass

    async def post_step(self,
                        step_res: Tuple[AgentInput, float, bool, bool, Dict[str, Any]],
                        action: ToolInput,
                        **kwargs) -> Message:
        pass

    async def step(self, message: Message, **kwargs) -> Message:
        self._init_context(message.context)
        action = message.payload
        await self.pre_step(action, **kwargs)
        res = await self.do_step(action, **kwargs)
        final_res = await self.post_step(res, action, **kwargs)
        return final_res

    @abc.abstractmethod
    async def reset(self, *, seed: int | None = None, options: Dict[str, str] | None = None) -> Tuple[
            AgentInput, dict[str, Any]]:
        """Resets the initial internal state, returning an initial state and extended info."""

    @abc.abstractmethod
    async def do_step(self, action: ToolInput, **kwargs) -> Tuple[AgentInput, float, bool, bool, Dict[str, Any]]:
        """Run one step of the tool's in env using the actions.

        Args:
            action(ToolInput): Actions provided by the agent to update the observation.
        Return:
            Quintuple，key information: AgentInput and extended info dict.
        """

    @property
    def finished(self) -> bool:
        """The final execution status of the task from agent instructions."""
        return self._finished

    @abc.abstractmethod
    async def close(self) -> None:
        """Close the tool resources in the environment."""

    async def render(self):
        """For interface compatibility."""
        pass


class Tool(BaseTool[Observation, List[ActionModel]]):
    def _internal_process(self, step_res: Tuple[AgentInput, float, bool, bool, Dict[str, Any]],
                          action: ToolInput,
                          **kwargs):
        if not step_res or not action:
            return
        for idx, act in enumerate(action):
            if eventbus is not None:
                tool_output = ToolResultOutput(
                    tool_type=kwargs.get("tool_id_mapping", {}).get(
                        act.tool_call_id) or self.name(),
                    tool_name=act.tool_name,
                    data=step_res[0].content,
                    origin_tool_call=ToolCall.from_dict({
                        "function": {
                            "name": act.action_name,
                            "arguments": act.params,
                        }
                    }),
                    metadata=step_res[0].action_result[idx].metadata,
                    task_id=self.context.task_id
                )
                tool_output_message = Message(
                    category=Constants.OUTPUT,
                    payload=tool_output,
                    sender=self.name(),
                    session_id=self.context.session_id if self.context else "",
                    headers={"context": self.context}
                )
                sync_exec(send_message, tool_output_message)

    def step(self, message: Message, **kwargs) -> Message:
        final_res = None
        try:
            self._init_context(message.context)
            action = message.payload
            tool_id_mapping = {}
            for act in action:
                tool_id = act.tool_call_id
                tool_name = act.tool_name
                tool_id_mapping[tool_id] = tool_name
            self.pre_step(action, **kwargs)
            res = self.do_step(action, **kwargs)
            final_res = self.post_step(res, action, **kwargs)
            self._internal_process(
                res, action, tool_id_mapping=tool_id_mapping, **kwargs)
            return final_res
        except Exception as e:
            logger.error(
                f"Failed to execute {self.name()}: {e}."
                f"Debug info: session_id = {message.session_id}, action = {message.payload}."
                f"Traceback:\n{traceback.format_exc()}"
            )
            raise e
        finally:
            logger.warning(
                f"Tool {self.name()} result: {final_res}, session_id: {message.session_id}, task_id: {message.context.task_id}"
            )

    def post_step(self,
                  step_res: Tuple[Observation, float, bool, bool, Dict[str, Any]],
                  action: List[ActionModel],
                  **kwargs) -> Tuple[Observation, float, bool, bool, Dict[str, Any]] | Message:
        if not step_res:
            raise Exception(f'{self.name()} no observation has been made.')

        step_res[0].from_agent_name = action[0].agent_name
        for idx, act in enumerate(action):
            step_res[0].action_result[idx].tool_call_id = act.tool_call_id

        if self.context.swarm:
            agent = self.context.swarm.agents.get(action[0].agent_name)
            feedback_tool_result = agent.feedback_tool_result if agent else False
        else:
            feedback_tool_result = True
        if feedback_tool_result:
            return AgentMessage(payload=step_res,
                                caller=action[0].agent_name,
                                sender=self.name(),
                                receiver=action[0].agent_name,
                                session_id=self.context.session_id,
                                headers={"context": self.context})
        else:
            return AgentMessage(payload=step_res,
                                sender=action[0].agent_name,
                                session_id=self.context.session_id,
                                headers={"context": self.context})


class AsyncTool(AsyncBaseTool[Observation, List[ActionModel]]):
    async def _internal_process(self, step_res: Tuple[Observation, float, bool, bool, Dict[str, Any]],
                                action: List[ActionModel],
                                input_message: Message,
                                **kwargs):
        for idx, act in enumerate(action):
            # send tool results output
            if eventbus is not None:
                tool_output = ToolResultOutput(
                    tool_type=kwargs.get("tool_id_mapping", {}).get(
                        act.tool_call_id) or self.name(),
                    tool_name=act.tool_name,
                    data=step_res[0].content,
                    origin_tool_call=ToolCall.from_dict({
                        "function": {
                            "name": act.action_name,
                            "arguments": act.params,
                        }
                    }),
                    metadata=step_res[0].action_result[idx].metadata,
                    task_id=self.context.task_id
                )
                tool_output_message = Message(
                    category=Constants.OUTPUT,
                    payload=tool_output,
                    sender=self.name(),
                    session_id=self.context.session_id if self.context else "",
                    headers={"context": self.context}
                )
                await send_message(tool_output_message)

        await send_message(Message(
            category=Constants.OUTPUT,
            payload=StepOutput.build_finished_output(name=f"{action[0].agent_name if action else ''}",
                                                     step_num=0,
                                                     task_id=self.context.task_id),
            sender=self.name(),
            receiver=action[0].agent_name,
            session_id=self.context.session_id if self.context else "",
            headers={"context": self.context}
        ))
        await self._exec_tool_callback(step_res, action,
                                       Message(
                                           category=Constants.TOOL_CALLBACK,
                                           payload=CallbackItem(
                                               data=step_res,
                                               actions=action,
                                               node_id=input_message.id
                                           ),
                                           sender=self.name(),
                                           receiver=action[0].agent_name,
                                           session_id=self.context.session_id,
                                           headers={"context": self.context}
                                       ),
                                       **kwargs)

    async def step(self, message: Message, **kwargs) -> Message:
        final_res = None
        try:
            self._init_context(message.context)
            action = message.payload
            tool_id_mapping = {}
            for act in action:
                tool_id = act.tool_call_id
                tool_name = act.tool_name
                tool_id_mapping[tool_id] = tool_name
            await self.pre_step(action, **kwargs)
            res = await self.do_step(action, **kwargs)
            final_res = await self.post_step(res, action, **kwargs)
            await self._internal_process(res, action, message, tool_id_mapping=tool_id_mapping, **kwargs)
            if isinstance(final_res, Message):
                self._update_headers(final_res, message)
            if message.group_id and message.headers.get('level', 0) == 0:
                from aworld.runners.state_manager import RuntimeStateManager, RunNodeStatus, RunNodeBusiType
                state_mng = RuntimeStateManager.instance()
                state_mng.finish_sub_group(message.group_id, message.headers.get('root_message_id'), [final_res])
                final_res.headers['_tool_finished'] = True
            return final_res
        except Exception as e:
            logger.error(
                f"Failed to execute {self.name()}: {e}."
                f"Debug info: session_id = {message.session_id}, action = {message.payload}."
                f"Traceback:\n{traceback.format_exc()}"
            )
            raise e
        finally:
            logger.warning(
                f"Tool {self.name()} result: {final_res}, session_id: {message.session_id}, task_id: {message.context.task_id}"
            )

    async def post_step(self,
                        step_res: Tuple[Observation, float, bool, bool, Dict[str, Any]],
                        action: List[ActionModel],
                        **kwargs) -> Tuple[Observation, float, bool, bool, Dict[str, Any]] | Message:
        if not step_res:
            raise Exception(f'{self.name()} no observation has been made.')

        step_res[0].from_agent_name = action[0].agent_name
        for idx, act in enumerate(action):
            step_res[0].action_result[idx].tool_call_id = act.tool_call_id

        if self.context.swarm:
            agent = self.context.swarm.agents.get(action[0].agent_name)
            feedback_tool_result = agent.feedback_tool_result if agent else False
        else:
            feedback_tool_result = True
        if feedback_tool_result:
            return AgentMessage(payload=step_res,
                                caller=action[0].agent_name,
                                sender=self.name(),
                                receiver=action[0].agent_name,
                                session_id=self.context.session_id,
                                headers={"context": self.context})
        else:
            return AgentMessage(payload=step_res,
                                sender=action[0].agent_name,
                                session_id=self.context.session_id,
                                headers={"context": self.context})

    async def _exec_tool_callback(self, step_res: Tuple[Observation, float, bool, bool, Dict[str, Any]],
                                  action: List[ActionModel],
                                  message: Message,
                                  **kwargs):
        logger.info(f"send callback message: {message}")
        await send_message(message)

        from aworld.runners.state_manager import RuntimeStateManager, RunNodeStatus, RunNodeBusiType
        state_mng = RuntimeStateManager.instance()
        msg_id = message.id
        msg_node = state_mng.get_node(msg_id)
        state_mng.create_node(
            node_id=msg_id,
            busi_type=RunNodeBusiType.from_message_category(
                Constants.TOOL_CALLBACK),
            busi_id=message.receiver or "",
            session_id=message.session_id,
            task_id=message.task_id,
            msg_id=msg_id,
            msg_from=message.sender)
        res_node = await state_mng.wait_for_node_completion(msg_id)
        if res_node.status == RunNodeStatus.SUCCESS or res_node.results:
            tool_act_results = step_res[0].action_result
            callback_act_results = res_node.results
            if not callback_act_results:
                logger.warn(
                    f"tool {self.name()} callback finished with empty node result.")
                return
            if len(tool_act_results) != len(callback_act_results):
                logger.warn(
                    "tool action result and callback action result length not match.")
                return
            for idx, res in enumerate(callback_act_results):
                if res.status == RunNodeStatus.SUCCESS:
                    callback_res = res.result.payload
                    if isinstance(callback_res, CallbackResult):
                        if callback_res.callback_action_type == CallbackActionType.OVERRIDE:
                            tool_act_results[idx].content = callback_res.result_data
                else:
                    logger.warn(
                        f"tool {self.name()} callback finished with node result: {res}.")
                    continue

            return
        else:
            logger.warn(
                f"tool {self.name()} callback failed with node: {res_node}.")
            return

    def _update_headers(self, message: Message, input_message: Message) -> Dict[str, Any]:
        headers = input_message.headers.copy()
        headers['context'] = message.context
        headers['level'] = headers.get('level', 0) + 1
        message.headers = headers


class ToolsManager(Factory):
    def __init__(self, type_name: str = None):
        super(ToolsManager, self).__init__(type_name)
        self._tool_with_action = {}
        self._tool_conf = {}
        self._tool_instance = {}

    def __iter__(self):
        for name in self._cls:
            name = "async_" + name if self._asyn.get(name, False) else name
            yield name

    def __contains__(self, name: str) -> bool:
        """Whether the name in the factory."""
        name = "async_" + name if self._asyn.get(name, False) else name
        return name in self._cls

    def __call__(self, name: str = None, *args, **kwargs):
        if name is None:
            return self

        asyn = kwargs.pop("asyn", False)
        name = "async_" + name if asyn else name

        conf = self._tool_conf.get(name)
        if not conf:
            logger.warning(f"{name} not find conf in tool factory")
            conf = dict()
        elif isinstance(conf, BaseModel):
            conf = conf.model_dump()

        user_conf = kwargs.pop('conf', None)
        if user_conf:
            if isinstance(user_conf, dict):
                conf.update(user_conf)
            elif isinstance(user_conf, BaseModel):
                conf.update(user_conf.model_dump())
            else:
                logger.warning(
                    f"Unknown conf type: {type(user_conf)}, ignored!")
        self._tool_conf[name] = conf

        # must is a dict
        conf['name'] = name
        conf = ConfigDict(conf)

        if kwargs.get("reuse", conf.get('reuse', False)) is True and name in self._tool_instance:
            return self._tool_instance[name]

        if name in self._cls:
            tool = self._cls[name](conf=conf, **kwargs)
            self._tool_instance[name] = tool
        else:
            raise RuntimeError(
                f"can not find {name} tool in the ToolFactory, register it first.")

        action_executor.register(name, tool)
        return tool

    def get_tool_action(self, tool: str, asyn: bool = False):
        if asyn:
            tool = "async_" + tool
        return self._tool_with_action.get(tool)

    def register(self, name: str, desc: str, supported_action: ToolAction = None, conf_file_name: str = None, **kwargs):
        """Register a tool to tool factory.

        Args:
            name: Tool name
            desc: Tool description
            supported_action: Tool abilities
            conf_file_name: Default tool config
        """
        res = super(ToolsManager, self).register(name, desc, **kwargs)
        asyn = kwargs.pop("asyn", False)
        prefix = "async_" if asyn else ""
        conf_file_name = conf_file_name if conf_file_name else f"{name}_tool.yaml"
        conf = load_config(conf_file_name, kwargs.get("dir"))
        if not conf:
            logger.debug(f"can not load conf from {conf_file_name}")
            # use general tool config
            conf = ToolConfig().model_dump()
        name = prefix + name
        self._tool_with_action[name] = supported_action
        self._tool_conf[name] = conf
        logger.debug(f"{name} register to the tool factory.")
        return res


ToolFactory = ToolsManager("env_tool_type")


class ToolActionExecutor(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, tool: Tool = None):
        self.tool = tool
        self.tools: Dict[str, Tool] = {}

    def register(
            self,
            name: str,
            tool: Union[Tool, AsyncTool]):
        self.tools[name] = tool

    @abc.abstractmethod
    def execute_action(self, actions: List[ActionModel], **kwargs) -> Tuple[List[ActionResult], Any]:
        """"""
        return self.execute_env_action(actions, self.tool, **kwargs)

    @abc.abstractmethod
    async def async_execute_action(self, actions: List[ActionModel], **kwargs) -> Tuple[List[ActionResult], Any]:
        """"""
        return await self.async_execute_env_action(actions, self.tool, **kwargs)

    @abc.abstractmethod
    def execute_env_action(self,
                           actions: List[ActionModel],
                           tool: Tool,
                           **kwargs) -> Tuple[List[ActionResult], Any]:
        """"""
        action_results = []
        ctx = None
        for action in actions:
            if action is None:
                logger.warning("empty action, ignore it.")
                continue

            if tool is None:
                tool_name = action.tool_name
                tool = self.tools.get(tool_name)
                if tool is None:
                    tool = ToolFactory(
                        tool_name, conf=kwargs.get("conf", ToolConfig()))
                    self.tools[tool_name] = tool

            try:
                action_result, ctx = self.do_act(action, tool, **kwargs)
            except:
                logger.warning(traceback.format_exc())
                action_result = ActionResult(
                    error=traceback.format_exc(), success=False)
            action_result.action_name = action.action_name
            action_result.tool_name = action.tool_name
            action_results.append(action_result)
        return action_results, ctx

    async def async_execute_env_action(self,
                                       actions: List[ActionModel],
                                       tool: Tool,
                                       **kwargs) -> Tuple[List[ActionResult], Any]:
        """"""
        action_results = []
        ctx = None
        for action in actions:
            if action is None:
                logger.warning("empty action, ignore it.")
                continue

            if tool is None:
                tool_name = "async_" + action.tool_name
                tool = self.tools.get(tool_name)
                if tool is None:
                    tool = ToolFactory(
                        tool_name, conf=kwargs.get("conf", ToolConfig()))
                    self.tools[tool_name] = tool
            try:
                action_result, ctx = await self.async_do_act(action, tool, **kwargs)
            except:
                logger.warning(traceback.format_exc())
                action_result = ActionResult(
                    error=traceback.format_exc(), success=False)
            action_result.action_name = action.action_name
            action_result.tool_name = action.tool_name
            action_results.append(action_result)
        return action_results, ctx

    def do_act(self, action_model: ActionModel, tool: Tool, **kwargs):
        action_name = action_model.action_name
        if action_name not in ActionFactory:
            action_name = action_model.tool_name + action_model.action_name
            if action_name not in ActionFactory:
                raise ValueError(
                    f'Action {action_model.action_name} not found in ActionFactory')

        action = ActionFactory(action_name)
        action_result, page = action.act(action_model, tool=tool, **kwargs)
        logger.info(
            f"{tool.name()}-{action_model.action_name} execute finished")
        return action_result, page

    async def async_do_act(self, action_model: ActionModel, tool: Tool,
                           **kwargs):
        action_name = action_model.action_name
        if action_name not in ActionFactory:
            action_name = action_model.tool_name + action_model.action_name
            if action_name not in ActionFactory:
                raise ValueError(
                    f'Action {action_model.action_name} not found in ActionFactory')

        action = ActionFactory(action_name)
        action_result, page = await action.async_act(action_model, tool=tool, **kwargs)
        logger.info(
            f"{tool.name()}-{action_model.action_name} execute finished")
        return action_result, page


action_executor = ToolActionExecutor()
