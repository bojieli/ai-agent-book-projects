# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import os

from aworld.config.conf import ModelConfig
from aworld.core.task import Task
from aworld.runner import Runners
from examples.browser_use.agent import BrowserAgent
from examples.browser_use.config import BrowserAgentConfig
from examples.common.tools.common import Agents, Tools
from examples.common.tools.conf import BrowserToolConfig

# os.environ["LLM_MODEL_NAME"] = "YOUR_LLM_MODEL_NAME"
# os.environ["LLM_BASE_URL"] = "YOUR_LLM_BASE_URL"
# os.environ["LLM_API_KEY"] = "YOUR_LLM_API_KEY"

if __name__ == '__main__':
    llm_config = ModelConfig(
        llm_provider=os.getenv("LLM_PROVIDER", "openai"),
        llm_model_name=os.getenv("LLM_MODEL_NAME"),
        llm_base_url=os.getenv("LLM_BASE_URL"),
        llm_api_key=os.getenv("LLM_API_KEY"),
        llm_temperature=os.getenv("LLM_TEMPERATURE", 0.0)
    )
    browser_tool_config = BrowserToolConfig(width=1280,
                                            height=720,
                                            headless=False,
                                            keep_browser_open=True,
                                            use_async=True,
                                            custom_executor=True,
                                            llm_config=llm_config)
    agent_config = BrowserAgentConfig(
        name=Agents.BROWSER.value,
        tool_calling_method="raw",
        llm_config=llm_config,
        max_actions_per_step=10,
        max_input_tokens=128000,
        working_dir="",
        # llm model not supported vision, need to set `False`
        # use_vision=False
    )

    task_config = {
        'max_steps': 100,
        'max_actions_per_step': 100
    }

    task = Task(
        input="""step1: first go to https://www.dangdang.com/ and search for 'the little prince' and rank by sales from high to low, get the first 5 results and put the products info in memory.
        step 2: write each product's title, price, discount, and publisher information to a fully structured HTML document with write_to_file, ensuring that the data is presented in a table with visible grid lines.
        step3: open the html file in browser by go_to_url""",
        agent=BrowserAgent(conf=agent_config, name=Agents.BROWSER.value, tool_names=[Tools.BROWSER.name]),
        tools_conf={Tools.BROWSER.value: browser_tool_config},
        conf=task_config
    )
    Runners.sync_run_task(task)
