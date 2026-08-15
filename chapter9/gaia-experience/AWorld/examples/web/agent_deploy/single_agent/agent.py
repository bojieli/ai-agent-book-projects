import logging
import os
import json
from aworld.cmd.data_model import BaseAWorldAgent, ChatCompletionRequest
from aworld.config.conf import AgentConfig, TaskConfig
from aworld.agents.llm_agent import Agent
from aworld.core.task import Task
from aworld.runner import Runners

logger = logging.getLogger(__name__)


class AWorldAgent(BaseAWorldAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def name(self):
        return "Single Agent Demo"

    def description(self):
        return "Single Agent Demo with search and playwright fetch ability"

    async def run(self, prompt: str = None, request: ChatCompletionRequest = None):
        llm_provider = os.getenv("LLM_PROVIDER_DEMO", "openai")
        llm_model_name = os.getenv("LLM_MODEL_NAME_DEMO")
        llm_api_key = os.getenv("LLM_API_KEY_DEMO")
        llm_base_url = os.getenv("LLM_BASE_URL_DEMO")
        llm_temperature = os.getenv("LLM_TEMPERATURE_DEMO", 0.0)

        if not llm_model_name or not llm_api_key or not llm_base_url:
            raise ValueError(
                "LLM_MODEL_NAME, LLM_API_KEY, LLM_BASE_URL must be set in your envrionment variables"
            )

        agent_config = AgentConfig(
            llm_provider=llm_provider,
            llm_model_name=llm_model_name,
            llm_api_key=llm_api_key,
            llm_base_url=llm_base_url,
            llm_temperature=llm_temperature,
        )

        path_cwd = os.path.dirname(os.path.abspath(__file__))
        mcp_path = os.path.join(path_cwd, "mcp.json")
        with open(mcp_path, "r") as f:
            mcp_config = json.load(f)

        super_agent = Agent(
            conf=agent_config,
            name="🙋🏻‍♂️ Single Agent Demo",
            system_prompt="""You are a Super Search Agent, your goal is to accomplish the ultimate task following the instructions.""",
            mcp_config=mcp_config,
            # mcp_servers=mcp_config.get("mcpServers", {}).keys(),
            # mcp_servers=["aworldsearch-server", "aworld-playwright"],
            mcp_servers=["google-pse-search", "aworld-playwright"],
            feedback_tool_result=True,
        )

        if prompt is None and request is not None:
            prompt = request.messages[-1].content

        task = Task(
            input=prompt,
            agent=super_agent,
            conf=TaskConfig(max_steps=20),
            session_id=request.session_id,
            endless_threshold=50,
        )

        with open("data/output.txt", "w") as f:
            f.write(f"AGENT START: agent={self.name()}, prompt: {prompt}\n")
            async for output in Runners.streamed_run_task(task).stream_events():
                f.write(f"Agent {self.name()} received output: {output}\n")
                yield output
