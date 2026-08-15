# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import asyncio
import json
import os

from dotenv import load_dotenv

from aworld.agents.llm_agent import Agent
from aworld.config.conf import AgentConfig, TaskConfig
from aworld.core.task import Task

from aworld.runner import Runners
from aworld.runners.callback.decorator import reg_callback


@reg_callback("print_content")
def simple_callback(content):
    """Simple callback function, prints content and returns it

        Args:
            content: Content to print

        Returns:
            The input content
        """
    print(f"callback content: {content}")
    return content

async def run():
    load_dotenv()
    llm_provider = os.getenv("LLM_PROVIDER_WEATHER", "openai")
    llm_model_name = os.getenv("LLM_MODEL_NAME_WEATHER")
    llm_api_key = os.getenv("LLM_API_KEY_WEATHER")
    llm_base_url = os.getenv("LLM_BASE_URL_WEATHER")
    llm_temperature = os.getenv("LLM_TEMPERATURE_WEATHER", 0.0)

    agent_config = AgentConfig(
        llm_provider=llm_provider,
        llm_model_name=llm_model_name,
        llm_api_key=llm_api_key,
        llm_base_url=llm_base_url,
        llm_temperature=llm_temperature,
    )
    #mcp_servers = ["filewrite_server", "fileread_server"]
    #mcp_servers = ["amap-amap-sse","filewrite_server", "fileread_server"]
    #mcp_servers = ["file_server"]
    #mcp_servers = ["amap-amap-sse"]
    mcp_servers = ["aworldsearch_server"]
    #mcp_servers = ["gen_video_server"]
   # mcp_servers = ["picsearch_server"]
    #mcp_servers = ["gen_audio_server"]
    #mcp_servers = ["playwright"]
    #mcp_servers = ["tavily-mcp"]

    path_cwd = os.path.dirname(os.path.abspath(__file__))
    mcp_path = os.path.join(path_cwd, "mcp.json")
    with open(mcp_path, "r") as f:
        mcp_config = json.load(f)

    print("-------------------mcp_config--------------",mcp_config)

    #sand_box = Sandbox(mcp_servers=mcp_servers,mcp_config=mcp_config)
    # You can specify sandbox
    #sand_box = Sandbox(mcp_servers=mcp_servers, mcp_config=mcp_config,env_type=SandboxEnvType.K8S)
    #sand_box = Sandbox(mcp_servers=mcp_servers, mcp_config=mcp_config,env_type=SandboxEnvType.SUPERCOMPUTER)

    search_sys_prompt = "You are a versatile assistant"
    search = Agent(
        conf=agent_config,
        name="search_agent",
        system_prompt=search_sys_prompt,
        mcp_config=mcp_config,
        mcp_servers=mcp_servers,
        #sandbox=sand_box,
    )

    # Run agent
    # Runners.sync_run(input="Use tavily-mcp to check what tourist attractions are in Hangzhou", agent=search)
    task = Task(
        # input="Use tavily-mcp to check what tourist attractions are in Hangzhou",
        # input="Use the file_server tool to analyze this audio link: https://amap-aibox-data.oss-cn-zhangjiakou.aliyuncs.com/.mp3",
        # input="Use the amap-amap-sse tool to find hotels within one kilometer of West Lake in Hangzhou",
        input="Use the aworldsearch_server tool to search for the origin of the Dragon Boat Festival",
        # input="Use the picsearch_server tool to search for Captain America",
        # input="Make sure to use the human_confirm tool to let the user confirm this message: 'Do you want to make a payment to this customer'",
        # input="Use the gen_audio_server tool to convert this sentence to audio: 'Nice to meet you'",
        #input="Use the gen_video_server tool to generate a video of this description: 'A cat walking alone on a snowy day'",
        #input="How's the weather in New York, Shanghai, and Beijing right now? These are three cities, I hope the large model returns three tools when it identifies tool calls",
        # input="First call the filewrite_server tool, then call the fileread_server tool",
        # input="Use the playwright tool, with Google browser, search for the latest news about the Trump administration on www.baidu.com",
        # input="Use tavily-mcp",
        agent=search,
        conf=TaskConfig(),
        event_driven=True
    )

    #result = Runners.sync_run_task(task)
    #result = Runners.sync_run_task(task)
    #result = await Runners.streamed_run_task(task)
    # result = await Runners.run_task(task)
    # print(
    #     "----------------------------------------------------------------------------------------------"
    # )
    # print(result)
    # async for chunk in Runners.streamed_run_task(task).stream_events():
    #     print(chunk, end="", flush=True)

    async for output in Runners.streamed_run_task(task).stream_events():
        print(f"Agent Ouput: {output}")
