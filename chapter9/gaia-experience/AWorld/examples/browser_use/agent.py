# coding: utf-8
# Copyright (c) 2025 inclusionAI.

import re
import time
import traceback
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field

from langchain_core.messages import HumanMessage, BaseMessage, AIMessage, ToolMessage
from pydantic import ValidationError

from aworld.core.agent.base import AgentFactory, AgentResult
from aworld.agents.llm_agent import Agent
from examples.browser_use.prompts import SystemPrompt
from examples.browser_use.utils import convert_input_messages, extract_json_from_model_output, estimate_messages_tokens
from examples.browser_use.common import AgentState, AgentStepInfo, AgentHistory, PolicyMetadata, AgentBrain
from aworld.config.conf import AgentConfig, ConfigDict
from aworld.core.common import Observation, ActionModel, ToolActionInfo, ActionResult
from aworld.logs.util import logger
from examples.browser_use.prompts import AgentMessagePrompt
from examples.common.tools.common import Tools
from examples.common.tools.tool_action import BrowserAction


@dataclass
class Trajectory:
    """A class to store agent history records, including all observations, info and AgentResult"""
    history: List[tuple[List[BaseMessage], Observation, Dict[str, Any], AIMessage, AgentResult]] = field(
        default_factory=list)

    def add_step(self, input_messages: List[BaseMessage], observation: Observation, info: Dict[str, Any],
                 output_message: AIMessage, agent_result: AgentResult):
        """Add a step to the history"""
        self.history.append((input_messages, observation, info, output_message, agent_result))

    def get_history(self) -> List[tuple[List[BaseMessage], Observation, Dict[str, Any], AIMessage, AgentResult]]:
        """Get the complete history"""
        return self.history

    def save_history(self, file_path: str):
        his_li = []
        for input_messages, observation, info, output_message, agent_result in self.get_history():
            llm_input = [{"type": input_message.type, "content": input_message.content} for input_message in
                         input_messages]
            llm_output = output_message.content
            his_li.append({"llm_input": llm_input, "llm_output": llm_output})
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(his_li, f, ensure_ascii=False, indent=4)


class BrowserAgent(Agent):
    def __init__(self, conf: Union[Dict[str, Any], ConfigDict, AgentConfig], name: str, **kwargs):
        super(BrowserAgent, self).__init__(conf=conf, name=name, **kwargs)
        self.state = AgentState()
        self.settings = self.conf
        provider = self.conf.llm_config.llm_provider
        if self.conf.llm_config.llm_provider:
            self.conf.llm_config.llm_provider = "chat" + provider
        else:
            raise Exception("no llm provider")

        self.save_file_path = self.conf.save_file_path
        self.available_actions = self._build_action_prompt()
        # Note: Removed _message_manager initialization as it's no longer used
        # Initialize trajectory
        self.trajectory = Trajectory()
        self._init = False

    def reset(self, options: Dict[str, Any] = None):
        super(BrowserAgent, self).reset(options)

        # Reset trajectory
        self.trajectory = Trajectory()

        # Note: Removed _message_manager initialization as it's no longer used
        # _estimate_tokens_for_messages method now directly uses functions from utils.py

        self._init = True

    def _build_action_prompt(self) -> str:
        def _prompt(info: ToolActionInfo) -> str:
            s = f'{info.desc}: \n'
            s += '{' + str(info.name) + ': '
            if info.input_params:
                s += str({k: {"title": k, "type": v.type} for k, v in info.input_params.items()})
            s += '}'
            return s

        val = "\n".join([_prompt(v.value) for k, v in BrowserAction.__members__.items()])
        return val

    def _log_message_sequence(self, input_messages: List[BaseMessage]) -> None:
        """Log the sequence of messages for debugging purposes"""
        logger.info(f"[agent] 🔍 Invoking LLM with {len(input_messages)} messages")
        logger.info("[agent] 📝 Messages sequence:")
        for i, msg in enumerate(input_messages):
            prefix = msg.type
            logger.info(f"[agent] Message {i + 1}: {prefix} ===================================")
            if isinstance(msg.content, list):
                for item in msg.content:
                    if item.get('type') == 'text':
                        logger.info(f"[agent] Text content: {item.get('text')}")
                    elif item.get('type') == 'image_url':
                        # Only print the first 30 characters of image URL to avoid printing entire base64
                        image_url = item.get('image_url', {}).get('url', '')
                        if image_url.startswith('data:image'):
                            logger.info(f"[agent] Image: [Base64 image data]")
                        else:
                            logger.info(f"[agent] Image URL: {image_url[:30]}...")
            else:
                content = str(msg.content)
                chunk_size = 500
                for j in range(0, len(content), chunk_size):
                    chunk = content[j:j + chunk_size]
                    if j == 0:
                        logger.info(f"[agent] Content: {chunk}")
                    else:
                        logger.info(f"[agent] Content (continued): {chunk}")

            if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    logger.info(f"[agent] Tool call: {tool_call.get('name')} - ID: {tool_call.get('id')}")
                    args = str(tool_call.get('args', {}))[:1000]
                    logger.info(f"[agent] Tool args: {args}...")

    def save_process(self, file_path: str):
        self.trajectory.save_history(file_path)

    def policy(self,
               observation: Observation,
               info: Dict[str, Any] = None, **kwargs) -> Union[List[ActionModel], None]:
        start_time = time.time()

        if self._init is False:
            self.reset({"task": observation.content})

        self._finished = False
        # Save current observation to state for message construction
        self.state.last_result = observation.action_result

        if self.conf.max_steps <= self.state.n_steps:
            logger.info('Last step finishing up')

        logger.info(f'[agent] step {self.state.n_steps}')

        # Use the new method to build messages, passing the current observation
        input_messages = self.build_messages_from_trajectory_and_observation(observation=observation)

        # Note: Special message addition has been moved to build_messages_from_trajectory_and_observation

        # Estimate token count
        tokens = self._estimate_tokens_for_messages(input_messages)

        llm_result = None
        output_message = None
        try:
            # Log the message sequence
            self._log_message_sequence(input_messages)

            output_message, llm_result = self._do_policy(input_messages)

            if not llm_result:
                logger.error("[agent] ❌ Failed to parse LLM response")
                return [ActionModel(tool_name=Tools.BROWSER.value, action_name="stop")]

            self.state.n_steps += 1

            # No longer need to remove the last state message
            # self._message_manager._remove_last_state_message()

            if self.state.stopped or self.state.paused:
                logger.info('Browser gent paused after getting state')
                return [ActionModel(tool_name=Tools.BROWSER.value, action_name="stop")]

            tool_action = llm_result.actions

            # Add the current step to the trajectory
            self.trajectory.add_step(input_messages, observation, info, output_message, llm_result)

        except Exception as e:
            logger.warning(traceback.format_exc())
            # No longer need to remove the last state message
            # self._message_manager._remove_last_state_message()
            logger.error(f"[agent] ❌ Error parsing LLM response: {str(e)}")

            # Create an AgentResult object with an empty actions list
            error_result = AgentResult(
                current_state=AgentBrain(
                    evaluation_previous_goal="Failed due to error",
                    memory=f"Error occurred: {str(e)}",
                    thought="Recover from error",
                    next_goal="Recover from error"
                ),
                actions=[]  # Empty actions list
            )

            # Add the error state to the trajectory
            self.trajectory.add_step(input_messages, observation, info, output_message, error_result)

            raise RuntimeError("Browser agent encountered exception while making the policy.", e)
        finally:
            if llm_result:
                # Only keep the history_item creation part
                metadata = PolicyMetadata(
                    number=self.state.n_steps,
                    start_time=start_time,
                    end_time=time.time(),
                    input_tokens=tokens,
                )
                self._make_history_item(llm_result, observation, observation.action_result, metadata)
            else:
                logger.warning("no result to record!")

        return tool_action

    def _do_policy(self, input_messages: list[BaseMessage]) -> Tuple[AIMessage, AgentResult]:
        THINK_TAGS = re.compile(r'<think>.*?</think>', re.DOTALL)

        def _remove_think_tags(text: str) -> str:
            """Remove think tags from text"""
            return re.sub(THINK_TAGS, '', text)

        input_messages = self._convert_input_messages(input_messages)
        output_message = None
        try:

            output_message = self.llm.invoke(input_messages)

            if not output_message or not output_message.content:
                logger.warning("[agent] LLM returned empty response")
                return output_message, AgentResult(
                    current_state=AgentBrain(evaluation_previous_goal="", memory="", thought="", next_goal=""),
                    actions=[ActionModel(agent_name=self.id(), tool_name='browser', action_name="stop")])
        except:
            logger.error(f"[agent] Response content: {output_message}")
            raise RuntimeError('call llm fail, please check llm conf and network.')

        if self.model_name == 'deepseek-reasoner':
            output_message.content = _remove_think_tags(output_message.content)
        try:
            # Get max retries from config
            max_retries = self.settings.get('max_llm_json_retries', 3)
            retry_count = 0
            json_parse_error = None

            while retry_count < max_retries:
                try:
                    parsed_json = extract_json_from_model_output(output_message.content)
                    # If parsing succeeds, break out of the retry loop
                    json_parse_error = None
                    break
                except ValueError as e:
                    # Store the error and retry
                    json_parse_error = e
                    retry_count += 1
                    logger.warning(f"[agent] Failed to parse JSON (attempt {retry_count}/{max_retries}): {str(e)}")

                    if retry_count < max_retries:
                        # Add a reminder message about JSON format with specific structure guidance
                        format_reminder = HumanMessage(
                            content="Your responses must be always JSON with the specified format. Make sure your response includes a 'current_state' object with 'evaluation_previous_goal', 'memory', and 'next_goal' fields, and an 'action' array with the actions to perform. Do not include any explanatory text, only return the raw JSON.")
                        retry_messages = input_messages.copy()
                        retry_messages.append(format_reminder)

                        # Retry with the updated messages
                        logger.info(
                            f"[agent] Retrying LLM invocation ({retry_count}/{max_retries}) with format reminder")
                        output_message = self.llm.invoke(retry_messages)

                        # Check for empty response during retry
                        if not output_message or not output_message.content:
                            logger.warning(
                                f"[agent] LLM returned empty response on retry attempt {retry_count}/{max_retries}")
                            # Continue to next retry instead of immediately returning
                            continue

                        if self.model_name == 'deepseek-reasoner':
                            output_message.content = _remove_think_tags(output_message.content)

            # If all retries failed, raise the last error
            if json_parse_error:
                logger.error(f"[agent] ❌ All {max_retries} attempts to parse JSON failed")
                raise json_parse_error

            logger.info((f"llm response: {parsed_json}"))
            try:
                agent_brain = AgentBrain(**parsed_json['current_state'])
            except:
                agent_brain = None
            actions = parsed_json.get('action')
            result = []
            if not actions:
                actions = parsed_json.get("actions")
            if not actions:
                logger.warning("agent not policy  an action.")
                self._finished = True
                return output_message, AgentResult(current_state=agent_brain,
                                                   actions=[ActionModel(tool_name='browser',
                                                                        agent_name=self.id(),
                                                                        action_name="done")])

            for action in actions:
                if "action_name" in action:
                    action_name = action['action_name']
                    browser_action = BrowserAction.get_value_by_name(action_name)
                    if not browser_action:
                        logger.warning(f"Unsupported action: {action_name}")
                    if action_name == "done":
                        self._finished = True
                    action_model = ActionModel(agent_name=self.id(),
                                               tool_name='browser',
                                               action_name=action_name,
                                               params=action.get('params', {}))
                    result.append(action_model)
                else:
                    for k, v in action.items():
                        browser_action = BrowserAction.get_value_by_name(k)
                        if not browser_action:
                            logger.warning(f"Unsupported action: {k}")

                        action_model = ActionModel(agent_name=self.id(), tool_name='browser', action_name=k, params=v)
                        result.append(action_model)
                        if k == "done":
                            self._finished = True
            return output_message, AgentResult(current_state=agent_brain, actions=result)
        except (ValueError, ValidationError) as e:
            logger.warning(f'Failed to parse model output: {output_message} {str(e)}')
            raise ValueError('Could not parse response.')

    def _convert_input_messages(self, input_messages: list[BaseMessage]) -> list[BaseMessage]:
        """Convert input messages to the correct format"""
        if self.model_name == 'deepseek-reasoner' or self.model_name.startswith('deepseek-r1'):
            return convert_input_messages(input_messages, self.model_name)
        else:
            return input_messages

    def _make_history_item(self,
                           model_output: AgentResult | None,
                           state: Observation,
                           result: list[ActionResult],
                           metadata: Optional[PolicyMetadata] = None) -> None:
        content = ""
        if hasattr(state, 'dom_tree') and state.dom_tree is not None:
            if hasattr(state.dom_tree, 'element_tree'):
                content = state.dom_tree.element_tree.__repr__()
            else:
                content = str(state.dom_tree)

        history_item = AgentHistory(model_output=model_output,
                                    result=state.action_result,
                                    metadata=metadata,
                                    content=content,
                                    base64_img=state.image if hasattr(state, 'image') else None)

        self.state.history.history.append(history_item)

    def _process_action_result(self, action_result, messages, tool_call=None):
        """Helper method to process an action result and add appropriate messages"""
        if action_result.content is not None:
            messages.append(HumanMessage(content='Action result: ' + action_result.content))
        elif action_result.error is not None:
            # Assemble error message when error information exists
            messages.append(HumanMessage(content='Action result: ' + action_result.error))
            if tool_call is not None:
                logger.warning(f"Action {tool_call} failed: {action_result.error}")
            else:
                logger.warning(f"Action failed: {action_result.error}")
            # If there is an error but success is true, log the error and terminate the program as the result is invalid
            if action_result.success is True:
                error_msg = f"Invalid result: success=True but error message exists: {action_result.error}"
                logger.error(error_msg)
                raise ValueError(error_msg)
        return action_result.error is not None

    def build_messages_from_trajectory_and_observation(self, observation: Optional[Observation] = None) -> List[
        BaseMessage]:
        """
        Build complete message history from trajectory and current observation
        
        Args:
            observation: Current observation object, if None current observation won't be added
        """
        messages = []
        # Add system message
        system_message = SystemPrompt(
            max_actions_per_step=self.settings.get('max_actions_per_step')
        ).get_system_message()
        if isinstance(system_message, tuple):
            system_message = system_message[0]
        messages.append(system_message)

        tool_calling_method = self.settings.get("tool_calling_method")
        llm_provider = self.conf.llm_config.llm_provider

        if tool_calling_method == 'raw' or (tool_calling_method == 'auto' and (
                llm_provider == 'deepseek-reasoner' or llm_provider.startswith('deepseek-r1'))):
            message_context = f'\n\nAvailable actions: {self.available_actions}'
        else:
            message_context = None

        # Add task context (if any)
        if message_context:
            context_message = HumanMessage(content='Context for the task' + message_context)
            messages.append(context_message)

        # Add task message
        task_message = HumanMessage(
            content=f'Your ultimate task is: """{self.task}""". If you achieved your ultimate task, stop everything and use the done action in the next step to complete the task. If not, continue as usual.'
        )
        messages.append(task_message)

        # Add example output
        placeholder_message = HumanMessage(content='Example output:')
        messages.append(placeholder_message)

        # Add example tool call
        tool_calls = [
            {
                'name': 'AgentOutput',
                'args': {
                    'current_state': {
                        'evaluation_previous_goal': 'Success - I opend the first page',
                        'memory': 'Starting with the new task. I have completed 1/10 steps',
                        'thought': 'From the current page I can get information about all the companies.',
                        'next_goal': 'Click on company a',
                    },
                    'action': [{'click_element': {'index': 0}}],
                },
                'id': '1',
                'type': 'tool_call',
            }
        ]
        example_tool_call = AIMessage(
            content='',
            tool_calls=tool_calls,
        )
        messages.append(example_tool_call)

        # Add first tool message with "Browser started" content
        messages.append(ToolMessage(content='Browser started', tool_call_id='1'))

        # Add task history marker
        messages.append(HumanMessage(content='[Your task history memory starts here]'))

        # Add available file paths (if any)
        if self.settings.get('available_file_paths'):
            filepaths_msg = HumanMessage(
                content=f'Here are file paths you can use: {self.settings.get("available_file_paths")}')
            messages.append(filepaths_msg)
        previous_action_entries = []
        # Add messages from the history trajectory
        for input_msgs, obs, info, output_msg, llm_result in self.trajectory.get_history():
            # Check the previous step's actionResult
            has_error = False
            if obs.action_result is not None:
                # The previous action entries should match with action results
                if len(previous_action_entries) == 0:
                    # if previous_action_entries is empty，process action_result directly
                    logger.info(
                        f"History item with action_result count ({len(obs.action_result)}) with empty previous actions - skipping count check")
                elif len(previous_action_entries) == len(obs.action_result):
                    for i, one_action_result in enumerate(obs.action_result):
                        has_error = self._process_action_result(one_action_result, messages,
                                                                previous_action_entries[i]) or has_error
                else:
                    # If sizes don't match, this is a critical error
                    error_msg = f"Action results count ({len(obs.action_result)}) doesn't match action entries count ({len(previous_action_entries)})"
                    logger.error(error_msg)
                    has_error = True
                    # raise ValueError(error_msg)

            # Add agent response
            if llm_result:
                # Create AI message
                output_data = llm_result.model_dump(mode='json', exclude_unset=True)
                action_entries = [{action.action_name: action.params} for action in llm_result.actions]
                output_data["action"] = action_entries
                if "actions" in output_data:
                    del output_data["actions"]

                # Calculate tool_id based on trajectory history. If no actions yet, start with ID 1
                tool_id = 1 if len(self.trajectory.get_history()) == 0 else len(self.trajectory.get_history()) + 1
                tool_calls = [
                    {
                        'name': 'AgentOutput',
                        'args': output_data,
                        'id': str(tool_id),
                        'type': 'tool_call',
                    }
                ]
                previous_action_entries = action_entries
                ai_message = AIMessage(
                    content='',
                    tool_calls=tool_calls,
                )
                messages.append(ai_message)

                # Add empty tool message after each AIMessage
                messages.append(ToolMessage(content='', tool_call_id=str(tool_id)))

        # Add current observation - using the passed observation parameter instead of self.state.current_observation
        if observation:
            # Check if the current observation has an action_result with error
            has_error = False
            if hasattr(observation, 'action_result') and observation.action_result is not None:
                # Match action results with previous actions
                if len(previous_action_entries) == 0:
                    # if previous_action_entries is empty，process action_result directly
                    logger.info(
                        f"Current observation with action_result count ({len(observation.action_result)}) with empty previous actions - skipping count check")
                elif len(previous_action_entries) == len(observation.action_result):
                    for i, one_action_result in enumerate(observation.action_result):
                        has_error = self._process_action_result(one_action_result, messages,
                                                                previous_action_entries[i]) or has_error
                else:
                    # If sizes don't match, this is a critical error
                    error_msg = f"Action results count ({len(observation.action_result)}) doesn't match action entries count ({len(previous_action_entries)})"
                    logger.error(error_msg)
                    has_error = True

            # If there's an error, append observation content outside the loop
            if has_error and observation.content:
                messages.append(HumanMessage(content=observation.content))
            # If no error, process the observation normally
            elif not has_error:
                step_info = AgentStepInfo(number=self.state.n_steps, max_steps=self.conf.max_steps)
                if hasattr(observation, 'dom_tree') and observation.dom_tree:
                    state_message = AgentMessagePrompt(
                        observation,
                        self.state.last_result,
                        include_attributes=self.settings.get('include_attributes',
                                                             ["title", "type", "name", "role", "aria-label",
                                                              "placeholder", "value", "alt", "aria-expanded",
                                                              "data-date-format"]),
                        step_info=step_info,
                    ).get_user_message(self.settings.get('use_vision'))
                    messages.append(state_message)
                elif observation.content:
                    messages.append(HumanMessage(content=observation.content))

        # Add special message for the last step
        # Note: Moved here from policy method to centralize all message building logic
        if self.conf.max_steps <= self.state.n_steps:
            last_step_message = f"""
                Now comes your last step. Use only the "done" action now. No other actions - so here your action sequence must have length 1.
                \nIf the task is not yet fully finished as requested by the user, set success in "done" to false! E.g. if not all steps are fully completed.
                \nIf the task is fully finished, set success in "done" to true.
                \nInclude everything you found out for the ultimate task in the done text.
            """
            messages.append(HumanMessage(content=[{'type': 'text', 'text': last_step_message}]))

        return messages

    def _estimate_tokens_for_messages(self, messages: List[BaseMessage]) -> int:
        """Roughly estimate token count for message list"""
        # Note: Using estimate_messages_tokens function from utils.py instead of calling _message_manager
        # This decouples the dependency on MessageManager
        return estimate_messages_tokens(
            messages,
            image_tokens=self.settings.get('image_tokens', 800),
            estimated_characters_per_token=self.settings.get('estimated_characters_per_token', 3)
        )
