import traceback
from aworld.agents.llm_agent import Agent
from aworld.config.conf import AgentConfig, ConfigDict
from aworld.core.common import Observation, ActionModel
from typing import Dict, Any, List, Union
from aworld.core.tool.base import ToolFactory
from aworld.models.llm import call_llm_model, acall_llm_model
from aworld.trace.config import ObservabilityConfig
from aworld.utils.common import sync_exec
from aworld.logs.util import logger
from aworld.core.agent.swarm import Swarm
from aworld.runner import Runners
from aworld.trace.server import get_trace_server
from aworld.runners.state_manager import RuntimeStateManager, RunNode
import aworld.trace as trace

trace.configure(ObservabilityConfig(trace_server_enabled=True,
                                    metrics_provider="otlp",
                                    metrics_backend="antmonitor",
                                    metrics_base_url="https://antcollector.alipay.com/namespace/aworld/task/aworld/otlp/api/v1/metrics"))


class TraceAgent(Agent):

    def __init__(self,
                 conf: Union[Dict[str, Any], ConfigDict, AgentConfig],
                 name: str,
                 **kwargs):
        super().__init__(conf, name, **kwargs)

    def policy(self, observation: Observation, info: Dict[str, Any] = {}, **kwargs) -> List[ActionModel]:
        """use trace tool to get trace data, and call llm to summary

        Args:
            observation: The state observed from tools in the environment.
            info: Extended information is used to assist the agent to decide a policy.

        Returns:
            ActionModel sequence from agent policy
        """

        self._finished = False
        self.desc_transform()

        tool_name = "trace"
        tool = ToolFactory(tool_name, asyn=False)
        tool.reset()
        tool_params = {}
        action = ActionModel(tool_name=tool_name,
                             action_name="get_trace",
                             agent_name=self.id(),
                             params=tool_params)
        message = tool.step(action)

        observation, _, _, _, _ = message.payload

        llm_response = None

        messages = self.messages_transform(content=observation.content,
                                           sys_prompt=self.system_prompt,
                                           agent_prompt=self.agent_prompt)
        try:
            llm_response = call_llm_model(
                self.llm,
                messages=messages,
                model=self.model_name,
                temperature=self.conf.llm_config.llm_temperature
            )

            logger.info(f"Execute response: {llm_response.message}")
        except Exception as e:
            logger.warn(traceback.format_exc())
            raise e
        finally:
            if llm_response:
                if llm_response.error:
                    logger.info(
                        f"{self.id()} llm result error: {llm_response.error}")
            else:
                logger.error(f"{self.id()} failed to get LLM response")
                raise RuntimeError(
                    f"{self.id()} failed to get LLM response")

        agent_result = sync_exec(self.model_output_parser.parse, llm_response, agent_id=self.id())
        if not agent_result.is_call_tool:
            self._finished = True
        return agent_result.actions

    async def async_policy(self, observation: Observation, info: Dict[str, Any] = {}, **kwargs) -> List[ActionModel]:

        self._finished = False
        self.desc_transform()

        tool_name = "trace"
        tool = ToolFactory(tool_name, asyn=False)
        tool.reset()
        tool_params = {}
        action = ActionModel(tool_name=tool_name,
                             action_name='get_trace',
                             agent_name=self.id(),
                             params=tool_params)
        message = tool.step([action])

        observation, _, _, _, _ = message.payload

        llm_response = None

        messages = self.messages_transform(content=observation.content,
                                           sys_prompt=self.system_prompt,
                                           agent_prompt=self.agent_prompt)
        try:
            llm_response = await acall_llm_model(
                self.llm,
                messages=messages,
                model=self.model_name,
                temperature=self.conf.llm_config.llm_temperature
            )

            logger.info(f"Execute response: {llm_response.message}")
        except Exception as e:
            logger.warn(traceback.format_exc())
            raise e
        finally:
            if llm_response:
                if llm_response.error:
                    logger.info(
                        f"{self.id()} llm result error: {llm_response.error}")
            else:
                logger.error(f"{self.id()} failed to get LLM response")
                raise RuntimeError(
                    f"{self.id()} failed to get LLM response")

        agent_result = await self.model_output_parser.parse(llm_response, agent_id=self.id())
        if not agent_result.is_call_tool:
            self._finished = True
        return agent_result.actions


search_sys_prompt = "You are a helpful search agent."
search_prompt = """
    Please act as a search agent, constructing appropriate keywords and searach terms, using search toolkit to collect relevant information, including urls, webpage snapshots, etc.

    Here are the question: {task}

    pleas only use one action complete this task, at least results 6 pages.
    """

summary_sys_prompt = "You are a helpful general summary agent."

summary_prompt = """
Summarize the following text in one clear and concise paragraph, capturing the key ideas without missing critical points. 
Ensure the summary is easy to understand and avoids excessive detail.

Here are the content: 
{task}
"""

trace_sys_prompt = "You are a helpful trace summary agent."

trace_prompt = """
    Please act as a trace summary agent, Using the provided trace data, summarize the main tasks completed by each agent and their token usage,
    whether the run_type attribute of span is an agent or a large model call: 
        run_type=AGNET and is_event=True represents the agent, 
        run_type=LLM and is_event=False represents the large model call.
        run_type=TOOL and is_event=True represents the tool call.
    The tool call and large model call of agent are manifested as the nearest child span of AGENT Span.
    Please output in the following standard JSON format without any additional explanatory text:
    [{{"agent":"xxx","summary":"xxx","token_usage":"xxx","input_tokens":"xxx","output_tokens":"xxx","use_tools":["xxx"]}}]
    Here are the trace data: {task}
    """


def build_run_flow(nodes: List[RunNode]):
    graph = {}
    start_nodes = []

    for node in nodes:
        if hasattr(node, 'parent_node_id') and node.parent_node_id:
            if node.parent_node_id not in graph:
                graph[node.parent_node_id] = []
            graph[node.parent_node_id].append(node.node_id)
        else:
            start_nodes.append(node.node_id)

    for start in start_nodes:
        print("-----------------------------------")
        _print_tree(graph, start, "", True)
        print("-----------------------------------")


def _print_tree(graph, node_id, prefix, is_last):
    print(prefix + ("└── " if is_last else "├── ") + node_id)
    if node_id in graph:
        children = graph[node_id]
        for i, child in enumerate(children):
            _print_tree(graph, child, prefix +
                        ("    " if is_last else "│   "), i == len(children) - 1)


def run():
    agent_config = AgentConfig(
        llm_provider="openai",
        llm_model_name="DeepSeek-V3-Function-Call",
        llm_temperature=0.3,

        llm_base_url="http://localhost:34567",
        llm_api_key="dummy-key",
    )

    search = Agent(
        conf=agent_config,
        name="search_agent",
        system_prompt=search_sys_prompt,
        agent_prompt=search_prompt,
        tool_names=["search_api"]
    )

    summary = Agent(
        conf=agent_config,
        name="summary_agent",
        system_prompt=summary_sys_prompt,
        agent_prompt=summary_prompt
    )

    trace = TraceAgent(
        conf=agent_config,
        name="trace_agent",
        system_prompt=trace_sys_prompt,
        agent_prompt=trace_prompt
    )

    # default is sequence swarm mode
    swarm = Swarm(search, summary, trace, max_steps=1, event_driven=True)

    prefix = "search baidu:"
    # can special search google, wiki, duck go, or baidu. such as:
    # prefix = "search wiki: "
    try:
        res = Runners.sync_run(
            input=prefix + """What is an agent.""",
            swarm=swarm,
            session_id="123"
        )
        print(res.answer)
    except Exception as e:
        logger.error(traceback.format_exc())

    state_manager = RuntimeStateManager.instance()
    nodes = state_manager.get_nodes("123")
    logger.info(f"session 123 nodes: {nodes}")
    build_run_flow(nodes)
    get_trace_server().join()
