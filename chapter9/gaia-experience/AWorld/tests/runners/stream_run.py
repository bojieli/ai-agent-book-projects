# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import asyncio
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv
from rich.table import Table
from rich.status import Status
from rich.console import Console

from aworld.agents.llm_agent import Agent
from aworld.config.conf import AgentConfig, TaskConfig
from aworld.core.task import Task
from aworld.output import MessageOutput, WorkSpace
from aworld.output.base import StepOutput, ToolResultOutput
from aworld.output.ui.base import AworldUI
from aworld.output.utils import consume_content
from aworld.runner import Runners


@dataclass
class RichAworldUI(AworldUI):
    console: Console = field(default_factory=Console)
    status: Status = None
    workspace: WorkSpace = None

    async def message_output(self, __output__: MessageOutput):
        result = []

        async def __log_item(item):
            result.append(item)
            self.console.print(item, end="")

        if __output__.reason_generator or __output__.response_generator:
            if __output__.reason_generator:
                await consume_content(__output__.reason_generator, __log_item)
            if __output__.reason_generator:
                await consume_content(__output__.response_generator, __log_item)
        else:
            await consume_content(__output__.reasoning, __log_item)
            await consume_content(__output__.response, __log_item)
        # if __output__.tool_calls:
        #     await consume_content(__output__.tool_calls, __log_item)
        self.console.print("")

    async def tool_result(self, output: ToolResultOutput):
        """
            tool_result
        """
        table = Table(show_header=False, header_style="bold magenta",
                      title=f"Call Tools#ID_{output.origin_tool_call.id}")
        table.add_column("name", style="dim", width=12)
        table.add_column("content")
        table.add_row("function_name", output.origin_tool_call.function.name)
        table.add_row("arguments", output.origin_tool_call.function.arguments)
        table.add_row("result", output.data)
        self.console.print(table)

    async def step(self, output: StepOutput):
        if output.status == "START":
            self.console.print(f"[bold green]{output.name} ✈️START ...")
            self.status = self.console.status(f"[bold green]{output.name} RUNNING ...")
            self.status.start()
        elif output.status == "FINISHED":
            self.status.stop()
            self.console.print(f"[bold green]{output.name} 🛬FINISHED ...")
        elif output.status == "FAILED":
            self.status.stop()
            self.console.print(f"[bold red]{output.name} 💥FAILED ...")
        else:
            self.status.stop()
            self.console.print(f"============={output.name} ❓❓❓UNKNOWN#{output.status} ======================")


def run():
    load_dotenv()
    agent_config = AgentConfig(
        llm_provider="openai",
        llm_model_name=os.environ["LLM_MODEL_NAME"],
        llm_api_key=os.environ["LLM_API_KEY"],
        llm_base_url=os.environ["LLM_BASE_URL"]
    )

    AMAP_API_KEY = os.environ['AMAP_API_KEY']
    amap_sys_prompt = "You are a helpful agent."
    amap_agent = Agent(
        conf=agent_config,
        name="amap_agent",
        system_prompt=amap_sys_prompt,
        mcp_servers=["amap-amap-sse"],  # MCP server name for agent to use
        history_messages=100,
        mcp_config={
            "mcpServers": {
                "amap-amap-sse": {
                    "url": f"https://mcp.amap.com/sse?key={AMAP_API_KEY}",
                    "timeout": 5.0,
                    "sse_read_timeout": 300.0
                }
            }
        }
    )

    user_input = (
        "How long does it take to drive from Hangzhou of Zhejiang to  Weihai of Shandong (generate a table with columns for starting point, destination, duration, distance), "
        "which cities are passed along the way, what interesting places are there along the route, "
        "and finally generate the content as markdown and save it")


    async def _run(agent, input):
        task = Task(
            input=input,
            agent=agent,
            conf=TaskConfig()
        )

        rich_ui = RichAworldUI()

        async for output in Runners.streamed_run_task(task).stream_events():
            await AworldUI.parse_output(output, rich_ui)


    asyncio.run(_run(amap_agent, user_input))
