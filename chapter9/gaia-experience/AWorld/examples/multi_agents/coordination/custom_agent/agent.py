# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import copy
import json
import traceback
from typing import Dict, Any, List, Union

from aworld.core.event.base import Message
from aworld.utils.common import sync_exec
from examples.multi_agents.coordination.custom_agent.prompts import execute_system_prompt, plan_system_prompt, plan_done_prompt, \
    plan_postfix_prompt, init_prompt
from examples.common.tools.common import Agents
from aworld.core.agent.base import AgentResult
from aworld.agents.llm_agent import Agent
from aworld.models.llm import call_llm_model
from aworld.config.conf import AgentConfig, ConfigDict
from aworld.core.common import Observation, ActionModel
from aworld.logs.util import logger
from examples.multi_agents.coordination.custom_agent.utils import extract_pattern


class ExecuteAgent(Agent):
    def __init__(self, conf: Union[Dict[str, Any], ConfigDict, AgentConfig], name: str, **kwargs):
        super(ExecuteAgent, self).__init__(conf=conf, name=name, **kwargs)

    def id(self) -> str:
        return Agents.EXECUTE.value

    def reset(self, options: Dict[str, Any] = None):
        """Execute agent reset need query task as input."""
        super().reset(options)

        self.system_prompt = execute_system_prompt.format(task=self.task)
        self.step_reset = False

    async def async_policy(self, observation: Observation, info: Dict[str, Any] = {}, message: Message = None,
                           **kwargs) -> Union[List[ActionModel], None]:
        await self.async_desc_transform(message.context)
        return self._common(observation, info)

    def policy(self,
               observation: Observation,
               info: Dict[str, Any] = None,
               message: Message = None,
               **kwargs) -> List[ActionModel] | None:
        self.desc_transform(message.context)
        return self._common(observation, info)

    def _common(self, observation, info):
        self._finished = False
        content = observation.content

        llm_result = None
        ## build input of llm
        input_content = [
            {'role': 'system', 'content': self.system_prompt},
        ]
        for traj in self.trajectory:
            # Handle multiple messages in content
            if isinstance(traj[0].content, list):
                input_content.extend(traj[0].content)
            else:
                input_content.append(traj[0].content)

            if traj[-1].tool_calls is not None:
                input_content.append(
                    {'role': 'assistant', 'content': '', 'tool_calls': traj[-1].tool_calls})
            else:
                input_content.append({'role': 'assistant', 'content': traj[-1].content})

        if content is None:
            content = observation.action_result[0].error
        if not self.trajectory:
            new_messages = [{"role": "user", "content": content}]
            input_content.extend(new_messages)
        else:
            # Collect existing tool_call_ids from input_content
            existing_tool_call_ids = {
                msg.get("tool_call_id") for msg in input_content
                if msg.get("role") == "tool" and msg.get("tool_call_id")
            }

            new_messages = []
            for traj in self.trajectory:
                if traj[-1].tool_calls is not None:
                    # Handle multiple tool calls
                    for tool_call in traj[-1].tool_calls:
                        # Only add if this tool_call_id doesn't exist in input_content
                        if tool_call.id not in existing_tool_call_ids:
                            new_messages.append({
                                "role": "tool",
                                "content": content,
                                "tool_call_id": tool_call.id
                            })
            if new_messages:
                input_content.extend(new_messages)
            else:
                input_content.append({"role": "user", "content": content})

            # Validate tool_calls and tool messages pairing
            assistant_tool_calls = []
            tool_responses = []
            for msg in input_content:
                if msg.get("role") == "assistant" and msg.get("tool_calls"):
                    assistant_tool_calls.extend(msg["tool_calls"])
                elif msg.get("role") == "tool":
                    tool_responses.append(msg.get("tool_call_id"))

            # Check if all tool_calls have corresponding responses
            tool_call_ids = {call.id for call in assistant_tool_calls}
            tool_response_ids = set(tool_responses)
            if tool_call_ids != tool_response_ids:
                missing_calls = tool_call_ids - tool_response_ids
                extra_responses = tool_response_ids - tool_call_ids
                error_msg = f"Tool calls and responses mismatch. Missing responses for tool_calls: {missing_calls}, Extra responses: {extra_responses}"
                logger.error(error_msg)
                raise ValueError(error_msg)

        tool_calls = []
        try:
            llm_result = call_llm_model(self.llm, input_content, model=self.model_name,
                                        tools=self.tools, temperature=0)
            logger.info(f"Execute response: {llm_result.message}")
            res = sync_exec(self.model_output_parser.parse, llm_result, agent_id=self.id())
            content = res.actions[0].policy_info
            tool_calls = llm_result.tool_calls
        except Exception as e:
            logger.warning(traceback.format_exc())
        finally:
            if llm_result:
                ob = copy.deepcopy(observation)
                ob.content = new_messages
                self.trajectory.append((ob, info, llm_result))
            else:
                logger.warning("no result to record!")

        res = []
        if tool_calls:
            for tool_call in tool_calls:
                tool_action_name: str = tool_call.function.name
                if not tool_action_name:
                    continue

                names = tool_action_name.split("__")
                tool_name = names[0]
                action_name = '__'.join(names[1:]) if len(names) > 1 else ''
                params = json.loads(tool_call.function.arguments)
                res.append(ActionModel(agent_name=Agents.EXECUTE.value,
                                       tool_name=tool_name,
                                       action_name=action_name,
                                       params=params))

        if res:
            res[0].policy_info = content
            self._finished = False
        elif content:
            policy_info = extract_pattern(content, "final_answer")
            if policy_info:
                res.append(ActionModel(agent_name=Agents.EXECUTE.value,
                                       policy_info=policy_info))
                self._finished = True
            else:
                res.append(ActionModel(agent_name=Agents.EXECUTE.value,
                                       policy_info=content))

        logger.info(f">>> execute result: {res}")

        result = AgentResult(actions=res,
                             current_state=None)
        return result.actions


class PlanAgent(Agent):
    def __init__(self, conf: Union[Dict[str, Any], ConfigDict, AgentConfig], name: str, **kwargs):
        super(PlanAgent, self).__init__(name=name, conf=conf, **kwargs)

    def id(self) -> str:
        return Agents.PLAN.value

    def reset(self, options: Dict[str, Any] = None):
        """Execute agent reset need query task as input."""
        super().reset(options)

        self.system_prompt = plan_system_prompt.format(task=self.task)
        self.done_prompt = plan_done_prompt.format(task=self.task)
        self.postfix_prompt = plan_postfix_prompt.format(task=self.task)
        self.first_prompt = init_prompt
        self.first = True
        self.step_reset = False

    async def async_policy(self, observation: Observation, info: Dict[str, Any] = {}, message: Message = None,
                           **kwargs) -> Union[List[ActionModel], None]:
        await self.async_desc_transform(message.context)
        return self._common(observation, info)

    def policy(self,
               observation: Observation,
               info: Dict[str, Any] = None,
               message: Message = None,
               **kwargs) -> List[ActionModel] | None:
        self._finished = False
        self.desc_transform(message.context)
        return self._common(observation, info)

    def _common(self, observation, info):
        llm_result = None
        input_content = [
            {'role': 'system', 'content': self.system_prompt},
        ]
        # build input of llm based history
        for traj in self.trajectory:
            input_content.append({'role': 'user', 'content': traj[0].content})
            # plan agent no tool to call, use content
            input_content.append({'role': 'assistant', 'content': traj[-1].content})

        message = observation.content
        if self.first_prompt:
            message = self.first_prompt
            self.first_prompt = None

        input_content.append({"role": "user", "content": message})
        try:
            llm_result = call_llm_model(self.llm, messages=input_content, model=self.model_name)
            logger.info(f"Plan response: {llm_result.message}")
        except Exception as e:
            logger.warning(traceback.format_exc())
            raise e
        finally:
            if llm_result:
                ob = copy.deepcopy(observation)
                ob.content = message
                self.trajectory.append((ob, info, llm_result))
            else:
                logger.warning("no result to record!")
        res = sync_exec(self.model_output_parser.parse, llm_result, agent_id=self.id())
        content = res.actions[0].policy_info
        if "TASK_DONE" not in content:
            content += self.done_prompt
        else:
            # The task is done, and the assistant agent need to give the final answer about the original task
            content += self.postfix_prompt
            if not self.first:
                self._finished = True

        self.first = False
        logger.info(f">>> plan result: {content}")
        result = AgentResult(actions=[ActionModel(agent_name=Agents.PLAN.value,
                                                  tool_name=Agents.EXECUTE.value,
                                                  policy_info=content)],
                             current_state=None)
        return result.actions
