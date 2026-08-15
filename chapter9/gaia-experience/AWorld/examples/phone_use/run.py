# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import os

from aworld.config import AgentConfig
from aworld.core.task import Task
from aworld.runner import Runners
from examples.common.tools.common import Agents, Tools
from examples.common.tools.conf import AndroidToolConfig
from examples.phone_use.agent import AndroidAgent

# os.environ["LLM_MODEL_NAME"] = "YOUR_LLM_MODEL_NAME"
# os.environ["LLM_BASE_URL"] = "YOUR_LLM_BASE_URL"
# os.environ["LLM_API_KEY"] = "YOUR_LLM_API_KEY"

def main():
    android_tool_config = AndroidToolConfig(avd_name='8ABX0PHWU',
                                            headless=False,
                                            max_retry=2)

    agent_config: AgentConfig = AgentConfig(
        llm_provider=os.getenv("LLM_PROVIDER", "openai"),
        llm_model_name=os.getenv("LLM_MODEL_NAME"),
        llm_base_url=os.getenv("LLM_BASE_URL"),
        llm_api_key=os.getenv("LLM_API_KEY"),
        llm_temperature=os.getenv("LLM_TEMPERATURE", 0.0)
    )
    agent = AndroidAgent(name=Agents.ANDROID.value, conf=agent_config)

    task = Task(
        input="""open rednote""",
        agent=agent,
        tools_conf={Tools.ANDROID.value: android_tool_config}
    )
    Runners.sync_run_task(task)


if __name__ == '__main__':
    main()
