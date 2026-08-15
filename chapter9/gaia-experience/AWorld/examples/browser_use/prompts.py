# coding: utf-8

from datetime import datetime
from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from examples.browser_use.common import AgentStepInfo
from aworld.core.common import Observation, ActionResult

PROMPT_TEMPLATE = """
You are an AI agent designed to automate browser tasks. Your goal is to accomplish the ultimate task following the rules.

# Input Format
Task
Previous steps
Current URL
Open Tabs
Interactive Elements
[index]<type>text</type>
- index: Numeric identifier for interaction
- type: HTML element type (button, input, etc.)
- text: Element description
Example:
[33]<button>Submit Form</button>

- Only elements with numeric indexes in [] are interactive
- elements without [] provide only context

# Response Rules
1. RESPONSE FORMAT: You must ALWAYS respond with valid JSON in this exact format:
{{"current_state": {{"evaluation_previous_goal": "Success|Failed|Unknown - Analyze the current elements and the image to check if the previous goals/actions are successful like intended by the task. Mention if something unexpected happened. Shortly state why/why not",
"memory": "Description of what has been done and what you need to remember. Be very specific. Count here ALWAYS how many times you have done something and how many remain. E.g. 0 out of 10 websites analyzed. Continue with abc and xyz",
"thought": "Your thought or reasoning based on the ultimate task and current observations",
"next_goal": "What needs to be done with the next immediate action"}},
"action":[{{"one_action_name": {{// action-specific parameter}}}}, // ... more actions in sequence]}}

2. ACTIONS: You can specify multiple actions in the list to be executed in sequence. But always specify only one action name per item. Use maximum {max_actions} actions per sequence.
Common action sequences:
- Form filling: [{{"input_text": {{"index": 1, "text": "username"}}}}, {{"input_text": {{"index": 2, "text": "password"}}}}, {{"click_element": {{"index": 3}}}}]
- Navigation and extraction: [{{"go_to_url": {{"url": "https://example.com"}}}}, {{"extract_content": {{"goal": "extract the names"}}}}]
- Actions are executed in the given order
- If the page changes after an action, the sequence is interrupted and you get the new state.
- Only provide the action sequence until an action which changes the page state significantly.
- Try to be efficient, e.g. fill forms at once, or chain actions where nothing changes on the page
- only use multiple actions if it makes sense.

3. ELEMENT INTERACTION:
- Only use indexes of the interactive elements
- Elements marked with "[]Non-interactive text" are non-interactive

4. NAVIGATION & ERROR HANDLING:
- If no suitable elements exist, use other functions to complete the task
- If stuck, try alternative approaches - like going back to a previous page, new search, new tab etc.
- Handle popups/cookies by accepting or closing them
- Use scroll to find elements you are looking for
- If you want to research something, open a new tab instead of using the current tab
- If captcha pops up, try to solve it - else try a different approach
- If the page is not fully loaded, use wait action

5. TASK COMPLETION:
- Use the done action as the last action as soon as the ultimate task is complete
- Dont use "done" before you are done with everything the user asked you, except you reach the last step of max_steps. 
- If you reach your last step, use the done action even if the task is not fully finished. Provide all the information you have gathered so far. If the ultimate task is completly finished set success to true. If not everything the user asked for is completed set success in done to false!
- If you have to do something repeatedly for example the task says for "each", or "for all", or "x times", count always inside "memory" how many times you have done it and how many remain. Don't stop until you have completed like the task asked you. Only call done after the last step.
- Don't hallucinate actions
- Make sure you include everything you found out for the ultimate task in the done text parameter. Do not just say you are done, but include the requested information of the task. 

6. VISUAL CONTEXT:
- When an image is provided, use it to understand the page layout
- Bounding boxes with labels on their top right corner correspond to element indexes

7. Form filling:
- If you fill an input field and your action sequence is interrupted, most often something changed e.g. suggestions popped up under the field.

8. Long tasks:
- Keep track of the status and subresults in the memory. 

9. Extraction:
- If your task is to find information - call extract_content on the specific pages to get and store the information.
Your responses must be always JSON with the specified format. 
"""


class SystemPrompt:
    def __init__(self,
                 max_actions_per_step: int = 10,
                 override_system_message: Optional[str] = None,
                 extend_system_message: Optional[str] = None):
        self.max_actions_per_step = max_actions_per_step
        if override_system_message:
            prompt = override_system_message
        else:
            prompt = PROMPT_TEMPLATE.format(max_actions=self.max_actions_per_step)

        if extend_system_message:
            prompt += f'\n{extend_system_message}'

        self.system_message = SystemMessage(content=prompt)

    def get_system_message(self) -> SystemMessage:
        """
        Get the system prompt for the agent.

        Returns:
            SystemMessage: Formatted system prompt
        """
        return self.system_message


class AgentMessagePrompt:
    def __init__(
            self,
            state: Observation,
            result: Optional[List[ActionResult]] = None,
            include_attributes: list[str] = [],
            step_info: Optional[AgentStepInfo] = None,
    ):
        self.state = state
        self.result = result
        self.include_attributes = include_attributes
        self.step_info = step_info

    def get_user_message(self, use_vision: bool = True) -> HumanMessage:
        elements_text = self.state.dom_tree.element_tree.clickable_elements_to_string(
            include_attributes=self.include_attributes)

        pixels_above = self.state.info.get('pixels_above', 0)
        pixels_below = self.state.info.get('pixels_below', 0)

        if elements_text != '':
            if pixels_above > 0:
                elements_text = (
                    f'... {pixels_above} pixels above - scroll or extract content to see more ...\n{elements_text}'
                )
            else:
                elements_text = f'[Start of page]\n{elements_text}'
            if pixels_below > 0:
                elements_text = (
                    f'{elements_text}\n... {pixels_below} pixels below - scroll or extract content to see more ...'
                )
            else:
                elements_text = f'{elements_text}\n[End of page]'
        else:
            elements_text = 'empty page'

        if self.step_info:
            step_info_description = f'Current step: {self.step_info.number}/{self.step_info.max_steps}'
        else:
            step_info_description = ''
        time_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        step_info_description += f'Current date and time: {time_str}'

        state_description = f"""
[Task history memory ends]
[Current state starts here]
The following is one-time information - if you need to remember it write it to memory:
Current url: {self.state.info.get("url")}
Interactive elements from top layer of the current page inside the viewport:
{elements_text}
{step_info_description}
"""

        if self.result:
            for i, result in enumerate(self.result):
                if result.content:
                    state_description += f'\nAction result {i + 1}/{len(self.result)}: {result.content}'
                if result.error:
                    # only use last line of error
                    error = result.error.split('\n')[-1]
                    state_description += f'\nAction error {i + 1}/{len(self.result)}: ...{error}'

        if self.state.image and use_vision == True:
            # Format message for vision model
            return HumanMessage(
                content=[
                    {'type': 'text', 'text': state_description},
                    {
                        'type': 'image_url',
                        'image_url': {'url': f'data:image/png;base64,{self.state.image}'},  # , 'detail': 'low'
                    },
                ]
            )

        return HumanMessage(content=state_description)


class PlannerPrompt(SystemPrompt):
    def get_system_message(self) -> SystemMessage:
        return SystemMessage(
            content="""You are a planning agent that helps break down tasks into smaller steps and reason about the current state.
Your role is to:
1. Analyze the current state and history
2. Evaluate progress towards the ultimate goal
3. Identify potential challenges or roadblocks
4. Suggest the next high-level steps to take

Inside your messages, there will be AI messages from different agents with different formats.

Your output format should be always a JSON object with the following fields:
{
    "state_analysis": "Brief analysis of the current state and what has been done so far",
    "progress_evaluation": "Evaluation of progress towards the ultimate goal (as percentage and description)",
    "challenges": "List any potential challenges or roadblocks",
    "next_steps": "List 2-3 concrete next steps to take",
    "reasoning": "Explain your reasoning for the suggested next steps"
}

Ignore the other AI messages output structures.
don't forget the index param for input_text action.
Keep your responses concise and focused on actionable insights."""
        )
