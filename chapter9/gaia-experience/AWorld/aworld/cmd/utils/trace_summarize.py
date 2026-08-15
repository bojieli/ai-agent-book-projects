import os
import logging
import traceback
import asyncio
import re
import json
import pickle
from asyncio.tasks import Task
from aworld.config.conf import AgentConfig
from aworld.agents.llm_agent import Agent
from typing import Dict, Union

from aworld.core.context.base import Context
from aworld.utils.run_util import exec_agent

logger = logging.getLogger(__name__)


class SimpleSummaryCache:
    def __init__(self) -> None:
        self._cache_file = os.path.join(os.curdir, "data", "trace_summary_cache.pkl")
        self._cache: Dict[str, str] = {}
        self._load_cache()

    def _load_cache(self):
        if os.path.exists(self._cache_file):
            try:
                with open(self._cache_file, "rb") as f:
                    self._cache = pickle.load(f)
            except (pickle.PickleError, EOFError):
                logger.warning("Cache file is corrupted, creating new cache")
                if self._cache_file.exists():
                    self._cache_file.unlink()

    def _save_cache(self):
        serializable_cache = {
            k: v for k, v in self._cache.items() if not isinstance(v, Task)
        }
        try:
            with open(self._cache_file, "wb") as f:
                pickle.dump(serializable_cache, f)
        except pickle.PickleError:
            logger.error("Failed to save cache")

    def add_to_cache(self, trace_id: str, value: Union[str, Task]):
        self._cache[trace_id] = value
        if not isinstance(value, Task):
            self._save_cache()

    def get_value(self, trace_id: str) -> Union[str, Task]:
        return self._cache.get(trace_id)

    def trace_exists(self, trace_id: str) -> bool:
        return trace_id in self._cache


# _trace_summary_cache: Dict[str, Union[str, Task]] = {}
_trace_summary_cache = SimpleSummaryCache()

trace_sys_prompt = "You are a helpful tracking summary agent."

trace_prompt = """
    you can use tracking tools to obtain tracking data and then summarize the main tasks completed by each agent and their token usage.
    You can identify which spans are agents, which spans are tool calls, and which spans are large model calls based on the following criteria:
    1 Agent span: the prefix for 'name' is 'event.agent.'
    2 LLM span: The prefix for 'name' is 'llm.'
    3 Tool span: The prefix for 'name' is 'event.tool.'

    requirement:
    1. Please summarize and output separately for agents with different event.id.
    2. Agent Span with the same name but different event.id are also considered as different agents.
    3. There may be a parent-child relationship between agents. Please select the LLM span and Tool span from the nearest child span to the current agent for summarizing.
    4. Ensure that all agent spans have their own independent summaries, and the number of summaries is exactly the same as the number of agent spans. For example: {{"name":"event.agent.a","attributes":{{"event.id":"111"}},"children":[{{"name":"llm.gpt-4o"}},{{"name":"event.tool.1","children":[{{"name":"event.agent.a","attributes":{{"event.id":"222"}},"children":[{{"name":"llm.gpt-4o"}}]}}]}}]}}, both of the above two agent names are event.agent.a, but event.id is different and needs to be summarized separately for 111 and 222. So you need to identify all agent spans without any omissions, which is very important.
    5. Please output in the following standard JSON format without any additional explanatory text:
    [{{"agent":"947cc4c1b7ed406ab7fbf38b9d2b1f5a",,"summary":"xxx"}},{{}}]
    6. Pay attention to controlling the length of the summary, so that the overall output does not exceed your output length limit.
    Here are the trace_id: {task}
    """

agent_config = None


async def _do_summarize_trace(trace_id: str):
    logger.info(f"_do_summarize_trace trace_id: {trace_id}")
    global agent_config
    trace_agent = Agent(
        conf=agent_config,
        name="trace_agent",
        system_prompt=trace_sys_prompt,
        agent_prompt=trace_prompt,
        tool_names=["trace"],
        feedback_tool_result=True,
    )

    if trace_agent.conf.llm_config.llm_api_key is None:
        logger.warning(
            "LLM_API_KEY_TRACE is not set, trace summarize will not be executed."
        )
        return ""
    try:
        res = await exec_agent(trace_id, trace_agent, Context())
        summary = _fetch_json_from_result(res.answer)
        _trace_summary_cache.add_to_cache(trace_id, summary)
        return summary
    except Exception as e:
        logger.error(traceback.format_exc())


def summarize_trace(trace_id: str):
    global agent_config
    if agent_config is None:
        llm_provider = os.getenv("LLM_PROVIDER_TRACE", "openai")
        llm_model_name = os.getenv("LLM_MODEL_NAME_TRACE", None)
        llm_base_url = os.getenv("LLM_BASE_URL_TRACE", None)
        llm_api_key = os.getenv("LLM_API_KEY_TRACE", None)

        if (
            not llm_provider
            or not llm_model_name
            or not llm_base_url
            or not llm_api_key
        ):
            logger.warning(
                "LLM_MODEL_NAME_TRACE, LLM_BASE_URL_TRACE, LLM_API_KEY_TRACE is not set, trace summarize will not be executed."
            )
            return

        agent_config = AgentConfig(
            llm_provider=os.getenv("LLM_PROVIDER_TRACE", "openai"),
            llm_model_name=os.getenv("LLM_MODEL_NAME_TRACE", None),
            llm_base_url=os.getenv("LLM_BASE_URL_TRACE", None),
            llm_api_key=os.getenv("LLM_API_KEY_TRACE", None),
        )
    llm_config = agent_config.llm_config
    if not _trace_summary_cache.trace_exists(trace_id):
        if (
            llm_config.llm_api_key is None
            or not llm_config.llm_base_url
            or not llm_config.llm_model_name
        ):
            logger.warning(
                "LLM_MODEL_NAME_TRACE, LLM_BASE_URL_TRACE, LLM_API_KEY_TRACE is not set, trace summarize will not be executed."
            )
            return

        task = asyncio.create_task(_do_summarize_trace(trace_id))
        _trace_summary_cache.add_to_cache(trace_id, task)


async def get_summarize_trace(trace_id: str):
    if not _trace_summary_cache.trace_exists(trace_id):
        return None
    cached_value = _trace_summary_cache.get_value(trace_id)
    if isinstance(cached_value, Task):
        # try:
        #     result = await cached_value
        #     if isinstance(result, Task):
        #         result = await result
        #     _trace_summary_cache[trace_id] = _fetch_json_from_result(result)
        # except Exception as e:
        #     logger.error(traceback.format_exc())
        return None
    return cached_value


def _fetch_json_from_result(input_str):
    json_match = re.search(r"\[.*\]", input_str, re.DOTALL)
    if json_match:
        json_str = json_match.group(0)
        try:
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError as e:
            logger.warning(f"_fetch_json_from_result json_str: {json_str} error: {e}")
    return ""
