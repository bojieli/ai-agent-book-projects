import logging
import os
import traceback
from typing import Dict, Any, List, Union
from typing import Optional

from aworld.core.event.base import Message
from aworldspace.base_agent import AworldBaseAgent
from pydantic import BaseModel, Field

import aworld.trace as trace
from aworld.config.conf import AgentConfig, ConfigDict
from aworld.config.conf import TaskConfig
from aworld.agents.llm_agent import Agent
from aworld.core.common import Observation, ActionModel
from aworld.core.memory import MemoryItem
from aworld.core.task import Task
from aworld.logs.util import logger
from aworld.models.llm import acall_llm_model
from aworld.models.model_response import ToolCall, Function
from aworld.output import Output, StreamingOutputs
from aworld.output import Outputs
from aworld.output.base import MessageOutput
from aworld.utils.common import sync_exec

BROWSER_SYSTEM_PROMPT = """You are a GUI agent. You are given a task and your action history, with screenshots. You need to perform the next action to complete the task.
## Output Format
```
Thought: ...
Action: ...
```
## Action Space
navigate(website='xxx') #Open the target website, usually the first action to open browser.
click(start_box='[x1, y1, x2, y2]')
left_double(start_box='[x1, y1, x2, y2]')
right_single(start_box='[x1, y1, x2, y2]')
drag(start_box='[x1, y1, x2, y2]', end_box='[x3, y3, x4, y4]')
hotkey(key='')
type(content='') #If you want to submit your input, use "\n" at the end of `content`.
scroll(direction='down or up or right or left')
wait() #Sleep for 5s and take a screenshot to check for any changes.
finished(content='xxx') # Use escape characters \\', \\", and \\n in content part to ensure we can parse the content in normal python string format.
## Note
- only one action per step.
- Use Chinese in `Thought` part.
- Write a small plan and finally summarize your next action (with its target element) in one sentence in `Thought` part.
## User Instruction
"""

import json
import re

MAX_IMAGE = 50


def parse_action_output(output_text):
    # 提取Thought部分
    logger.info(f"{output_text=}")
    thought_match = re.search(r'Thought:(.*?)\nAction:', output_text, re.DOTALL)
    thought = thought_match.group(1).strip() if thought_match else ""

    # 提取Action部分
    action_match = re.search(r'Action:(.*?)(?:\n|$)', output_text, re.DOTALL)
    action_text = action_match.group(1).strip() if action_match else ""

    # 初始化结果字典
    result = {
        "thought": thought,
        "action": "",
        "key": None,
        "content": None,
        "start_box": None,
        "end_box": None,
        "direction": None,
        "website": None,
    }

    if not action_text:
        return json.dumps(result, ensure_ascii=False)

    # tmp 兼容ui-tars1.5-7b
    action_text = action_text.replace("'(","'[").replace(")'","]'")

    # 解析action类型
    action_parts = action_text.split('(')
    action_type = action_parts[0]
    result["action"] = action_type

    # 解析参数
    if len(action_parts) > 1:
        params_text = action_parts[1].rstrip(')')
        params = {}

        # gpt-4o兼容
        if 'start_box' in params_text:
            params_text = params_text.replace(", ", " ").replace(",", " ")
        if 'end_box' in params_text:
            params_text = params_text.replace(" end_box", ", end_box")

        # 处理键值对参数
        for param in params_text.split(','):
            param = param.strip()

            if '=' in param:
                key, value = param.split('=', 1)
                key = key.strip()
                value = value.strip().strip('\'"')

                # 处理bbox格式
                if 'box' in key:
                    print(value)
                    # 提取坐标数字
                    numbers = re.findall(r'\d+', value)
                    print(numbers)
                    if numbers:
                        coords = [int(num) for num in numbers]
                        if len(coords) == 4:
                            if key == 'start_box':
                                result["start_box"] = coords
                            elif key == 'end_box':
                                result["end_box"] = coords
                        if len(coords) == 2:
                            if key == 'start_box':
                                result["start_box"] = [coords[0], coords[1], coords[0], coords[1]]
                            elif key == 'end_box':
                                result["end_box"] = [coords[0], coords[1], coords[0], coords[1]]
                elif key == 'key':
                    result["key"] = value.replace("pagedown", "PageDown").replace("pageup", "PageUp").replace("enter","Enter")
                elif key == 'content':
                    # 处理转义字符
                    value = value.replace('\\n', '\n').replace('\\"', '"').replace("\\'", "'")
                    result["content"] = value
                elif key == 'website':
                    result["website"] = value
                elif key == 'direction':
                    result["direction"] = value

    return result, thought, action_text


def parse_tool_call(line):
    # 提取 Action和param
    result, thought, action_text = parse_action_output(line)
    action = result['action']

    # 映射到实际函数名和参数
    if action == 'navigate':
        func_name = 'mcp__ms-playwright__browser_navigate'
        content = {'url': result['website']}

    elif action == 'click':
        func_name = 'mcp__ms-playwright__browser_screen_click'

        x = int((result["start_box"][0] + result["start_box"][2]) / 2)
        y = int((result["start_box"][1] + result["start_box"][3]) / 2)
        content = {'element': '', 'x': x, 'y': y}

    elif action == 'right_single':
        func_name = 'mcp__ms-playwright__browser_screen_click'

        x = int((result["start_box"][0] + result["start_box"][2]) / 2)
        y = int((result["start_box"][1] + result["start_box"][3]) / 2)
        content = {'element': 'right click target', 'x': x, 'y': y, 'button': 'right'}

    elif action == 'drag':
        func_name = 'mcp__ms-playwright__browser_screen_drag'

        x1 = int((result["start_box"][0] + result["start_box"][2]) / 2)
        y1 = int((result["start_box"][1] + result["start_box"][3]) / 2)
        x2 = int((result["end_box"][0] + result["end_box"][2]) / 2)
        y2 = int((result["end_box"][1] + result["end_box"][3]) / 2)

        content = {
            'element': f'drag from [{x1},{y1}] to [{x2},{y2}]',
            'startX': x1,
            'startY': y1,
            'endX': x2,
            'endY': y2
        }
    elif action == 'hotkey':
        func_name = 'mcp__ms-playwright__browser_press_key'
        content = {'key': result["key"]}
    elif action == 'type':
        func_name = 'mcp__ms-playwright__browser_screen_type'
        content = {'text': result['content']}
    elif action == 'scroll':
        # 暂时使用presskey代替scroll
        func_name = 'mcp__ms-playwright__browser_press_key'
        direction = result['direction']
        key_map = {
            'up': 'PageUp',
            'down': 'PageDown',
            'left': 'ArrowLeft',
            'right': 'ArrowRight'
        }
        key = key_map.get(direction, 'ArrowDown')
        content = {'key': key}
    elif action == 'wait':
        func_name = 'mcp__ms-playwright__browser_wait_for'
        content = {'time': 5}
    elif action == 'finished':
        func_name = "finished"
        content = result['content']
    else:
        return ""

    return Function(name=func_name, arguments=json.dumps(content)), thought, action_text, result

# eval code start


def identify_key_points(task):
    system_msg = """You are an expert tasked with analyzing a given task to identify the key points explicitly stated in the task description.

**Objective**: Carefully analyze the task description and extract the critical elements explicitly mentioned in the task for achieving its goal.

**Instructions**:
1. Read the task description carefully.
2. Identify and extract **key points** directly stated in the task description.
   - A **key point** is a critical element, condition, or step explicitly mentioned in the task description.
   - Do not infer or add any unstated elements.
   - Words such as "best," "highest," "cheapest," "latest," "most recent," "lowest," "closest," "highest-rated," "largest," and "newest" must go through the sort function(e.g., the key point should be "Filter by highest").

**Respond with**:
- **Key Points**: A numbered list of the explicit key points for completing this task, one per line, without explanations or additional details."""
    prompt = """Task: {task}"""
    text = prompt.format(task=task)
    messages = [
        {"role": "system", "content": system_msg},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": text}
            ],
        }
    ]
    return messages


def judge_image(task, image_path, key_points):
    system_msg = """You are an expert evaluator tasked with determining whether an image contains information about the necessary steps to complete a task.

**Objective**: Analyze the provided image and decide if it shows essential steps or evidence required for completing the task. Use your reasoning to explain your decision before assigning a score.

**Instructions**:
1. Provide a detailed description of the image, including its contents, visible elements, text (if any), and any notable features.

2. Carefully examine the image and evaluate whether it contains necessary steps or evidence crucial to task completion:  
- Identify key points that could be relevant to task completion, such as actions, progress indicators, tool usage, applied filters, or step-by-step instructions.  
- Does the image show actions, progress indicators, or critical information directly related to completing the task?  
- Is this information indispensable for understanding or ensuring task success?
- If the image contains partial but relevant information, consider its usefulness rather than dismissing it outright.

3. Provide your response in the following format:  
- **Reasoning**: Explain your thought process and observations. Mention specific elements in the image that indicate necessary steps, evidence, or lack thereof.  
- **Score**: Assign a score based on the reasoning, using the following scale:  
    - **1**: The image does not contain any necessary steps or relevant information.  
    - **2**: The image contains minimal or ambiguous information, unlikely to be essential.  
    - **3**: The image includes some relevant steps or hints but lacks clarity or completeness.  
    - **4**: The image contains important steps or evidence that are highly relevant but not fully comprehensive.  
    - **5**: The image clearly displays necessary steps or evidence crucial for completing the task.

Respond with:  
1. **Reasoning**: [Your explanation]  
2. **Score**: [1-5]"""

    # jpg_base64_str = encode_image(Image.open(image_path))

    prompt = """**Task**: {task}

**Key Points for Task Completion**: {key_points}

The snapshot of the web page is shown in the image."""
    text = prompt.format(task=task, key_points=key_points)

    messages = [
        {"role": "system", "content": system_msg},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": text},
                {
                    "type": "image_url",
                    "image_url": {"url": image_path, "detail": "high"},
                },
            ],
        }
    ]

    return messages


def WebJudge_Online_Mind2Web_eval(task, last_actions, images_path, image_responses, key_points, score_threshold):
    system_msg = """You are an expert in evaluating the performance of a web navigation agent. The agent is designed to help a human user navigate a website to complete a task. Given the user's task, the agent's action history, key points for task completion, some potentially important web pages in the agent's trajectory and their reasons, your goal is to determine whether the agent has completed the task and achieved all requirements.

Your response must strictly follow the following evaluation criteria!
*Important Evaluation Criteria*:
1: The filtered results must be displayed correctly. If filters were not properly applied (i.e., missing selection, missing confirmation, or no visible effect in results), the task is not considered successful.
2: You must carefully check whether these snapshots and action history meet these key points. Ensure that specific filter conditions, such as "best," "highest," "cheapest," "latest," "most recent," "lowest," "closest," "highest-rated," "largest," and "newest" are correctly applied using the filter function(e.g., sort function).
3: Certain key points or requirements should be applied by the filter. Otherwise, a search with all requirements as input will be deemed a failure since it cannot guarantee that all results meet the requirements!
4: If the task requires filtering by a specific range of money, years, or the number of beds and bathrooms, the applied filter must exactly match the given requirement. Any deviation results in failure. To ensure the task is successful, the applied filter must precisely match the specified range without being too broad or too narrow.
Examples of Failure Cases:
- If the requirement is less than $50, but the applied filter is less than $25, it is a failure.
- If the requirement is $1500-$2500, but the applied filter is $2000-$2500, it is a failure.
- If the requirement is $25-$200, but the applied filter is $0-$200, it is a failure.
- If the required years are 2004-2012, but the filter applied is 2001-2012, it is a failure.
- If the required years are before 2015, but the applied filter is 2000-2014, it is a failure.
- If the task requires exactly 2 beds, but the filter applied is 2+ beds, it is a failure.
5: Some tasks require a submission action or a display of results to be considered successful.
6: If the retrieved information is invalid or empty(e.g., No match was found), but the agent has correctly performed the required action, it should still be considered successful.
7: If the current page already displays all available items, then applying a filter is not necessary. As long as the agent selects items that meet the requirements (e.g., the cheapest or lowest price), the task is still considered successful.

*IMPORTANT*
Format your response into two lines as shown below:

Thoughts: <your thoughts and reasoning process based on double-checking each key points and the evaluation criteria>
Status: "success" or "failure"
"""
    prompt = """User Task: {task}

Key Points: {key_points}

Action History:
{last_actions}

The potentially important snapshots of the webpage in the agent's trajectory and their reasons:
{thoughts}"""

    whole_content_img = []
    whole_thoughts = []
    record = []
    pattern = r"[1-5]"
    for response, image_path in zip(image_responses, images_path):
        try:
            score_text = response.split("Score")[1]
            thought = response.split("**Reasoning**:")[-1].strip().lstrip("\n").split("\n\n")[0].replace('\n', ' ')
            score = re.findall(pattern, score_text)[0]
            record.append({"Response": response, "Score": int(score)})
        except Exception as e:
            print(f"Error processing response: {e}")
            score = 0
            record.append({"Response": response, "Score": 0})

        if int(score) >= score_threshold:
            # jpg_base64_str = encode_image(Image.open(image_path))
            whole_content_img.append(
                {
                    'type': 'image_url',
                    "image_url": {"url": image_path, "detail": "high"},
                }
            )
            if thought != "":
                whole_thoughts.append(thought)

    whole_content_img = whole_content_img[:MAX_IMAGE]
    whole_thoughts = whole_thoughts[:MAX_IMAGE]
    if len(whole_content_img) == 0:
        prompt = """User Task: {task}

Key Points: {key_points}

Action History:
{last_actions}"""
    text = prompt.format(task=task,
                         last_actions="\n".join(f"{i + 1}. {action}" for i, action in enumerate(last_actions)),
                         key_points=key_points,
                         thoughts="\n".join(f"{i + 1}. {thought}" for i, thought in enumerate(whole_thoughts)))

    messages = [
        {"role": "system", "content": system_msg},
        {
            "role": "user",
            "content": [
                           {"type": "text", "text": text}]
                       + whole_content_img
        }
    ]
    return messages, text, system_msg, record


# eval code end

class PlayWrightAgent(Agent):

    def __init__(self, conf: Union[Dict[str, Any], ConfigDict, AgentConfig], **kwargs):
        self.screen_capture = True
        self.step_images = []
        self.step_thoughts = []
        self.step_actions = []
        self.step_results = []
        self.success = False
        super().__init__(conf, **kwargs)

    async def async_policy(self, observation: Observation, info: Dict[str, Any] = {}, message: Message = None,
                           **kwargs) -> Union[
        List[ActionModel], None]:
        """The strategy of an agent can be to decide which tools to use in the environment, or to delegate tasks to other agents.

        Args:
            observation: The state observed from tools in the environment.
            info: Extended information is used to assist the agent to decide a policy.

        Returns:
            ActionModel sequence from agent policy
        """
        outputs = None
        if kwargs.get("outputs") and isinstance(kwargs.get("outputs"), Outputs):
            outputs = kwargs.get("outputs")

        # Get current step information for trace recording
        step = kwargs.get("step", 0)
        exp_id = kwargs.get("exp_id", None)
        source_span = trace.get_current_span()

        if hasattr(observation, 'context') and observation.context:
            self.task_histories = observation.context

        self._finished = False
        await self.async_desc_transform(message.context)

        self.tools = None
        if "data:image/jpeg;base64," in observation.content:
            logger.info("transfer base64 content to image")
            observation.image = observation.content
            observation.content = "observation:"
            self.step_images.append(observation.image)

        images = observation.images if self.conf.use_vision else None
        if self.conf.use_vision and not images and observation.image:
            images = [observation.image]

        messages = self.messages_transform(content=observation.content,
                                           image_urls=images,
                                           sys_prompt=self.system_prompt,
                                           agent_prompt=self.agent_prompt)

        self._log_messages(messages)
        if isinstance(messages[-1]['content'], list):
            messages[-1]['role'] = 'user'  # 有image的话必须使用user请求，而且不写入历史对话
            # self.memory.add(MemoryItem(
            #     content=messages[-1]['content'],
            #     metadata={
            #         "role": messages[-1]['role'],
            #         "agent_name": self.name(),
            #     }
            # ))
        else:
            self.memory.add(MemoryItem(
                content=messages[-1]['content'],
                metadata={
                    "role": messages[-1]['role'],
                    "agent_name": self.name(),
                }
            ))



        llm_response = None
        span_name = f"llm_call_{exp_id}"
        with trace.span(span_name) as llm_span:
            llm_span.set_attributes({
                "exp_id": exp_id,
                "step": step,
                "messages": json.dumps([str(m) for m in messages], ensure_ascii=False)
            })
            if source_span:
                source_span.set_attribute("messages", json.dumps([str(m) for m in messages], ensure_ascii=False))

            try:
                llm_response = await acall_llm_model(
                    self.llm,
                    messages=messages,
                    model=self.model_name,
                    # temperature=self.conf.llm_config.llm_temperature,
                    temperature=0.0,
                    tools=self.tools if not self.use_tools_in_prompt and self.tools else None,
                    stream=kwargs.get("stream", False)
                )

                # Record LLM response
                llm_span.set_attributes({
                    "llm_response": json.dumps(llm_response.to_dict(), ensure_ascii=False),
                    "tool_calls": json.dumps([tool_call.model_dump() for tool_call in
                                              llm_response.tool_calls] if llm_response.tool_calls else [],
                                             ensure_ascii=False),
                    "error": llm_response.error if llm_response.error else ""
                })

            except Exception as e:
                logger.warn(traceback.format_exc())
                llm_span.set_attribute("error", str(e))
                raise e
            finally:
                if llm_response:
                    use_tools = self.use_tool_list(llm_response)
                    is_use_tool_prompt = len(use_tools) > 0
                    if llm_response.error:
                        logger.info(f"llm result error: {llm_response.error}")
                    else:
                        self.memory.add(MemoryItem(
                            content=llm_response.content,
                            metadata={
                                "role": "assistant",
                                "agent_name": self.name(),
                                "tool_calls": llm_response.tool_calls if not self.use_tools_in_prompt else use_tools,
                                "is_use_tool_prompt": is_use_tool_prompt if not self.use_tools_in_prompt else False
                            }
                        ))

                        function, origin_thought, origin_action, origin_result = parse_tool_call(
                            llm_response.message['content'])
                        self.step_thoughts.append(origin_thought)
                        self.step_actions.append(origin_action)
                        self.step_results.append(origin_result)

                        if function.name == "finished":
                            self._finished = True
                            llm_response.content = "<answer>" + llm_response.content + "</answer>"
                            llm_response.tool_calls = None
                        else:
                            llm_response.content = None

                            tool_call = ToolCall(
                                id="tooluse_mock",
                                type="function",
                                function=function,
                            )
                            screen_capture = ToolCall(
                                id="screen_capture",
                                type="function",
                                function=Function(
                                    name="mcp__ms-playwright__browser_screen_capture",
                                    arguments="{}"
                                )
                            )
                            llm_response.tool_calls = [tool_call, screen_capture]
                else:
                    logger.error(f"{self.name()} failed to get LLM response")
                    raise RuntimeError(f"{self.name()} failed to get LLM response")

        if outputs and isinstance(outputs, Outputs):
            await outputs.add_output(MessageOutput(source=llm_response, json_parse=False))

        agent_result = await self.model_output_parser.parse(llm_response, agent_id=self.id())
        if not agent_result.is_call_tool:
            self._finished = True

        logger.info(self.step_thoughts)
        logger.info(self.step_actions)

        # now is eval code:
        logger.info(f"step:{step}")

        if self.finished or step >= 20:  # 暂时写死，这里应该是max_step
            task = self.task.split("Please first navigate to the target")[0]
            key_points_messages = identify_key_points(task)

            # eval_model_name = "shangshu.gpt-4o"
            eval_model_name = self.model_name
            tmp_llm_response = await acall_llm_model(
                self.llm,
                messages=key_points_messages,
                model=eval_model_name,
                temperature=0
            )

            key_points = tmp_llm_response.content
            key_points = key_points.replace("\n\n", "\n")

            try:
                key_points = key_points.split("**Key Points**:")[1]
                key_points = "\n".join(line.lstrip() for line in key_points.splitlines())
            except:
                key_points = key_points.split("Key Points:")[-1]
                key_points = "\n".join(line.lstrip() for line in key_points.splitlines())

            logger.info(f"key_points: {key_points}")

            tasks_messages = [judge_image(task, image_path, key_points) for image_path in self.step_images]

            #  这里暂时使用串行执行的写法
            image_responses = []
            for task_messages in tasks_messages:
                logger.info(task_messages)
                image_response = await acall_llm_model(
                    self.llm,  # 假设这是你传给函数的第一个参数
                    messages=task_messages,  # 每个请求的消息内容
                    model=eval_model_name,  # 模型名称
                    temperature=0  # 温度参数
                )
                image_responses.append(image_response)

            image_responses = [i.content for i in image_responses]

            logger.info(f"image_responses: {image_responses}")

            eval_messages, text, system_msg, record = WebJudge_Online_Mind2Web_eval(
                self.task, self.step_actions, self.step_images, image_responses, key_points, 3)
            response = await acall_llm_model(
                self.llm,
                messages=eval_messages,
                model=eval_model_name,
                temperature=0
            )
            eval_response = response.content

            logger.info(f"eval_response: {eval_response}")

            if "success" in eval_response.lower().split('status:')[1]:
                self.success = True

            # now is saving code:

            result_dict = {
                'task': task,
                'images': self.step_images,
                'actions': self.step_actions,
                'thoughts': self.step_thoughts,
                'results': self.step_results,
                'success': self.success,
                'final_answer': llm_response.content,
                'eval_response': eval_response,
                'is_done': self.finished,
                'done_step': step,
            }
            result_dict = json.dumps(result_dict, ensure_ascii=False)

            agent_result.actions[0].policy_info = result_dict
            agent_result.actions[0].tool_name = None
            agent_result.actions[0].action_name = None
            agent_result.actions[0].agent_name = self.name()
            # saving is over...

        return agent_result.actions


class Pipeline(AworldBaseAgent):
    class Valves(BaseModel):
        llm_provider: Optional[str] = Field(default=None, description="llm_model_name")
        llm_model_name: Optional[str] = Field(default=None, description="llm_model_name")
        llm_base_url: Optional[str] = Field(default=None, description="llm_base_urly")
        llm_api_key: Optional[str] = Field(default=None, description="llm api key")
        system_prompt: str = Field(default=BROWSER_SYSTEM_PROMPT, description="system_prompt")
        history_messages: int = Field(default=100, description="rounds of history messages")

    def __init__(self):
        self.valves = self.Valves()
        self.agent_config = AgentConfig(
            name=self.agent_name(),
            llm_provider=self.valves.llm_provider if self.valves.llm_provider else os.environ.get("LLM_PROVIDER"),
            llm_model_name=self.valves.llm_model_name if self.valves.llm_model_name else os.environ.get(
                "LLM_MODEL_NAME"),
            llm_api_key=self.valves.llm_api_key if self.valves.llm_api_key else os.environ.get("LLM_API_KEY"),
            llm_base_url=self.valves.llm_base_url if self.valves.llm_base_url else os.environ.get("LLM_BASE_URL"),
            system_prompt=self.valves.system_prompt if self.valves.system_prompt else BROWSER_SYSTEM_PROMPT
        )

        self.m2w_files = os.path.abspath(os.path.join(os.path.curdir, "aworldspace", "datasets", "online-mind2web"))

        logging.info(f"m2w_files path {self.m2w_files}")
        file_path = os.path.join(self.m2w_files, "Online_Mind2Web.json")

        with open(file_path, 'r') as file:
            self.full_dataset = json.load(file)
            logging.info("playwright_agent init success")

    # 重写build_agent
    async def build_agent(self, body: dict):
        agent_config = await self.get_agent_config(body)
        mcp_servers = await self.get_mcp_servers(body)

        agent = PlayWrightAgent(
            conf=agent_config,
            name=agent_config.name,
            system_prompt=agent_config.system_prompt,
            mcp_servers=mcp_servers,
            mcp_config=await self.load_mcp_config(),
            history_messages=await self.get_history_messages(body)
        )
        return agent

    async def get_custom_input(self, user_message: str, model_id: str, messages: List[dict], body: dict) -> Any:
        task = await self.get_m2w_task(int(user_message))
        return task['Task']

    async def get_agent_config(self, body):
        default_llm_provider = self.valves.llm_provider if self.valves.llm_provider else os.environ.get("LLM_PROVIDER")
        llm_model_name = self.valves.llm_model_name if self.valves.llm_model_name else os.environ.get("LLM_MODEL_NAME")
        llm_api_key = self.valves.llm_api_key if self.valves.llm_api_key else os.environ.get("LLM_API_KEY")
        llm_base_url = self.valves.llm_base_url if self.valves.llm_base_url else os.environ.get("LLM_BASE_URL")
        system_prompt = self.valves.system_prompt if self.valves.system_prompt else BROWSER_SYSTEM_PROMPT

        task = await self.get_task_from_body(body)
        logging.info(
            f"task llm config is: {task.llm_provider}, {task.llm_model_name}, {task.llm_api_key}, {task.llm_base_url}")

        return AgentConfig(
            name=self.agent_name(),
            llm_provider=task.llm_provider if task and task.llm_provider else default_llm_provider,
            llm_model_name=task.llm_model_name if task and task.llm_model_name else llm_model_name,
            llm_api_key=task.llm_api_key if task and task.llm_api_key else llm_api_key,
            llm_base_url=task.llm_base_url if task and task.llm_base_url else llm_base_url,
            system_prompt=task.task_system_prompt if task and task.task_system_prompt else system_prompt
        )

    def agent_name(self) -> str:
        return "PlaywrightAgent"

    async def get_mcp_servers(self, body) -> list[str]:
        task = await self.get_task_from_body(body)
        if task.mcp_servers:
            logging.info(f"mcp_servers from task: {task.mcp_servers}")
            return task.mcp_servers

        return [
            "ms-playwright"
        ]

    async def get_m2w_task(self, index) -> dict:
        logging.info(f"Start to process: m2w_task_{index}")
        m2w_task = self.full_dataset[index]
        logging.info(f"Detail: {m2w_task}")
        logging.info(f"Task: {m2w_task['confirmed_task']}")
        logging.info(f"Level: {m2w_task['level']}")
        logging.info(f"Website: {m2w_task['website']}")

        return self.add_file_path(m2w_task)

    async def custom_output_before_task(self, outputs: Outputs, chat_id: str, task: Task) -> None:
        task_config: TaskConfig = task.conf
        m2w_task = await self.get_m2w_task(int(task_config.ext['origin_message']))

        result = f"\n\n`Web TASK#{task_config.ext['origin_message']}`\n\n---\n\n"
        result += f"**Task**: {m2w_task['Task']}\n"
        result += f"**Level**: {m2w_task['level']}\n"
        result += f"**Website**: \n {m2w_task['website']}\n"
        result += f"\n\n-----\n\n"
        await outputs.add_output(Output(data=result))

    async def custom_output_after_task(self, outputs: Outputs, chat_id: str, task: Task):
        """
        check gaia task output
        Args:
            outputs:
            chat_id:
            task:

        Returns:

        """
        task_config: TaskConfig = task.conf
        web_task_id = int(task_config['ext']['origin_message'])
        web_task = await self.get_m2w_task(web_task_id)
        agent_result = ""
        if isinstance(outputs, StreamingOutputs):
            agent_result = await outputs._visited_outputs[-2].get_finished_response()  # read llm result
        # match = re.search(r"<answer>(.*?)</answer>", agent_result)
        result = ""
        # if match:
        #     answer = match.group(1)
        logging.info(f"Agent answer: {agent_result}")

        metadata = await outputs.get_metadata()
        if not metadata:
            await outputs.set_metadata({})
            metadata = await outputs.get_metadata()
        metadata['web_task'] = web_task
        return result

    def add_file_path(self, task: Dict[str, Any]
                      ):
        task["Task"] = "Task: " + task['confirmed_task'] + '\n' + "Please first navigate to the target " + "Website: " + \
                       task['website']
        return task

    async def load_mcp_config(self) -> dict:
        return {
            "mcpServers": {
                "ms-playwright": {
                    "command": "npx",
                    "args": [
                        "@playwright/mcp@0.0.27",
                        "--vision",
                        "--no-sandbox",
                        "--headless",
                        "--isolated"
                    ],
                    "env": {
                        "PLAYWRIGHT_TIMEOUT": "120000",
                        "SESSION_REQUEST_CONNECT_TIMEOUT": "120"
                    }
                }
            }
        }
