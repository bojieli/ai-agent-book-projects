# coding: utf-8

import os
import re

from typing import Tuple, Any

from aworld.core.tool.action_factory import ActionFactory
from aworld.core.common import ActionModel, ActionResult
from aworld.logs.util import logger
from aworld.core.tool.action import ExecutableAction
from aworld.models.llm import get_llm_model, call_llm_model


@ActionFactory.register(name="write_html",
                        desc="a tool use for write html.",
                        tool_name="html")
class WriteHTML(ExecutableAction):
    def act(self, action: ActionModel, **kwargs) -> Tuple[ActionResult, Any]:
        logger.info("start write html!")
        goal = action.params.get("goal")
        information = action.params.get("information")

        llm_conf = kwargs.get("llm_config")
        llm = get_llm_model(llm_conf)
        sys_prompt = "you are a helpful html writer."
        prompt = """Your task is to create a detailed and visually appealing HTML document based on the specified theme. 
        The document must meet the following requirements, and you should utilize the provided reference materials to ensure accuracy and aesthetic quality.
        1) HTML Document Requirements
        Design and write the HTML document according to the following specifications:
        Theme : {goal}
        Related Info: {information}
        Structural Requirements :
        Use semantic HTML tags (e.g., <header>, <main>, <footer>, <section>) to create a clear and organized structure.
        Ensure the document includes a header, navigation bar, main content area, and footer.
        If applicable, add additional sections such as a sidebar, or call-to-action buttons.
        Styling Requirements :
        Implement a visually appealing design using CSS, including color schemes, font choices, spacing adjustments, etc.
        Ensure the page has a responsive layout that works well on different devices (use media queries or frameworks like Bootstrap).
        Add animations or interactive features (e.g., hover effects on buttons, scroll-triggered animations) to enhance user experience.
        please give me html code directly, no need other words
        """

        messages = [{'role': 'system', 'content': sys_prompt},
                    {'role': 'user', 'content': prompt.format(goal=goal, information=information)}]

        output = call_llm_model(llm,
                                messages=messages,
                                model=llm_conf.llm_model_name,
                                temperature=llm_conf.llm_temperature)

        content = output.content
        html_pattern = re.compile(r'<html.*?>.*?</html>', re.DOTALL)
        matches = html_pattern.findall(content)

        title_pattern = re.compile(r'<title.*?>.*?</title>', re.DOTALL)
        filename = (title_pattern.findall(content)[0]
                    .replace("<title>", "")
                    .replace("</title>", "")
                    .replace(" ", "_") + ".html")

        with open(filename, "a", encoding='utf-8') as f:
            f.write(matches[0])

        abs_file_path = os.path.abspath(filename)
        msg = f'Successfully wrote html to {abs_file_path}'

        return ActionResult(content=msg, keep=True, is_done=True), None
