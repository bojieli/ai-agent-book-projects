# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import abc
import json
import logging
import os
import uuid
from typing import Any, List, Dict, Union

from aworld.agents.llm_agent import Agent
from aworld.config.agent_loader import _load_yaml
from aworld.core.agent.swarm import Swarm
from aworld.runner import Runners
from aworld.logs.util import logger

from verl.experimental.agent_loop.agent_loop import AgentLoopBase, AgentLoopOutput

from train.adapter.verl.common import to_agent_loop_output

logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class AworldAgentLoop(AgentLoopBase):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    async def build_agents(self) -> Union[Agent, Swarm]:
        """Build single- or multi-agent"""

    async def get_llm_server_address(self, server_name: str = None) -> str:
        server = self.server_manager._choose_server(server_name or uuid.uuid4().hex)
        base_url = await server.get_server_address.remote()
        base_url = f"http://{base_url}/v1"
        logger.info(f"get_server_address#base_url: {base_url}")
        return base_url

    async def get_llm_server_model_name(self):
        model_name = "/".join(self.config.actor_rollout_ref.model.path.split("/")[-2:])
        logger.info(f"get_server_model_name#model_name: {model_name}")
        return model_name

    # main branch
    # async def run(self, sampling_params: dict[str, Any], **kwargs) -> AgentLoopOutput:
    #     messages = list(kwargs["raw_prompt"])

    # release 0.5.0
    async def run(self, messages: list, sampling_params: dict[str, Any], **kwargs) -> AgentLoopOutput:
        agent = await self.build_agents()

        self.agent = agent

        result = await self.run_agents(messages[0], agent)
        res = result.trajectory

        # build agent loop output
        output = await self.convert_agent_output(trajectory=res,
                                                 response_length=self.config.actor_rollout_ref.rollout.response_length)
        return output

    async def run_agents(self, input, agent):
        if isinstance(input, dict):
            input = input.get("content", "")
        # collect trajectory
        if isinstance(agent, Swarm):
            result = Runners.sync_run(input=input, swarm=agent)
        else:
            result = Runners.sync_run(input=input, agent=agent)

        return result

    async def get_agent_tool_config(self, config_path: str) -> Dict[str, Any]:
        """Load tool configuration, preferring YAML with simple fields.

            Priority:
            1) agent_tools.yaml (simple user config with url, Authorization, MCP_SERVERS)
            2) mcp.json (legacy full config)
            """

        # 1) Try YAML (simple schema)
        try:
            import yaml  # Local import to avoid hard dependency at import time
            if os.path.exists(config_path):
                src = _load_yaml(config_path)

                url = src.get('url', '')
                authorization = src.get('Authorization', '')
                mcp_servers_value = src.get('MCP_SERVERS', '')

                # Normalize servers to comma-separated string for header and list for internal
                if isinstance(mcp_servers_value, list):
                    mcp_servers_str = ','.join([str(s).strip() for s in mcp_servers_value if str(s).strip()])
                else:
                    mcp_servers_str = str(mcp_servers_value or '').strip()

                # Build internal full mcp_config
                server_name = src.get('server_name', 'aworld-mcp')
                server_type = src.get('type', 'streamable-http')
                timeout = src.get('timeout', 600)
                sse_read_timeout = src.get('sse_read_timeout', 600)
                client_session_timeout_seconds = src.get('client_session_timeout_seconds', 600)

                if url:
                    mcp_config = {
                        "mcpServers": {
                            server_name: {
                                "type": server_type,
                                "url": url,
                                "headers": {
                                    "Authorization": authorization,
                                    "MCP_SERVERS": mcp_servers_str,
                                },
                                "timeout": timeout,
                                "sse_read_timeout": sse_read_timeout,
                                "client_session_timeout_seconds": client_session_timeout_seconds,
                            }
                        }
                    }
                    return mcp_config
        except Exception as err:
            print(f"Error loading YAML tool config err: {err}")

        # 2) Fallback to legacy JSON
        try:
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
        except Exception as err:
            print(f"Error loading tool config[{config_path}] err is : {err}")

    def get_num_turns(self, trajectory: List[Dict[str, Any]]):
        return len(trajectory)

    async def convert_agent_output(self, trajectory: List[Dict[str, Any]], response_length: int) -> AgentLoopOutput:
        """Convert trajectory to AgentLoopOutput.

        Args:
            trajectory (List[Dict[str, Any]]): List of agent execution trajectory.
            response_length (int): Max length of response.

        Returns:
            AgentLoopOutput: agent loop output trajectory used for training.
        """
        if not trajectory:
            raise Exception("Trajectory is empty")

        num_turns = self.get_num_turns(trajectory)
        messages = trajectory[-1].get("exp_data", {}).get("messages", [])
        if not messages:
            return AgentLoopOutput(
                prompt_ids=[],
                response_ids=[],
                response_mask=[],
                num_turns=num_turns,
                metrics={},
            )
        if messages[-1].get("role") != "assistant":
            logger.warning(f"Found last message with role '{messages[-1].get('role')}', but expected 'assistant'. Truncating trailing 'tool' messages.")
            last_non_tool_index = -1
            for i in range(len(messages) - 1, -1, -1):
                if messages[i].get("role") != "tool":
                    last_non_tool_index = i
                    break 
            if last_non_tool_index != -1:
                messages = messages[:last_non_tool_index + 1]
            else:
                messages = []

        output = await to_agent_loop_output(tokenizer=self.tokenizer,
                                            messages=messages,
                                            response_length=response_length,
                                            tools=self.agent.tools)
        return output
