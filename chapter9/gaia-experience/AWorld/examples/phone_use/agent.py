# coding: utf-8
# Copyright (c) 2025 inclusionAI.

import json
import time
import traceback
from typing import Dict, Any, Optional, List, Union

from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage

from examples.phone_use.prompts import SYSTEM_PROMPT, LAST_STEP_PROMPT
from examples.phone_use.utils import (
    AgentState,
    AgentHistory,
    AgentHistoryList,
    ActionResult,
    PolicyMetadata,
    AgentBrain,
    Trajectory
)
from examples.browser_use.common import AgentStepInfo
from aworld.config.conf import AgentConfig, ConfigDict
from aworld.core.agent.base import AgentResult
from aworld.agents.llm_agent import Agent
from aworld.core.common import Observation, ActionModel, ToolActionInfo
from aworld.logs.util import logger
from examples.common.tools.tool_action import AndroidAction


class AndroidAgent(Agent):
    def __init__(self, conf: Union[Dict[str, Any], ConfigDict, AgentConfig], name: str, **kwargs):
        super(AndroidAgent, self).__init__(conf=conf, name=name, **kwargs)
        provider = self.conf.llm_config.llm_provider
        if self.conf.llm_config.llm_provider:
            self.conf.llm_config.llm_provider = "chat" + provider
        else:
            raise Exception("no llm provider")
        self.available_actions_desc = self._build_action_prompt()
        # Settings
        self.settings = self.conf

    def reset(self, options: Dict[str, Any] = None):
        super(AndroidAgent, self).reset(options)
        # State
        self.state = AgentState()
        # History
        self.history = AgentHistoryList(history=[])
        self.trajectory = Trajectory(history=[])

    def _build_action_prompt(self) -> str:
        def _prompt(info: ToolActionInfo) -> str:
            s = f'{info.desc}:\n'
            s += '{' + str(info.name) + ': '
            if info.input_params:
                s += str({k: {"title": k, "type": v} for k, v in info.input_params.items()})
            s += '}'
            return s

        # Iterate over all android actions
        val = "\n".join([_prompt(v.value) for k, v in AndroidAction.__members__.items()])
        return val

    def policy(self,
               observation: Observation,
               info: Dict[str, Any] = None,
               **kwargs) -> Union[List[ActionModel], None]:
        self._finished = False
        step_info = AgentStepInfo(number=self.state.n_steps, max_steps=self.conf.max_steps)
        last_step_msg = None
        if step_info and step_info.is_last_step():
            # Add last step warning if needed
            last_step_msg = HumanMessage(
                content=LAST_STEP_PROMPT)
            logger.info('Last step finishing up')

        logger.info(f'[agent] 📍 Step {self.state.n_steps}')
        step_start_time = time.time()

        try:

            xml_content, base64_img = observation.dom_tree, observation.image

            if xml_content is None:
                logger.error("[agent] ⚠ Failed to get UI state, stopping task")
                self.stop()
                return None

            self.state.last_result = (xml_content, base64_img if base64_img else "")

            logger.info("[agent] 🤖 Analyzing current state with LLM...")
            a_step_msg = HumanMessage(content=[
                {
                    "type": "text",
                    "text": f"""
                        Task: {self.task}
                        Current Step: {self.state.n_steps}
                        
                        Please analyze the current interface and decide the next action. Please directly return the response in JSON format without any other text or code block markers.
                    """
                },
                {
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{self.state.image}"
                }
            ])

            messages = [SystemMessage(content=SYSTEM_PROMPT)]
            if last_step_msg:
                messages.append(last_step_msg)
            messages.append(a_step_msg)

            logger.info(f"[agent] VLM Input last message: {messages[-1]}")
            llm_result = None
            try:
                llm_result = self._do_policy(messages)

                if self.state.stopped or self.state.paused:
                    logger.info('Android agent paused after getting state')
                    return [ActionModel(tool_name='android', action_name="stop")]

                tool_action = llm_result.actions

                step_metadata = PolicyMetadata(
                    start_time=step_start_time,
                    end_time=time.time(),
                    number=self.state.n_steps,
                    input_tokens=1
                )

                history_item = AgentHistory(
                    result=[ActionResult(success=True)],
                    metadata=step_metadata,
                    content=xml_content,
                    base64_img=base64_img
                )
                self.history.history.append(history_item)

                if self.settings.save_history and self.settings.history_path:
                    self.history.save_to_file(self.settings.history_path)

                logger.info(f'📍 Step {self.state.n_steps} starts to execute')

                self.state.n_steps += 1
                self.state.consecutive_failures = 0
                return tool_action

            except Exception as e:
                logger.warning(traceback.format_exc())
                raise RuntimeError("Android agent encountered exception while making the policy.", e)
            finally:
                if llm_result:
                    self.trajectory.add_step(observation, info, llm_result)
                    metadata = PolicyMetadata(
                        number=self.state.n_steps,
                        start_time=step_start_time,
                        end_time=time.time(),
                        input_tokens=1
                    )
                    self._make_history_item(llm_result, observation, metadata)
                else:
                    logger.warning("no result to record!")

        except json.JSONDecodeError as e:
            logger.error("[agent] ❌ JSON parsing error")
            raise
        except Exception as e:
            logger.error(f"[agent] ❌ Action execution error: {str(e)}")
            raise

    def _do_policy(self, input_messages: list[BaseMessage]) -> AgentResult:
        response = self.llm.invoke(input_messages)
        content = response.content

        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        action_data = json.loads(content)
        brain_state = AgentBrain(**action_data["current_state"])

        logger.info(f"[agent] ⚠ Eval: {brain_state.evaluation_previous_goal}")
        logger.info(f"[agent] 🧠 Memory: {brain_state.memory}")
        logger.info(f"[agent] 🎯 Next goal: {brain_state.next_goal}")

        actions = action_data.get('action')
        result = []
        if not actions:
            actions = action_data.get("actions")

        # print actions
        logger.info(f"[agent] VLM Output actions: {actions}")
        for action in actions:
            action_type = action.get('type')
            if not action_type:
                logger.warning(f"Action missing type: {action}")
                continue

            params = {}
            if 'type' == action_type:
                action_type = 'input_text'
            if 'params' in action:
                params = action['params']
            if 'index' in action:
                params['index'] = action['index']
            if 'type' in action:
                params['type'] = action['type']
            if 'text' in action:
                params['text'] = action['text']

            action_model = ActionModel(
                tool_name='android',
                action_name=action_type,
                params=params
            )
            result.append(action_model)

        return AgentResult(current_state=brain_state, actions=result)

    def _make_history_item(self,
                           model_output: AgentResult | None,
                           state: Observation,
                           metadata: Optional[PolicyMetadata] = None) -> None:
        if isinstance(state, dict):
            state = Observation(**state)

        history_item = AgentHistory(
            model_output=model_output,
            result=state.action_result,
            metadata=metadata,
            content=state.dom_tree,
            base64_img=state.image
        )
        self.state.history.history.append(history_item)

    def pause(self) -> None:
        """Pause the agent"""
        logger.info('🔄 Pausing Agent')
        self.state.paused = True

    def resume(self) -> None:
        """Resume the agent"""
        logger.info('▶️ Agent resuming')
        self.state.paused = False

    def stop(self) -> None:
        """Stop the agent"""
        logger.info('⏹️ Agent stopping')
        self.state.stopped = True
