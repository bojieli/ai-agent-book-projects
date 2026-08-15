"""
This code is adapted from AgentS2 (https://github.com/simular-ai/Agent-S)
with modifications to suit specific requirements.
"""
import logging
import textwrap
from typing import Dict, List, Tuple

from aworld.config.conf import AgentConfig
from aworld.agents.llm_agent import Agent
from aworld.core.common import Observation

from aworld.core.task import Task
from aworld.core.context.base import Context
from aworld.core.event.base import Message
from aworld.models.llm import get_llm_model
from aworld.utils.common import sync_exec

from aworldAgent.grounding import ACI
from aworldAgent.prompt import GENERATOR_SYS_PROMPT, REFLECTION_SYS_PROMPT
from aworldAgent.utils import encode_image, extract_first_agent_function, parse_single_code_from_string, sanitize_code
from aworldAgent.utils import prune_image_messages, reps_action_result

logger = logging.getLogger("desktopenv.agent")


class Worker:
    def __init__(
        self,
        engine_params: Dict,
        grounding_agent: ACI,
        platform: str = "ubuntu",
        max_trajectory_length: int = 16,
        enable_reflection: bool = True,
    ):
        """
        Worker receives the main task and generates actions, without the need of hierarchical planning
        Args:
            engine_params: Dict
                Parameters for the multimodal engine
            grounding_agent: Agent
                The grounding agent to use
            platform: str
                OS platform the agent runs on (darwin, linux, windows)
            max_trajectory_length: int
                The amount of images turns to keep
            enable_reflection: bool
                Whether to enable reflection
        """
        # super().__init__(engine_params, platform)

        self.grounding_agent = grounding_agent
        self.max_trajectory_length = max_trajectory_length
        self.enable_reflection = enable_reflection
        self.use_thinking = engine_params.get("model", "") in [
            "claude-3-7-sonnet-20250219"
        ]

        self.generator_agent_config = AgentConfig(
            llm_provider=engine_params.get("engine_type", "openai"),
            llm_model_name=engine_params.get("model", "openai/o3",),
            llm_temperature=engine_params.get("temperature", 1.0),
            llm_base_url=engine_params.get("base_url", "https://openrouter.ai/api/v1"),
            llm_api_key=engine_params.get("api_key", ""),
        )

        self.reset()

    def reset(self):

        self.generator_agent = Agent(
            name="generator_agent",
            conf=self.generator_agent_config,
            system_prompt=GENERATOR_SYS_PROMPT,
            resp_parse_func=reps_action_result
        )

        self.reflection_agent = Agent(
            name="reflection_agent",
            conf=self.generator_agent_config,
            system_prompt=REFLECTION_SYS_PROMPT,
            resp_parse_func=reps_action_result
        )

        self.turn_count = 0
        self.worker_history = []
        self.reflections = []
        self.cost_this_turn = 0
        self.screenshot_inputs = []

        self.dummy_task = Task()
        self.dummy_context = Context()
        self.dummy_context.set_task(self.dummy_task)
        self.dummy_message = Message(headers={'context': self.dummy_context})

        self.planning_model = get_llm_model(self.generator_agent_config)

        self.first_done = False
        self.first_image = None

    def generate_next_action(
        self,
        instruction: str,
        obs: Dict,
    ) -> Tuple[Dict, List]:
        """
        Predict the next action(s) based on the current observation.
        """
        agent = self.grounding_agent
        generator_message = (
            ""
            if self.turn_count > 0
            else "The initial screen is provided. No action has been taken yet."
        )

        # Load the task into the system prompt
        if self.turn_count == 0:
            self.generator_agent.system_prompt = self.generator_agent.system_prompt.replace(
                "TASK_DESCRIPTION", instruction)

        # Get the per-step reflection
        reflection = None
        reflection_thoughts = None
        if self.enable_reflection:
            # Load the initial message
            if self.turn_count == 0:
                text_content = textwrap.dedent(
                    f"""
                    Task Description: {instruction}
                    Current Trajectory below:
                    """
                )
                updated_sys_prompt = (
                    self.reflection_agent.system_prompt + "\n" + text_content
                )
                self.reflection_agent.system_prompt = updated_sys_prompt

                image_content = [
                    {
                        "type": "text",
                        "text": f"The initial screen is provided. No action has been taken yet."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:image/png;base64," + encode_image(obs["screenshot"])
                        }
                    }
                ]
                self.reflection_agent._init_context(context=self.dummy_context)

                sync_exec(
                    self.reflection_agent._add_human_input_to_memory,
                    image_content,
                    self.dummy_context,
                    "message"
                )

            # Load the latest action
            else:

                image = "data:image/png;base64," + encode_image(obs["screenshot"])
                reflection_message = self.worker_history[-1] + "\n" + f"Here is function execute result: {obs['action_response']}.\n"

                reflection_observation = Observation(content=reflection_message, image=image)

                self.reflection_agent._init_context(context=self.dummy_context)
                reflection_actions = self.reflection_agent.policy(reflection_observation, message=self.dummy_message)

                reflection = reflection_actions[0].action_name
                reflection_thoughts = reflection_actions[0].policy_info

                self.reflections.append(reflection)

                generator_message += f"Here is your function execute result: {obs['action_response']}.\n"

                generator_message += f"REFLECTION: You may use this reflection on the previous action and overall trajectory:\n{reflection}\n"
                logger.info("REFLECTION: %s", reflection)

        if self.first_done:
            pass

        else:
            # Add finalized message to conversation
            generator_message += f"\nCurrent Text Buffer = [{','.join(agent.notes)}]\n"

            image = "data:image/png;base64," + encode_image(obs["screenshot"])
            generator_observation = Observation(content=generator_message, image=image)

            self.generator_agent._init_context(context=self.dummy_context)
            generator_actions = self.generator_agent.policy(generator_observation, message=self.dummy_message)

            plan = generator_actions[0].action_name
            plan_thoughts = generator_actions[0].policy_info

            prune_image_messages(self.generator_agent.memory.memory_store, 16)
            prune_image_messages(self.reflection_agent.memory.memory_store, 16)

            self.worker_history.append(plan)

            logger.info("FULL PLAN:\n %s", plan)

            # self.generator_agent.add_message(plan, role="assistant")
            # Use the grounding agent to convert agent_action("desc") into agent_action([x, y])

        try:
            agent.assign_coordinates(plan, obs)
            plan_code = parse_single_code_from_string(plan.split("Grounded Action")[-1])
            plan_code = sanitize_code(plan_code)
            plan_code = extract_first_agent_function(plan_code)
            exec_code = eval(plan_code)

        except Exception as e:
            logger.error("Error in parsing plan code: %s", e)
            plan_code = "agent.wait(1.0)"
            exec_code = eval(plan_code)

        executor_info = {
            "full_plan": plan,
            "executor_plan": plan,
            "plan_thoughts": plan_thoughts,
            "plan_code": plan_code,
            "reflection": reflection,
            "reflection_thoughts": reflection_thoughts,
        }
        self.turn_count += 1

        self.screenshot_inputs.append(obs["screenshot"])

        return executor_info, [exec_code]