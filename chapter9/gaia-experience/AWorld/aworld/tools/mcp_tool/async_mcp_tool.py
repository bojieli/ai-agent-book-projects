# coding: utf-8
# Copyright (c) 2025 inclusionAI.

from typing import Any, Dict, Tuple, Union

from aworld.core.context.base import Context

from aworld.config.conf import ToolConfig, ConfigDict
from aworld.core.common import ActionModel, Observation, ActionResult
from aworld.core.tool.base import ToolFactory, AsyncTool
from aworld.logs.util import logger
from aworld.tools.mcp_tool.executor import MCPToolExecutor
from aworld.tools.utils import build_observation


@ToolFactory.register(name="mcp",
                      desc="mcp execute tool",
                      asyn=True)
class McpTool(AsyncTool):
    def __init__(self, conf: Union[Dict[str, Any], ConfigDict, ToolConfig], **kwargs) -> None:
        """Initialize the McpTool.

        Args:
            conf: tool config
        """
        super(McpTool, self).__init__(conf, **kwargs)
        self.action_executor = MCPToolExecutor(self)

    async def reset(self, *, seed: int | None = None, options: Dict[str, str] | None = None) -> Tuple[
            Observation, dict[str, Any]]:
        self._finished = False
        return build_observation(observer=self.name(), ability=""), {}

    async def close(self) -> None:
        self._finished = True
        # default only close playwright
        await self.action_executor.close(self.conf.get('close_servers', ['ms-playwright']))

    async def do_step(self,
                      actions: list[ActionModel],
                      **kwargs) -> Tuple[Observation, float, bool, bool, dict[str, Any]]:
        """Step of tool.

        Args:
            actions: actions
            **kwargs: -
        Returns:
            Observation, float, bool, bool, dict[str, Any]: -
        """
        from aworld.core.agent.base import AgentFactory

        self._finished = False
        reward = 0
        fail_error = ""
        terminated = kwargs.get("terminated", False)
        agent = AgentFactory.agent_instance(actions[0].agent_name)
        if not agent:
            logger.warning(
                f"async_mcp_tool can not get agent,agent_name:{actions[0].agent_name}")
        task_id = self.context.task_id
        session_id = self.context.session_id

        if not actions:
            self._finished = True
            observation = build_observation(observer=self.name(),
                                            content="raw actions is empty",
                                            ability="")
            return (observation,
                    reward,
                    terminated,
                    kwargs.get("truncated", False),
                    {"exception": "actions is empty"})

        mcp_actions = []
        for action in actions:
            tool_name = action.tool_name
            if 'mcp' != tool_name:
                logger.warning(f"Unsupported tool: {tool_name}. {actions}")
                continue
            full_tool_name = action.action_name
            names = full_tool_name.split("__")
            if len(names) < 2:
                logger.warning(f"{full_tool_name} illegal format")
                continue
            action.action_name = names[1]
            action.tool_name = names[0]
            mcp_actions.append(action)

        if not mcp_actions:
            self._finished = True
            action_results = [ActionResult(success=False,
                                           content="something wrong, no mcp tool find",
                                           error="something wrong, no mcp tool find")
                              for _ in actions]
            observation = build_observation(observer=self.name(),
                                            content="no valid mcp actions",
                                            ability=actions[-1].action_name,
                                            action_result=action_results)

            return (observation, reward,
                    terminated,
                    kwargs.get("truncated", False),
                    {"exception": "no valid mcp actions"})

        action_results = None
        try:
            if agent and agent.sandbox:
                sand_box = agent.sandbox
                action_results = await sand_box.mcpservers.call_tool(action_list=mcp_actions, task_id=task_id, session_id=session_id,context=self.context)
            else:
                action_results, ignore = await self.action_executor.async_execute_action(mcp_actions)
            reward = 1
        except Exception as e:
            fail_error = str(e)
        finally:
            self._finished = True

        observation = build_observation(observer=self.name(),
                                        ability=actions[-1].action_name)
        if action_results:
            for res in action_results:
                if res.is_done:
                    terminated = res.is_done
                if res.error:
                    fail_error += res.error

            observation.action_result = action_results
            observation.content = action_results[-1].content
        else:
            if self.conf.get('exit_on_failure'):
                raise Exception(fail_error)
            else:
                logger.warning(
                    f"{actions} no action results, fail info: {fail_error}, will use fail action results")
                # every action need has the result
                action_results = [ActionResult(
                    success=False, content=fail_error, error=fail_error) for _ in actions]
                observation.action_result = action_results
                observation.content = fail_error

        info = {"exception": fail_error, **kwargs}
        return (observation,
                reward,
                terminated,
                kwargs.get("truncated", False),
                info)
