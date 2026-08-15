# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import copy
import json
import time
import traceback
import uuid
from collections import OrderedDict
from datetime import datetime
from typing import Dict, Any, List, Callable, Optional

import aworld.trace as trace
from aworld.core.agent.agent_desc import get_agent_desc
from aworld.core.agent.base import BaseAgent, AgentResult, is_agent_by_name, is_agent
from aworld.core.common import ActionResult, Observation, ActionModel, Config, TaskItem
from aworld.core.context.base import Context
from aworld.core.context.processor.prompt_processor import PromptProcessor
from aworld.core.context.prompts import BasePromptTemplate
from aworld.core.context.prompts.string_prompt_template import StringPromptTemplate
from aworld.core.event import eventbus
from aworld.core.event.base import Message, ToolMessage, Constants, AgentMessage, GroupMessage, TopicType
from aworld.core.model_output_parser import ModelOutputParser
from aworld.core.tool.tool_desc import get_tool_desc
from aworld.events.util import send_message
from aworld.logs.util import logger, color_log, Color
from aworld.mcp_client.utils import mcp_tool_desc_transform
from aworld.memory.main import MemoryFactory
from aworld.memory.models import MessageMetadata, MemoryAIMessage, MemoryToolMessage, MemoryHumanMessage, \
    MemorySystemMessage, MemoryMessage
from aworld.models.llm import get_llm_model, acall_llm_model, acall_llm_model_stream
from aworld.models.model_response import ModelResponse, ToolCall, LLMResponseError
from aworld.models.utils import tool_desc_transform, agent_desc_transform
from aworld.output import Outputs
from aworld.output.base import MessageOutput, Output
from aworld.runners.hook.hooks import HookPoint
from aworld.sandbox.base import Sandbox
from aworld.trace.constants import SPAN_NAME_PREFIX_AGENT
from aworld.trace.instrumentation import semconv
from aworld.utils.common import sync_exec, nest_dict_counter
from aworld.utils.serialized_util import to_serializable


class LlmOutputParser(ModelOutputParser[ModelResponse, AgentResult]):
    async def parse(self, resp: ModelResponse, **kwargs) -> AgentResult:
        """Standard parse based Openai API."""

        if not resp:
            logger.warning("no valid content to parse!")
            return AgentResult(actions=[], current_state=None)

        agent_id = kwargs.get("agent_id")
        if not agent_id:
            logger.warning("need agent_id param.")
            raise RuntimeError("no `agent_id` param.")

        results = []
        is_call_tool = False
        content = '' if resp.content is None else resp.content
        if kwargs.get("use_tools_in_prompt"):
            tool_calls = []
            for tool in self.use_tool_list(content):
                tool_calls.append(ToolCall.from_dict({
                    "id": tool.get("id"),
                    "function": {
                        "name": tool.get("tool"),
                        "arguments": tool.get("arguments")
                    }
                }))
            if tool_calls:
                resp.tool_calls = tool_calls

        if resp.tool_calls:
            is_call_tool = True
            for tool_call in resp.tool_calls:
                full_name: str = tool_call.function.name
                if not full_name:
                    logger.warning("tool call response no tool name.")
                    continue
                try:
                    params = json.loads(tool_call.function.arguments)
                except:
                    logger.warning(f"{tool_call.function.arguments} parse to json fail.")
                    params = {}
                # format in framework
                names = full_name.split("__")
                tool_name = names[0]
                if is_agent_by_name(full_name):
                    param_info = params.get('content', "") + ' ' + params.get('info', '')
                    results.append(ActionModel(tool_name=full_name,
                                               tool_call_id=tool_call.id,
                                               agent_name=agent_id,
                                               params=params,
                                               policy_info=content + param_info))
                else:
                    action_name = '__'.join(names[1:]) if len(names) > 1 else ''
                    results.append(ActionModel(tool_name=tool_name,
                                               tool_call_id=tool_call.id,
                                               action_name=action_name,
                                               agent_name=agent_id,
                                               params=params,
                                               policy_info=content))
        else:
            content = content.replace("```json", "").replace("```", "")
            results.append(ActionModel(agent_name=agent_id, policy_info=content))

        return AgentResult(actions=results, current_state=None, is_call_tool=is_call_tool)

    def use_tool_list(self, content: str) -> List[Dict[str, Any]]:
        tool_list = []
        try:
            content = content.replace('\n', '').replace('\r', '')
            response_json = json.loads(content)
            use_tool_list = response_json.get("use_tool_list", [])
            for use_tool in use_tool_list:
                tool_name = use_tool.get("tool", None)
                if tool_name:
                    tool_list.append(use_tool)
        except Exception:
            logger.debug(f"tool_parse error, content: {content}, \n{traceback.format_exc()}")
        return tool_list


class Agent(BaseAgent[Observation, List[ActionModel]]):
    """Basic agent for unified protocol within the framework."""

    def __init__(self,
                 name: str,
                 conf: Config | None = None,
                 desc: str = None,
                 agent_id: str = None,
                 *,
                 task: Any = None,
                 tool_names: List[str] = None,
                 agent_names: List[str] = None,
                 mcp_servers: List[str] = None,
                 mcp_config: Dict[str, Any] = None,
                 feedback_tool_result: bool = True,
                 wait_tool_result: bool = False,
                 sandbox: Sandbox = None,
                 system_prompt: str = None,
                 system_prompt_template: BasePromptTemplate = None,
                 agent_prompt: str = None,
                 need_reset: bool = True,
                 step_reset: bool = True,
                 use_tools_in_prompt: bool = False,
                 black_tool_actions: Dict[str, List[str]] = None,
                 model_output_parser: ModelOutputParser[..., AgentResult] = LlmOutputParser(),
                 tool_aggregate_func: Callable[..., Any] = None,
                 event_handler_name: str = None,
                 event_driven: bool = True,
                 **kwargs):
        """A api class implementation of agent, using the `Observation` and `List[ActionModel]` protocols.

        Args:
            system_prompt: Instruction of the agent.
            agent_prompt: Optimized prompt of the agent.
            need_reset: Whether need to reset the status in start.
            step_reset: Reset the status at each step
            use_tools_in_prompt: Whether the tool description in prompt.
            black_tool_actions: Black list of actions of the tool.
            model_output_parser: Llm response parse function for the agent standard output, transform llm response.
            tool_aggregate_func: Aggregation strategy for multiple tool results.
            event_handler_name: Custom handlers for certain types of events.
        """
        super(Agent, self).__init__(name, conf, desc, agent_id,
                                    task=task,
                                    tool_names=tool_names,
                                    agent_names=agent_names,
                                    mcp_servers=mcp_servers,
                                    mcp_config=mcp_config,
                                    black_tool_actions=black_tool_actions,
                                    feedback_tool_result=feedback_tool_result,
                                    wait_tool_result=wait_tool_result,
                                    sandbox=sandbox,
                                    **kwargs)
        conf = self.conf
        self.model_name = conf.llm_config.llm_model_name
        self._llm = None
        self.memory = MemoryFactory.instance()
        self.memory_config = conf.memory_config
        self.system_prompt: str = system_prompt if system_prompt else conf.system_prompt
        self.system_prompt_template: str = system_prompt_template if (
            system_prompt_template) else conf.system_prompt_template

        # for backward compatibility
        if not self.system_prompt_template:
            self.system_prompt_template = StringPromptTemplate.from_template(self.system_prompt)
        if isinstance(self.system_prompt_template, str):
            self.system_prompt_template = StringPromptTemplate.from_template(self.system_prompt_template)
        if not self.system_prompt:
            self.system_prompt = self.system_prompt_template.template
        self.agent_prompt: str = agent_prompt if agent_prompt else conf.agent_prompt
        self.event_driven = event_driven

        self.need_reset = need_reset if need_reset else conf.need_reset
        # whether to keep contextual information, False means keep, True means reset in every step by the agent call
        self.step_reset = step_reset
        # tool_name: [tool_action1, tool_action2, ...]
        # self.black_tool_actions: Dict[str, List[str]] = black_tool_actions if black_tool_actions \
        #     else conf.get('black_tool_actions', {})
        self.model_output_parser = model_output_parser
        self.use_tools_in_prompt = use_tools_in_prompt if use_tools_in_prompt else conf.use_tools_in_prompt
        self.tools_aggregate_func = tool_aggregate_func if tool_aggregate_func else self._tools_aggregate_func
        self.event_handler_name = event_handler_name

    @property
    def llm(self):
        # lazy
        if self._llm is None:
            llm_config = self.conf.llm_config or None
            conf = llm_config if llm_config and (
                    llm_config.llm_provider or llm_config.llm_base_url or llm_config.llm_api_key or llm_config.llm_model_name) else self.conf
            self._llm = get_llm_model(conf)
        return self._llm

    def desc_transform(self, context: Context) -> None:
        """Transform of descriptions of supported tools, agents, and MCP servers in the framework to support function calls of LLM."""
        sync_exec(self.async_desc_transform, context)

    async def async_desc_transform(self, context: Context) -> None:
        """Transform of descriptions of supported tools, agents, and MCP servers in the framework to support function calls of LLM."""

        # Stateless tool
        self.tools = tool_desc_transform(get_tool_desc(),
                                         tools=self.tool_names if self.tool_names else [],
                                         black_tool_actions=self.black_tool_actions)
        # Agents as tool
        self.tools.extend(agent_desc_transform(get_agent_desc(),
                                               agents=self.handoffs if self.handoffs else []))
        # MCP servers are tools
        if self.sandbox:
            mcp_tools = await self.sandbox.mcpservers.list_tools(context)
            self.tools.extend(mcp_tools)
        else:
            self.tools.extend(await mcp_tool_desc_transform(self.mcp_servers, self.mcp_config))

    def messages_transform(self,
                           content: str,
                           image_urls: List[str] = None,
                           observation: Observation = None,
                           message: Message = None,
                           **kwargs) -> List[Dict[str, Any]]:
        return sync_exec(self.async_messages_transform, image_urls=image_urls, observation=observation,
                         message=message, **kwargs)

    async def async_messages_transform(self,
                                       image_urls: List[str] = None,
                                       observation: Observation = None,
                                       message: Message = None,
                                       **kwargs) -> List[Dict[str, Any]]:
        """Transform the original content to LLM messages of native format.

        Args:
            observation: Observation by env.
            image_urls: List of images encoded using base64.
            message: Event received by the Agent.
        Returns:
            Message list for LLM.
        """
        agent_prompt = self.agent_prompt
        messages = []
        # append sys_prompt to memory
        await self._add_system_message_to_memory(context=message.context, content=observation.content)

        session_id = message.context.get_task().session_id
        task_id = message.context.get_task().id
        histories = self.memory.get_all(filters={
            "agent_id": self.id(),
            "session_id": session_id,
            "task_id": task_id,
            "memory_type": "message"
        })
        last_history = histories[-1] if histories and len(histories) > 0 else None

        # append observation to memory
        if observation.is_tool_result:
            for action_item in observation.action_result:
                tool_call_id = action_item.tool_call_id
                await self._add_tool_result_to_memory(tool_call_id, tool_result=action_item, context=message.context)
        elif last_history and last_history.metadata and "tool_calls" in last_history.metadata and \
                last_history.metadata[
                    'tool_calls']:
            for tool_call in last_history.metadata['tool_calls']:
                tool_call_id = tool_call['id']
                tool_name = tool_call['function']['name']
                if tool_name and tool_name == message.sender:
                    await self._add_tool_result_to_memory(tool_call_id, tool_result=observation.content,
                                                          context=message.context)
                    break
        else:
            content = observation.content
            logger.debug(f"agent_prompt: {agent_prompt}")
            if agent_prompt:
                content = agent_prompt.format(task=content, current_date=datetime.now().strftime("%Y-%m-%d"))
            if image_urls:
                urls = [{'type': 'text', 'text': content}]
                for image_url in image_urls:
                    urls.append(
                        {'type': 'image_url', 'image_url': {"url": image_url}})
                content = urls
            await self._add_human_input_to_memory(content, message.context, memory_type="message")

        # from memory get last n messages
        histories = self.memory.get_last_n(self.memory_config.history_rounds, filters={
            "agent_id": self.id(),
            "session_id": session_id,
            "task_id": task_id
        }, agent_memory_config=self.memory_config)
        if histories:
            # default use the first tool call
            for history in histories:
                if isinstance(history, MemoryMessage):
                    messages.append(history.to_openai_message())
                else:
                    if not self.use_tools_in_prompt and "tool_calls" in history.metadata and history.metadata[
                        'tool_calls']:
                        messages.append({'role': history.metadata['role'], 'content': history.content,
                                         'tool_calls': [history.metadata["tool_calls"][0]]})
                    else:
                        messages.append({'role': history.metadata['role'], 'content': history.content,
                                         "tool_call_id": history.metadata.get("tool_call_id")})
        return messages

    async def init_observation(self, observation: Observation) -> Observation:
        # supported string only
        # if self.task and isinstance(self.task, str) and self.task != observation.content:
        #     observation.content = f"base task is: {self.task}\n{observation.content}"
        #     # `task` only needs to be processed once and reflected in the context
        #     self.task = None

        # default use origin observation
        return observation

    def _log_messages(self, messages: List[Dict[str, Any]], **kwargs) -> None:
        """Log the sequence of messages for debugging purposes"""
        logger.info(f"[agent] Invoking LLM with {len(messages)} messages:")
        logger.debug(f"[agent] use tools: {self.tools}")
        for i, msg in enumerate(messages):
            prefix = msg.get('role')
            logger.info(
                f"[agent] Message {i + 1}: {prefix} ===================================")
            if isinstance(msg['content'], list):
                try:
                    for item in msg['content']:
                        if item.get('type') == 'text':
                            logger.info(
                                f"[agent] Text content: {item.get('text')}")
                        elif item.get('type') == 'image_url':
                            image_url = item.get('image_url', {}).get('url', '')
                            if image_url.startswith('data:image'):
                                logger.info(f"[agent] Image: [Base64 image data]")
                            else:
                                logger.info(
                                    f"[agent] Image URL: {image_url[:30]}...")
                except Exception as e:
                    logger.error(f"[agent] Error parsing msg['content']: {msg}. Error: {e}")
                    content = str(msg['content'])
                    chunk_size = 500
                    for j in range(0, len(content), chunk_size):
                        chunk = content[j:j + chunk_size]
                        if j == 0:
                            logger.info(f"[agent] Content: {chunk}")
                        else:
                            logger.info(f"[agent] Content (continued): {chunk}")
            else:
                content = str(msg['content'])
                chunk_size = 500
                for j in range(0, len(content), chunk_size):
                    chunk = content[j:j + chunk_size]
                    if j == 0:
                        logger.info(f"[agent] Content: {chunk}")
                    else:
                        logger.info(f"[agent] Content (continued): {chunk}")

            if 'tool_calls' in msg and msg['tool_calls']:
                for tool_call in msg.get('tool_calls'):
                    if isinstance(tool_call, dict):
                        logger.info(
                            f"[agent] Tool call: {tool_call.get('function', {}).get('name', {})} - ID: {tool_call.get('id')}")
                        args = str(tool_call.get('function', {}).get(
                            'arguments', {}))[:1000]
                        logger.info(f"[agent] Tool args: {args}...")
                    elif isinstance(tool_call, ToolCall):
                        logger.info(
                            f"[agent] Tool call: {tool_call.function.name} - ID: {tool_call.id}")
                        args = str(tool_call.function.arguments)[:1000]
                        logger.info(f"[agent] Tool args: {args}...")

    def _agent_result(self, actions: List[ActionModel], caller: str, input_message: Message):
        if not actions:
            raise Exception(f'{self.id()} no action decision has been made.')
        if self.event_handler_name:
            return Message(payload=actions,
                           caller=caller,
                           sender=self.id(),
                           receiver=actions[0].tool_name,
                           category=self.event_handler_name,
                           session_id=input_message.context.session_id if input_message.context else "",
                           headers=self._update_headers(input_message))

        tools = OrderedDict()
        agents = []
        for action in actions:
            if is_agent(action):
                agents.append(action)
            else:
                if action.tool_name not in tools:
                    tools[action.tool_name] = []
                tools[action.tool_name].append(action)

        _group_name = None
        # agents and tools exist simultaneously, more than one agent/tool name
        if (agents and tools) or len(agents) > 1 or len(tools) > 1:
            _group_name = f"{self.id()}_{uuid.uuid1().hex}"

        # complex processing
        if _group_name:
            return GroupMessage(payload=actions,
                                caller=caller,
                                sender=self.id(),
                                receiver=actions[0].tool_name,
                                session_id=input_message.context.session_id if input_message.context else "",
                                group_id=_group_name,
                                topic=TopicType.GROUP_ACTIONS,
                                headers=self._update_headers(input_message))
        elif agents:
            return AgentMessage(payload=actions,
                                caller=caller,
                                sender=self.id(),
                                receiver=actions[0].tool_name,
                                session_id=input_message.context.session_id if input_message.context else "",
                                headers=self._update_headers(input_message))

        else:
            return ToolMessage(payload=actions,
                               caller=caller,
                               sender=self.id(),
                               receiver=actions[0].tool_name,
                               session_id=input_message.context.session_id if input_message.context else "",
                               headers=self._update_headers(input_message))

    def post_run(self, policy_result: List[ActionModel], policy_input: Observation, message: Message = None) -> Message:
        return self._agent_result(
            policy_result,
            policy_input.from_agent_name if policy_input.from_agent_name else policy_input.observer,
            message
        )

    async def async_post_run(self, policy_result: List[ActionModel], policy_input: Observation,
                             message: Message = None) -> Message:
        return self._agent_result(
            policy_result,
            policy_input.from_agent_name if policy_input.from_agent_name else policy_input.observer,
            message
        )

    def policy(self, observation: Observation, info: Dict[str, Any] = {}, message: Message = None, **kwargs) -> List[
        ActionModel]:
        """The strategy of an agent can be to decide which tools to use in the environment, or to delegate tasks to other agents.

        Args:
            observation: The state observed from tools in the environment.
            info: Extended information is used to assist the agent to decide a policy.

        Returns:
            ActionModel sequence from agent policy
        """
        return sync_exec(self.async_policy, observation, info, message, **kwargs)

    async def async_policy(self, observation: Observation, info: Dict[str, Any] = {}, message: Message = None,
                           **kwargs) -> List[ActionModel]:
        """The strategy of an agent can be to decide which tools to use in the environment, or to delegate tasks to other agents.

        Args:
            observation: The state observed from tools in the environment.
            info: Extended information is used to assist the agent to decide a policy.

        Returns:
            ActionModel sequence from agent policy
        """
        logger.info(f"Agent{type(self)}#{self.id()}: async_policy start")

        # Get current step information for trace recording
        source_span = trace.get_current_span()
        self._finished = False
        if hasattr(observation, 'context') and observation.context:
            self.task_histories = observation.context

        try:
            events = []
            async for event in self.run_hooks(message.context, HookPoint.PRE_LLM_CALL):
                events.append(event)
        except Exception:
            logger.debug(traceback.format_exc())

        messages = await self.build_llm_input(observation, info, message=message, **kwargs)

        serializable_messages = to_serializable(messages)
        llm_response = None
        if source_span:
            source_span.set_attribute("messages", json.dumps(serializable_messages, ensure_ascii=False))
        try:
            llm_response = await self.invoke_model(messages, message=message, **kwargs)
        except Exception as e:
            logger.warn(traceback.format_exc())
            raise e
        finally:
            if llm_response:
                if llm_response.error:
                    logger.info(f"llm result error: {llm_response.error}")
                    if eventbus is not None:
                        output_message = Message(
                            category=Constants.OUTPUT,
                            payload=Output(
                                data=f"llm result error: {llm_response.error}"
                            ),
                            sender=self.id(),
                            session_id=message.context.session_id if message.context else "",
                            headers={"context": message.context}
                        )
                        await send_message(output_message)
                else:
                    await self._add_llm_response_to_memory(llm_response, message.context, history_messages=messages)
            else:
                logger.error(f"{self.id()} failed to get LLM response")
                raise RuntimeError(f"{self.id()} failed to get LLM response")

        try:
            events = []
            async for event in self.run_hooks(message.context, HookPoint.POST_LLM_CALL):
                events.append(event)
        except Exception as e:
            logger.debug(traceback.format_exc())

        agent_result = await self.model_output_parser.parse(llm_response,
                                                            agent_id=self.id(),
                                                            use_tools_in_prompt=self.use_tools_in_prompt)
        logger.info(f"agent_result: {agent_result}")
        policy_result: Optional[List[ActionModel]] = None
        if self.is_agent_finished(llm_response, agent_result):
            policy_result = agent_result.actions
        else:
            if not self.wait_tool_result:
                policy_result = agent_result.actions
            else:
                policy_result = await self.execution_tools(agent_result.actions, message)
        await self.send_llm_response_output(llm_response, agent_result, message.context, kwargs.get("outputs"))
        return policy_result

    async def execution_tools(self, actions: List[ActionModel], message: Message = None, **kwargs) -> List[ActionModel]:
        """Tool execution operations.

        Returns:
            ActionModel sequence. Tool execution result.
        """
        from aworld.utils.run_util import exec_tool

        tool_results = []
        for act in actions:
            if is_agent(act):
                continue
            act_result = await exec_tool(tool_name=act.tool_name,
                                         action_name=act.action_name,
                                         params=act.params,
                                         agent_name=self.id(),
                                         context=message.context.deep_copy(),
                                         sub_task=True,
                                         outputs=message.context.outputs,
                                         task_group_id=message.context.get_task().group_id or uuid.uuid4().hex)
            if not act_result.success:
                color_log(f"Agent {self.id()} _execute_tool failed with exception: {act_result.msg}",
                          color=Color.red)
                continue
            tool_results.append(
                ActionResult(tool_call_id=act.tool_call_id, tool_name=act.tool_name, content=act_result.answer))
            await self._add_tool_result_to_memory(act.tool_call_id, act_result.answer,
                                                  context=message.context)
        result = sync_exec(self.tools_aggregate_func, tool_results)
        return result

    async def _tools_aggregate_func(self, tool_results: List[ActionResult]) -> List[ActionModel]:
        """Aggregate tool results
        Args:
            tool_results: Tool results
        Returns:
            ActionModel sequence
        """
        content = ""
        for res in tool_results:
            content += f"{res.content}\n"
        return [ActionModel(agent_name=self.id(), policy_info=content)]

    async def build_llm_input(self,
                              observation: Observation,
                              info: Dict[str, Any] = {},
                              message: Message = None,
                              **kwargs):
        """Build LLM input.

        Args:
            observation: The state observed from the environment
            info: Extended information to assist the agent in decision-making
        """
        await self.async_desc_transform(message.context)
        # observation secondary processing
        observation = await self.init_observation(observation)
        images = observation.images if self.conf.use_vision else None
        if self.conf.use_vision and not images and observation.image:
            images = [observation.image]
        messages = await self.async_messages_transform(image_urls=images, observation=observation, message=message)
        # truncate and other process
        try:
            messages = self._process_messages(messages=messages, context=message.context)
        except Exception as e:
            logger.warning(f"Failed to process messages in messages_transform: {e}")
            logger.debug(f"Process messages error details: {traceback.format_exc()}")

        self._log_messages(messages, context=message.context)

        return messages

    def _process_messages(self, messages: List[Dict[str, Any]],
                          context: Context = None) -> Optional[List[Dict[str, Any]]]:
        origin_messages = messages
        st = time.time()
        with trace.span(f"{SPAN_NAME_PREFIX_AGENT}llm_context_process", attributes={
            "start_time": st,
            semconv.AGENT_ID: self.id()
        }) as compress_span:
            if self.conf.context_rule is None:
                logger.debug('debug|skip process_messages context_rule is None')
                return messages
            origin_len = compressed_len = len(str(messages))
            origin_messages_count = truncated_messages_count = len(messages)
            try:
                prompt_processor = PromptProcessor(self.conf.context_rule, self.conf.llm_config)
                result = prompt_processor.process_messages(messages, context)
                messages = result.processed_messages

                compressed_len = len(str(messages))
                truncated_messages_count = len(messages)
                logger.debug(
                    f'debug|llm_context_process|{origin_len}|{compressed_len}|{origin_messages_count}|{truncated_messages_count}|\n|{origin_messages}\n|{messages}')
                return messages
            finally:
                compress_span.set_attributes({
                    "end_time": time.time(),
                    "duration": time.time() - st,
                    # messages length
                    "origin_messages_count": origin_messages_count,
                    "truncated_messages_count": truncated_messages_count,
                    "truncated_ratio": round(truncated_messages_count / origin_messages_count,
                                             2) if origin_messages_count > 0 else 0,
                    # token length
                    "origin_len": origin_len,
                    "compressed_len": compressed_len,
                    "compress_ratio": round(compressed_len / origin_len, 2)
                })

    async def invoke_model(self,
                           messages: List[Dict[str, str]] = [],
                           message: Message = None,
                           **kwargs) -> ModelResponse:
        """Perform LLM call.

        Args:
            messages: LLM model input messages.
            message: Event message.
            **kwargs: Other parameters

        Returns:
            LLM response
        """
        llm_response = None
        source_span = trace.get_current_span()
        serializable_messages = to_serializable(messages)
        message.context.context_info["llm_input"] = serializable_messages

        if source_span:
            source_span.set_attribute("messages", json.dumps(
                serializable_messages, ensure_ascii=False))

        try:
            stream_mode = kwargs.get("stream", False)
            float_temperature = float(self.conf.llm_config.llm_temperature)
            if stream_mode:
                llm_response = ModelResponse(
                    id="", model="", content="", tool_calls=[])
                resp_stream = acall_llm_model_stream(
                    self.llm,
                    messages=messages,
                    model=self.model_name,
                    temperature=float_temperature,
                    tools=self.tools if not self.use_tools_in_prompt and self.tools else None,
                    stream=True
                )

                async def async_call_llm(resp_stream, json_parse=False):
                    llm_resp = ModelResponse(
                        id="", model="", content="", tool_calls=[])

                    # Async streaming with acall_llm_model
                    async def async_generator():
                        async for chunk in resp_stream:
                            if chunk.content:
                                llm_resp.content += chunk.content
                                yield chunk.content
                            if chunk.tool_calls:
                                llm_resp.tool_calls.extend(chunk.tool_calls)
                            if chunk.error:
                                llm_resp.error = chunk.error
                            llm_resp.id = chunk.id
                            llm_resp.model = chunk.model
                            llm_resp.usage = nest_dict_counter(
                                llm_resp.usage, chunk.usage)

                    return MessageOutput(source=async_generator(), json_parse=json_parse), llm_resp

                output, response = await async_call_llm(resp_stream)
                llm_response = response

            else:
                llm_response = await acall_llm_model(
                    self.llm,
                    messages=messages,
                    model=self.model_name,
                    temperature=float_temperature,
                    tools=self.tools if not self.use_tools_in_prompt and self.tools else None,
                    stream=kwargs.get("stream", False)
                )

            logger.info(f"Execute response: {json.dumps(llm_response.to_dict(), ensure_ascii=False)}")
        except Exception as e:
            logger.warn(traceback.format_exc())
            await send_message(Message(
                category=Constants.OUTPUT,
                payload=Output(
                    data=f"Failed to call llm model: {e}"
                ),
                sender=self.id(),
                session_id=message.context.session_id if message.context else "",
                headers={"context": message.context}
            ))

            if "Please reduce the length of the messages" in str(e):
                # Meaning context too long, will return directly. You can develop a Processor to truncate or compress it.
                await send_message(Message(
                    category=Constants.TASK,
                    topic=TopicType.CANCEL,
                    payload=TaskItem(data=messages, msg=str(e)),
                    sender=self.id(),
                    priority=-1,
                    session_id=message.context.session_id if message.context else "",
                    headers={"context": message.context}
                ))
                return ModelResponse(id=uuid.uuid4().hex, model=self.model_name, content=to_serializable(messages))
            raise e
        finally:
            message.context.context_info["llm_output"] = llm_response
        return llm_response

    def _init_context(self, context: Context):
        super()._init_context(context)
        logger.debug(f'init_context llm_agent {self.name()} {self.conf} {self.conf.context_rule}')

    async def run_hooks(self, context: Context, hook_point: str):
        """Execute hooks asynchronously"""
        from aworld.runners.hook.hook_factory import HookFactory
        from aworld.core.event.base import Message

        # Get all hooks for the specified hook point
        all_hooks = HookFactory.hooks(hook_point)
        hooks = all_hooks.get(hook_point, [])

        for hook in hooks:
            try:
                # Create a temporary Message object to pass to the hook
                message = Message(
                    category="agent_hook",
                    payload=None,
                    sender=self.id(),
                    session_id=context.session_id if hasattr(
                        context, 'session_id') else None,
                    headers={"context": message.context}
                )

                # Execute hook
                msg = await hook.exec(message, context)
                if msg:
                    logger.debug(f"Hook {hook.point()} executed successfully")
                    yield msg
            except Exception as e:
                logger.warning(f"Hook {hook.point()} execution failed: {traceback.format_exc()}")

    async def _add_system_message_to_memory(self, context: Context, content: str):
        if not self.system_prompt:
            return
        session_id = context.get_task().session_id
        task_id = context.get_task().id
        user_id = context.get_task().user_id

        histories = self.memory.get_last_n(0, filters={
            "agent_id": self.id(),
            "session_id": session_id,
            "task_id": task_id
        }, agent_memory_config=self.memory_config)
        if histories:
            logger.debug(f"🧠 [MEMORY:short-term] histories is not empty, do not need add system input to agent memory")
            return

        content = await self.custom_system_prompt(context=context, content=content, tool_list=self.tools)
        await self.memory.add(MemorySystemMessage(
            content=content,
            metadata=MessageMetadata(
                session_id=session_id,
                user_id=user_id,
                task_id=task_id,
                agent_id=self.id(),
                agent_name=self.name(),
            )
        ), agent_memory_config=self.memory_config)

    async def custom_system_prompt(self, context: Context, content: str, tool_list: List[str] = None):
        logger.info(f"llm_agent custom_system_prompt .. agent#{type(self)}#{self.id()}")
        return self.system_prompt_template.format(context=context, task=content, tool_list=tool_list)

    async def _add_human_input_to_memory(self, content: Any, context: Context, memory_type="init"):
        """Add user input to memory"""
        session_id = context.get_task().session_id
        user_id = context.get_task().user_id
        task_id = context.get_task().id

        await self.memory.add(MemoryHumanMessage(
            content=content,
            metadata=MessageMetadata(
                session_id=session_id,
                user_id=user_id,
                task_id=task_id,
                agent_id=self.id(),
                agent_name=self.name(),
            ),
            memory_type=memory_type
        ), agent_memory_config=self.memory_config)

    async def _add_llm_response_to_memory(self, llm_response, context: Context, history_messages: list, **kwargs):
        """Add LLM response to memory"""
        ai_message = MemoryAIMessage(
            content=llm_response.content,
            tool_calls=llm_response.tool_calls,
            metadata=MessageMetadata(
                session_id=context.get_task().session_id,
                user_id=context.get_task().user_id,
                task_id=context.get_task().id,
                agent_id=self.id(),
                agent_name=self.name()
            )
        )
        await self.memory.add(ai_message, agent_memory_config=self.memory_config)

    async def _add_tool_result_to_memory(self, tool_call_id: str, tool_result: ActionResult, context: Context):
        """Add tool result to memory"""
        if hasattr(tool_result, 'content') and isinstance(tool_result.content, str) and tool_result.content.startswith(
                "data:image"):
            image_content = tool_result.content
            tool_result.content = "this picture is below "
            await self._do_add_tool_result_to_memory(tool_call_id, tool_result, context)
            image_content = [
                {
                    "type": "text",
                    "text": f"this is file of tool_call_id:{tool_result.tool_call_id}"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_content
                    }
                }
            ]
            await self._add_human_input_to_memory(image_content, context, "message")
        else:
            await self._do_add_tool_result_to_memory(tool_call_id, tool_result, context)

    async def _do_add_tool_result_to_memory(self, tool_call_id: str, tool_result: ActionResult, context: Context):
        """Add tool result to memory"""
        tool_use_summary = None
        if isinstance(tool_result, ActionResult):
            tool_use_summary = tool_result.metadata.get("tool_use_summary")
        await self.memory.add(MemoryToolMessage(
            content=tool_result.content if hasattr(tool_result, 'content') else tool_result,
            tool_call_id=tool_call_id,
            status="success",
            metadata=MessageMetadata(
                session_id=context.get_task().session_id,
                user_id=context.get_task().user_id,
                task_id=context.get_task().id,
                agent_id=self.id(),
                agent_name=self.name(),
                summary_content=tool_use_summary
            )
        ), agent_memory_config=self.memory_config)

    async def send_llm_response_output(self, llm_response: ModelResponse, agent_result: AgentResult, context: Context,
                                       outputs: Outputs = None):
        """Send LLM response to output"""
        if not llm_response or llm_response.error:
            return
        if eventbus is None:
            logger.warn("=============== eventbus is none ============")
        llm_resp_output = MessageOutput(
            source=llm_response,
            metadata={"agent_id": self.id(), "agent_name": self.name(), "is_finished": self.finished}
        )
        if eventbus is not None and llm_response:
            await send_message(Message(
                category=Constants.OUTPUT,
                payload=llm_resp_output,
                sender=self.id(),
                session_id=context.session_id if context else "",
                headers={"context": context}
            ))
        elif not self.event_driven and outputs:
            await outputs.add_output(llm_resp_output)

    def is_agent_finished(self, llm_response: ModelResponse, agent_result: AgentResult) -> bool:
        if not agent_result.is_call_tool:
            self._finished = True
        return self.finished

    def _update_headers(self, input_message: Message) -> Dict[str, Any]:
        headers = input_message.headers.copy()
        headers['context'] = input_message.context
        headers['level'] = headers.get('level', 0) + 1
        if input_message.group_id:
            headers['parent_group_id'] = input_message.group_id
        return headers
