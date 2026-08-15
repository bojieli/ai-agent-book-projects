# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import json
import time
import traceback

import aworld.trace as trace

from typing import List, Dict, Any, Tuple

from aworld.config.conf import ToolConfig
from aworld.core.agent.base import is_agent
from aworld.agents.llm_agent import Agent
from aworld.core.common import Observation, ActionModel, ActionResult
from aworld.core.context.base import Context
from aworld.core.event.base import Message, ToolMessage, AgentMessage
from aworld.core.tool.base import ToolFactory, Tool, AsyncTool
from aworld.core.tool.tool_desc import is_tool_by_name
from aworld.core.task import Task, TaskResponse
from aworld.logs.util import logger, color_log, Color, trace_logger
from aworld.models.model_response import ToolCall
from aworld.output.base import StepOutput, ToolResultOutput
from aworld.runners.task_runner import TaskRunner
from aworld.runners.utils import endless_detect
from aworld.sandbox import Sandbox
from aworld.tools.utils import build_observation
from aworld.utils.common import override_in_subclass
from aworld.utils.serialized_util import NumpyEncoder


def action_result_transform(message: Message, sandbox: Sandbox) -> Tuple[Observation, float, bool, bool, dict]:
    action_results = message.payload
    result: ActionResult = action_results[-1]
    # ignore image, dom_tree attribute, need to process them from action_results in the agent.
    return build_observation(container_id=sandbox.sandbox_id,
                             observer=result.tool_name,
                             ability=result.action_name,
                             content=result.content,
                             action_result=action_results), 1.0, result.is_done, result.is_done, {}


class WorkflowRunner(TaskRunner):
    def __init__(self, task: Task, *args, **kwargs):
        super().__init__(task=task, *args, **kwargs)

    async def do_run(self, context: Context = None) -> TaskResponse:
        self.max_steps = self.conf.get("max_steps", 100)
        resp = await self._do_run(context)
        self._task_response = resp
        return resp

    async def _do_run(self, context: Context = None) -> TaskResponse:
        """Multi-agent sequence general process workflow.

        NOTE: Use the agent's finished state(no tool calls) to control the inner loop.
        Args:
            observation: Observation based on env
            info: Extend info by env
        """
        observation = self.observation
        if not observation:
            raise RuntimeError("no observation, check run process")

        start = time.time()
        msg = None
        response = None

        # Use trace.span to record the entire task execution process
        with trace.span(f"task_execution_{self.task.id}", attributes={
            "task_id": self.task.id,
            "task_name": self.task.name,
            "start_time": start
        }) as task_span:
            try:
                response = await self._common_process(task_span)
            except Exception as err:
                logger.error(f"Runner run failed, err is {traceback.format_exc()}")
            finally:
                if not self.task.is_sub_task:
                    logger.info(f"FINISHED|call_driven_runner|mark_completed|{self.task.id}")
                    await self.outputs.mark_completed()
                color_log(f"task token usage: {self.context.token_usage}",
                          color=Color.pink,
                          logger_=trace_logger)
                for _, tool in self.tools.items():
                    if isinstance(tool, AsyncTool):
                        await tool.close()
                    else:
                        tool.close()
                task_span.set_attributes({
                    "end_time": time.time(),
                    "duration": time.time() - start,
                    "error": msg
                })
                # todo sandbox cleanup
                if self.swarm and hasattr(self.swarm, 'agents') and self.swarm.agents:
                    for agent_name, agent in self.swarm.agents.items():
                        try:
                            if hasattr(agent, 'sandbox') and agent.sandbox:
                                await agent.sandbox.cleanup()
                        except Exception as e:
                            logger.warning(f"call_driven_runner Failed to cleanup sandbox for agent {agent_name}: {e}")
            return response

    async def _common_process(self, task_span):
        start = time.time()
        step = 1
        pre_agent_name = None
        observation = self.observation

        for idx, agent in enumerate(self.swarm.ordered_agents):
            observation.from_agent_name = agent.id()
            observations = [observation]
            policy = None
            cur_agent = agent
            while step <= self.max_steps:
                await self.outputs.add_output(
                    StepOutput.build_start_output(name=f"Step{step}", step_num=step, task_id=self.task.id))

                terminated = False

                observation = self.swarm.action_to_observation(policy, observations)
                observation.from_agent_name = observation.from_agent_name or cur_agent.id()

                if observation.to_agent_name and observation.to_agent_name != cur_agent.id():
                    cur_agent = self.swarm.agents.get(observation.to_agent_name)

                exp_id = self._get_step_span_id(step, cur_agent.id())
                with trace.span(f"step_execution_{exp_id}") as step_span:
                    try:
                        step_span.set_attributes({
                            "exp_id": exp_id,
                            "task_id": self.task.id,
                            "task_name": self.task.name,
                            "trace_id": trace.get_current_span().get_trace_id(),
                            "step": step,
                            "agent_id": cur_agent.id(),
                            "pre_agent": pre_agent_name,
                            "observation": json.dumps(observation.model_dump(exclude_none=True),
                                                      ensure_ascii=False,
                                                      cls=NumpyEncoder)
                        })
                    except:
                        pass
                    pre_agent_name = cur_agent.id()
                    agent_message = AgentMessage(
                        payload=observation,
                        session_id=self.context.session_id,
                        headers={"context": self.context}
                    )

                    if not override_in_subclass('async_policy', cur_agent.__class__, Agent):
                        message = cur_agent.run(agent_message,
                                                step=step,
                                                outputs=self.outputs,
                                                stream=self.conf.get("stream", False),
                                                exp_id=exp_id)
                    else:
                        message = await cur_agent.async_run(agent_message,
                                                            step=step,
                                                            outputs=self.outputs,
                                                            stream=self.conf.get("stream",
                                                                                 False),
                                                            exp_id=exp_id)
                    policy = message.payload
                    step_span.set_attribute("actions",
                                            json.dumps([action.model_dump() for action in policy],
                                                       ensure_ascii=False))
                    observation.content = None
                    color_log(f"{cur_agent.id()} policy: {policy}")
                    if not policy:
                        logger.warning(f"current agent {cur_agent.id()} no policy to use.")
                        await self.outputs.add_output(
                            StepOutput.build_failed_output(name=f"Step{step}",
                                                           step_num=step,
                                                           data=f"current agent {cur_agent.id()} no policy to use.",
                                                           task_id=self.context.task_id)
                        )
                        if not self.task.is_sub_task:
                            await self.outputs.mark_completed()
                        task_span.set_attributes({
                            "end_time": time.time(),
                            "duration": time.time() - start,
                            "status": "failed",
                            "error": f"current agent {cur_agent.id()} no policy to use."
                        })
                        return TaskResponse(msg=f"current agent {cur_agent.id()} no policy to use.",
                                            answer="",
                                            success=False,
                                            id=self.task.id,
                                            time_cost=(time.time() - start),
                                            usage=self.context.token_usage)

                    if is_agent(policy[0]):
                        status, info = await self._agent(agent, observation, policy, step)
                        if status == 'normal':
                            if info:
                                observations.append(observation)
                        elif status == 'break':
                            observation = self.swarm.action_to_observation(policy, observations)
                            if idx == len(self.swarm.ordered_agents) - 1:
                                return TaskResponse(
                                    answer=observation.content,
                                    success=True,
                                    id=self.task.id,
                                    time_cost=(time.time() - start),
                                    usage=self.context.token_usage
                                )
                            break
                        elif status == 'return':
                            await self.outputs.add_output(
                                StepOutput.build_finished_output(name=f"Step{step}",
                                                                 step_num=step,
                                                                 task_id=self.context.task_id)
                            )
                            info.time_cost = (time.time() - start)
                            task_span.set_attributes({
                                "end_time": time.time(),
                                "duration": info.time_cost,
                                "status": "success"
                            })
                            return info
                    elif is_tool_by_name(policy[0].tool_name):
                        # todo sandbox
                        msg, reward, terminated = await self._tool_call(policy, observations, step,
                                                                        cur_agent)
                        step_span.set_attribute("reward", reward)

                    else:
                        logger.warning(f"Unrecognized policy: {policy[0]}")
                        await self.outputs.add_output(
                            StepOutput.build_failed_output(
                                name=f"Step{step}",
                                step_num=step,
                                data=f"Unrecognized policy: {policy[0]}, need to check prompt or agent / tool.",
                                task_id=self.context.task_id
                            )
                        )
                        if not self.task.is_sub_task:
                            logger.info(f"FINISHED|WorkflowRunner|outputs|{self.task.id} {self.task.is_sub_task}")
                            await self.outputs.mark_completed()
                        task_span.set_attributes({
                            "end_time": time.time(),
                            "duration": time.time() - start,
                            "status": "failed",
                            "error": f"Unrecognized policy: {policy[0]}, need to check prompt or agent / tool."
                        })
                        return TaskResponse(
                            msg=f"Unrecognized policy: {policy[0]}, need to check prompt or agent / tool.",
                            answer="",
                            success=False,
                            id=self.task.id,
                            time_cost=(time.time() - start),
                            usage=self.context.token_usage
                        )
                    await self.outputs.add_output(
                        StepOutput.build_finished_output(name=f"Step{step}",
                                                         step_num=step,
                                                         task_id=self.context.task_id)
                    )
                    step += 1
                    if terminated and agent.finished:
                        logger.info(f"{agent.id()} finished")
                        if idx == len(self.swarm.ordered_agents) - 1:
                            return TaskResponse(
                                answer=observations[-1].content,
                                success=True,
                                id=self.task.id,
                                time_cost=(time.time() - start),
                                usage=self.context.token_usage
                            )
                        break

    async def _agent(self, agent: Agent, observation: Observation, policy: List[ActionModel], step: int):
        # only one agent, and get agent from policy
        policy_for_agent = policy[0]
        agent_name = policy_for_agent.tool_name
        if not agent_name:
            agent_name = policy_for_agent.agent_name
        cur_agent: Agent = self.swarm.agents.get(agent_name)
        if not cur_agent:
            raise RuntimeError(f"Can not find {agent_name} agent in swarm.")

        status = "normal"
        if cur_agent.id() == agent.id():
            # Current agent is entrance agent, means need to exit to the outer loop
            logger.info(f"{cur_agent.id()} exit the loop")
            status = "break"
            return status, None

        if agent.handoffs and agent_name not in agent.handoffs:
            # Unable to hand off, exit to the outer loop
            status = "return"
            return status, TaskResponse(msg=f"Can not handoffs {agent_name} agent ",
                                        answer=observation.content,
                                        success=False,
                                        id=self.task.id,
                                        usage=self.context.token_usage)
        # Check if current agent done
        if cur_agent.finished:
            cur_agent._finished = False
            logger.info(f"{cur_agent.id()} agent be be handed off, so finished state reset to False.")

        con = policy_for_agent.policy_info
        if policy_for_agent.params and 'content' in policy_for_agent.params:
            con = policy_for_agent.params['content']
        if observation:
            observation.content = con
        else:
            observation = Observation(content=con)
            return status, observation
        return status, None

    # todo sandbox
    async def _tool_call(self, policy: List[ActionModel], observations: List[Observation], step: int, agent: Agent):
        msg = None
        terminated = False
        # group action by tool name
        tool_mapping = dict()
        reward = 0.0
        # Directly use or use tools after creation.
        for act in policy:
            if not self.tools or (self.tools and act.tool_name not in self.tools):
                # dynamic only use default config in module.
                conf = self.tools_conf.get(act.tool_name)
                tool = ToolFactory(act.tool_name, conf=conf, asyn=conf.use_async if conf else False)
                if isinstance(tool, Tool):
                    tool.reset()
                elif isinstance(tool, AsyncTool):
                    await tool.reset()
                tool_mapping[act.tool_name] = []
                self.tools[act.tool_name] = tool
            if act.tool_name not in tool_mapping:
                tool_mapping[act.tool_name] = []
            tool_mapping[act.tool_name].append(act)

        for tool_name, action in tool_mapping.items():
            tool_message = ToolMessage(
                payload=action,
                session_id=self.context.session_id,
                headers={"context": self.context}
            )
            # Execute action using browser tool and unpack all return values
            if isinstance(self.tools[tool_name], Tool):
                message = self.tools[tool_name].step(tool_message)
            elif isinstance(self.tools[tool_name], AsyncTool):
                # todo sandbox
                message = await self.tools[tool_name].step(tool_message, agent=agent)
            else:
                logger.warning(f"Unsupported tool type: {self.tools[tool_name]}")
                continue

            observation, reward, terminated, _, info = message.payload
            # observation, reward, terminated, _, info = action_result_transform(message, sandbox=None)
            observations.append(observation)
            for i, item in enumerate(action):
                tool_output = ToolResultOutput(
                    tool_type=tool_name,
                    tool_name=item.tool_name,
                    data=observation.content,
                    origin_tool_call=ToolCall.from_dict({
                        "function": {
                            "name": item.action_name,
                            "arguments": item.params,
                        }
                    })
                )
                await self.outputs.add_output(tool_output)

            # Check if there's an exception in info
            if info.get("exception"):
                color_log(f"Step {step} failed with exception: {info['exception']}", color=Color.red)
                msg = f"Step {step} failed with exception: {info['exception']}"
            logger.info(f"step: {step} finished by tool action: {action}.")
            log_ob = Observation(content='' if observation.content is None else observation.content,
                                 action_result=observation.action_result)
            trace_logger.info(f"{tool_name} observation: {log_ob}", color=Color.green)
        return msg, reward, terminated

    def _get_step_span_id(self, step, cur_agent_name):
        key = (step, cur_agent_name)
        if key not in self.step_agent_counter:
            self.step_agent_counter[key] = 0
        else:
            self.step_agent_counter[key] += 1
        exp_index = self.step_agent_counter[key]

        return f"{self.task.id}_{step}_{cur_agent_name}_{exp_index}"


class LoopWorkflowRunner(WorkflowRunner):

    async def _do_run(self, context: Context = None) -> TaskResponse:
        observation = self.observation
        if not observation:
            raise RuntimeError("no observation, check run process")

        start = time.time()
        step = 1
        msg = None

        # Use trace.span to record the entire task execution process
        with trace.span(f"task_execution_{self.task.id}", attributes={
            "task_id": self.task.id,
            "task_name": self.task.name,
            "start_time": start
        }) as task_span:
            try:
                for i in range(self.max_steps):
                    await self._common_process(task_span)
                    step += 1
            except Exception as err:
                logger.error(f"Runner run failed, err is {traceback.format_exc()}")
            finally:
                if not self.task.is_sub_task:
                    logger.info(f"FINISHED|LoopWorkflowRunner|outputs|{self.task.id} {self.task.is_sub_task}")
                    await self.outputs.mark_completed()
                color_log(f"task token usage: {self.context.token_usage}",
                          color=Color.pink,
                          logger_=trace_logger)
                for _, tool in self.tools.items():
                    if isinstance(tool, AsyncTool):
                        await tool.close()
                    else:
                        tool.close()
                task_span.set_attributes({
                    "end_time": time.time(),
                    "duration": time.time() - start,
                    "error": msg
                })
            return TaskResponse(msg=msg,
                                answer=observation.content,
                                success=True if not msg else False,
                                id=self.task.id,
                                time_cost=(time.time() - start),
                                usage=self.context.token_usage)


class HandoffRunner(TaskRunner):
    def __init__(self, task: Task, *args, **kwargs):
        super().__init__(task=task, *args, **kwargs)

    async def do_run(self, context: Context = None) -> TaskResponse:
        resp = await self._do_run(context)
        self._task_response = resp
        return resp

    async def _do_run(self, context: Context = None) -> TaskResponse:
        """Multi-agent general process based on handoff.

        NOTE: Use the agent's finished state to control the loop, so the agent must carefully set finished state.

        Args:
            context: Context of runner.
        """
        start = time.time()

        observation = self.observation
        info = dict()
        step = 0
        max_steps = self.conf.get("max_steps", 100)
        results = []
        swarm_resp = None
        self.loop_detect = []
        # Use trace.span to record the entire task execution process
        with trace.span(f"task_execution_{self.task.id}", attributes={
            "task_id": self.task.id,
            "task_name": self.task.name,
            "start_time": start
        }) as task_span:
            try:
                while step < max_steps:
                    # Loose protocol
                    result_dict = await self._process(observation=observation, info=info)
                    results.append(result_dict)

                    swarm_resp = result_dict.get("response")
                    logger.info(f"Step: {step} response:\n {result_dict}")

                    step += 1
                    if self.swarm.finished or endless_detect(self.loop_detect,
                                                             self.endless_threshold,
                                                             self.swarm.communicate_agent.id()):
                        logger.info("task done!")
                        break

                    if not swarm_resp:
                        logger.warning(f"Step: {step} swarm no valid response")
                        break

                    observation = result_dict.get("observation")
                    if not observation:
                        observation = Observation(content=swarm_resp)
                    else:
                        observation.content = swarm_resp

                time_cost = time.time() - start
                if not results:
                    logger.warning("task no result!")
                    task_span.set_attributes({
                        "status": "failed",
                        "error": f"task no result!"
                    })
                    return TaskResponse(msg=traceback.format_exc(),
                                        answer='',
                                        success=False,
                                        id=self.task.id,
                                        time_cost=time_cost,
                                        usage=self.context.token_usage)

                answer = results[-1].get('observation').content if results[-1].get('observation') else swarm_resp
                return TaskResponse(answer=answer,
                                    success=True,
                                    id=self.task.id,
                                    time_cost=(time.time() - start),
                                    usage=self.context.token_usage)
            except Exception as e:
                logger.error(f"Task execution failed with error: {str(e)}\n{traceback.format_exc()}")
                task_span.set_attributes({
                    "status": "failed",
                    "error": f"Task execution failed with error: {str(e)}\n{traceback.format_exc()}"
                })
                return TaskResponse(msg=traceback.format_exc(),
                                    answer='',
                                    success=False,
                                    id=self.task.id,
                                    time_cost=(time.time() - start),
                                    usage=self.context.token_usage)
            finally:
                color_log(f"task token usage: {self.context.token_usage}",
                          color=Color.pink,
                          logger_=trace_logger)
                for _, tool in self.tools.items():
                    if isinstance(tool, AsyncTool):
                        await tool.close()
                    else:
                        tool.close()
                task_span.set_attributes({
                    "end_time": time.time(),
                    "duration": time.time() - start,
                })

    async def _process(self, observation, info) -> Dict[str, Any]:
        if not self.swarm.initialized:
            raise RuntimeError("swarm needs to use `reset` to init first.")

        start = time.time()
        step = 0
        max_steps = self.conf.get("max_steps", 100)
        self.swarm.cur_agent = self.swarm.communicate_agent
        pre_agent_name = None
        # use communicate agent every time
        agent_message = AgentMessage(
            payload=observation,
            session_id=self.context.session_id,
            headers={"context": self.context}
        )
        if override_in_subclass('async_policy', self.swarm.cur_agent.__class__, Agent):
            message = self.swarm.cur_agent.run(agent_message,
                                               step=step,
                                               outputs=self.outputs,
                                               stream=self.conf.get("stream", False))
        else:
            message = await self.swarm.cur_agent.async_run(agent_message,
                                                           step=step,
                                                           outputs=self.outputs,
                                                           stream=self.conf.get("stream", False))
        self.loop_detect.append(self.swarm.cur_agent.id())
        policy = message.payload
        if not policy:
            logger.warning(f"current agent {self.swarm.cur_agent.id()} no policy to use.")
            exp_id = self._get_step_span_id(step, self.swarm.cur_agent.id())
            with trace.span(f"step_execution_{exp_id}") as step_span:
                step_span.set_attributes({
                    "exp_id": exp_id,
                    "task_id": self.task.id,
                    "task_name": self.task.name,
                    "trace_id": trace.get_current_span().get_trace_id(),
                    "step": step,
                    "agent_id": self.swarm.cur_agent.id(),
                    "pre_agent": pre_agent_name,
                    "observation": json.dumps(observation.model_dump(exclude_none=True),
                                              ensure_ascii=False,
                                              cls=NumpyEncoder),
                    "actions": json.dumps([action.model_dump() for action in policy], ensure_ascii=False)
                })
            return {"msg": f"current agent {self.swarm.cur_agent.id()} no policy to use.",
                    "steps": step,
                    "success": False,
                    "time_cost": (time.time() - start)}
        color_log(f"{self.swarm.cur_agent.id()} policy: {policy}")

        msg = None
        response = None
        return_entry = False
        cur_agent = None
        cur_observation = observation
        finished = False
        try:
            while step < max_steps:
                terminated = False
                exp_id = self._get_step_span_id(step, self.swarm.cur_agent.id())
                with trace.span(f"step_execution_{exp_id}") as step_span:
                    try:
                        step_span.set_attributes({
                            "exp_id": exp_id,
                            "task_id": self.task.id,
                            "task_name": self.task.name,
                            "trace_id": trace.get_current_span().get_trace_id(),
                            "step": step,
                            "agent_id": self.swarm.cur_agent.id(),
                            "pre_agent": pre_agent_name,
                            "observation": json.dumps(cur_observation.model_dump(exclude_none=True),
                                                      ensure_ascii=False,
                                                      cls=NumpyEncoder),
                            "actions": json.dumps([action.model_dump() for action in policy], ensure_ascii=False)
                        })
                    except:
                        pass

                    if is_agent(policy[0]):
                        status, info, ob = await self._social_agent(policy, step)
                        if status == 'normal':
                            self.swarm.cur_agent = self.swarm.agents.get(policy[0].agent_name)
                            policy = info

                        cur_observation = ob
                        # clear observation
                        observation = None
                    elif is_tool_by_name(policy[0].tool_name):
                        status, terminated, info = await self._social_tool_call(policy, step)
                        if status == 'normal':
                            observation = info
                            cur_observation = observation
                    else:
                        logger.warning(f"Unrecognized policy: {policy[0]}")
                        return {"msg": f"Unrecognized policy: {policy[0]}, need to check prompt or agent / tool.",
                                "response": "",
                                "steps": step,
                                "success": False}

                    if status == 'break':
                        return_entry = info
                        break
                    elif status == 'return':
                        return info

                step += 1
                pre_agent_name = self.swarm.cur_agent.id()
                if terminated and self.swarm.cur_agent.finished:
                    logger.info(f"{self.swarm.cur_agent.id()} finished")
                    break

                if observation:
                    if cur_agent is None:
                        cur_agent = self.swarm.cur_agent
                    agent_message = AgentMessage(
                        payload=observation,
                        session_id=self.context.session_id,
                        headers={"context": self.context}
                    )
                    if not override_in_subclass('async_policy', cur_agent.__class__, Agent):
                        message = cur_agent.run(agent_message,
                                                step=step,
                                                outputs=self.outputs,
                                                stream=self.conf.get("stream", False))
                    else:
                        message = await cur_agent.async_run(agent_message,
                                                            step=step,
                                                            outputs=self.outputs,
                                                            stream=self.conf.get("stream", False))
                    policy = message.payload
                    color_log(f"{cur_agent.id()} policy: {policy}")

            if policy:
                response = policy[0].policy_info if policy[0].policy_info else policy[0].action_name

                # All agents or tools have completed their tasks
            if all(agent.finished for _, agent in self.swarm.agents.items()) or (all(
                    tool.finished for _, tool in self.tools.items()) and len(self.swarm.agents) == 1):
                logger.info("entry agent finished, swarm process finished.")
                finished = True

            if return_entry and not finished:
                # Return to the entrance, reset current agent finished state
                self.swarm.cur_agent._finished = False
            return {"steps": step,
                    "response": response,
                    "observation": observation,
                    "msg": msg,
                    "success": True if not msg else False}
        except Exception as e:
            logger.error(f"Task execution failed with error: {str(e)}\n{traceback.format_exc()}")
            return {
                "msg": str(e),
                "response": "",
                "traceback": traceback.format_exc(),
                "steps": step,
                "success": False
            }

    async def _social_agent(self, policy: List[ActionModel], step):
        # only one agent, and get agent from policy
        policy_for_agent = policy[0]
        agent_name = policy_for_agent.tool_name
        if not agent_name:
            agent_name = policy_for_agent.agent_name

        cur_agent: Agent = self.swarm.agents.get(agent_name)
        if not cur_agent:
            raise RuntimeError(f"Can not find {agent_name} agent in swarm.")

        if cur_agent.id() == self.swarm.communicate_agent.id() or cur_agent.id() == self.swarm.cur_agent.id():
            # Current agent is entrance agent, means need to exit to the outer loop
            logger.info(f"{cur_agent.id()} exit to the outer loop")
            return 'break', True, None

        if self.swarm.cur_agent.handoffs and agent_name not in self.swarm.cur_agent.handoffs:
            # Unable to hand off, exit to the outer loop
            return "return", {"msg": f"Can not handoffs {agent_name} agent "
                                     f"by {cur_agent.id()} agent.",
                              "response": policy[0].policy_info if policy else "",
                              "steps": step,
                              "success": False}, None
        # Check if current agent done
        if cur_agent.finished:
            cur_agent._finished = False
            logger.info(f"{cur_agent.id()} agent be be handed off, so finished state reset to False.")

        observation = Observation(content=policy_for_agent.policy_info)
        self.loop_detect.append(cur_agent.id())
        if cur_agent.step_reset:
            cur_agent.reset()

        agent_message = AgentMessage(
            payload=observation,
            session_id=self.context.session_id,
            headers={"context": self.context}
        )

        if not override_in_subclass('async_policy', cur_agent.__class__, Agent):
            message = cur_agent.run(agent_message,
                                    step=step,
                                    outputs=self.outputs,
                                    stream=self.conf.get("stream", False))
        else:
            message = await cur_agent.async_run(agent_message,
                                                step=step,
                                                outputs=self.outputs,
                                                stream=self.conf.get("stream", False))

        agent_policy = message.payload
        if not agent_policy:
            logger.warning(
                f"{observation} can not get the valid policy in {policy_for_agent.agent_name}, exit task!")
            return "return", {"msg": f"{policy_for_agent.agent_name} invalid policy",
                              "response": "",
                              "steps": step,
                              "success": False}, None
        color_log(f"{cur_agent.id()} policy: {agent_policy}")
        return 'normal', agent_policy, observation

    async def _social_tool_call(self, policy: List[ActionModel], step: int):
        observation = None
        terminated = False
        # group action by tool name
        tool_mapping = dict()
        # Directly use or use tools after creation.
        for act in policy:
            if not self.tools or (self.tools and act.tool_name not in self.tools):
                # dynamic only use default config in module.
                conf: ToolConfig = self.tools_conf.get(act.tool_name)
                tool = ToolFactory(act.tool_name, conf=conf, asyn=conf.use_async if conf else False)
                if isinstance(tool, Tool):
                    tool.reset()
                elif isinstance(tool, AsyncTool):
                    await tool.reset()

                tool_mapping[act.tool_name] = []
                self.tools[act.tool_name] = tool
            if act.tool_name not in tool_mapping:
                tool_mapping[act.tool_name] = []
            tool_mapping[act.tool_name].append(act)

        for tool_name, action in tool_mapping.items():
            tool_message = ToolMessage(
                payload=action,
                session_id=self.context.session_id,
                headers={"context": self.context}
            )
            # Execute action using browser tool and unpack all return values
            if isinstance(self.tools[tool_name], Tool):
                message = self.tools[tool_name].step(tool_message)
            elif isinstance(self.tools[tool_name], AsyncTool):
                message = await self.tools[tool_name].step(tool_message)
            else:
                logger.warning(f"Unsupported tool type: {self.tools[tool_name]}")
                continue

            observation, reward, terminated, _, info = message.payload
            for i, item in enumerate(action):
                tool_output = ToolResultOutput(
                    data=observation.content,
                    origin_tool_call=ToolCall.from_dict({
                        "function": {
                            "name": item.action_name,
                            "arguments": item.params,
                        }
                    }),
                    task_id=self.task.id
                )
                await self.outputs.add_output(tool_output)

            # Check if there's an exception in info
            if info.get("exception"):
                color_log(f"Step {step} failed with exception: {info['exception']}", color=Color.red)
            logger.info(f"step: {step} finished by tool action {action}.")
            log_ob = Observation(content='' if observation.content is None else observation.content,
                                 action_result=observation.action_result)
            color_log(f"{tool_name} observation: {log_ob}", color=Color.green)

        # The tool results give itself, exit; give to other agents, continue
        tmp_name = policy[0].agent_name
        if self.swarm.cur_agent.id() == self.swarm.communicate_agent.id() and (
                len(self.swarm.agents) == 1 or tmp_name is None or self.swarm.cur_agent.id() == tmp_name):
            return "break", terminated, True
        elif policy[0].agent_name:
            policy_for_agent = policy[0]
            agent_name = policy_for_agent.agent_name
            if not agent_name:
                agent_name = policy_for_agent.tool_name
            cur_agent: Agent = self.swarm.agents.get(agent_name)
            if not cur_agent:
                raise RuntimeError(f"Can not find {agent_name} agent in swarm.")
            if self.swarm.cur_agent.handoffs and agent_name not in self.swarm.cur_agent.handoffs:
                # Unable to hand off, exit to the outer loop
                return "return", {"msg": f"Can not handoffs {agent_name} agent "
                                         f"by {cur_agent.id()} agent.",
                                  "response": policy[0].policy_info if policy else "",
                                  "steps": step,
                                  "success": False}
            # Check if current agent done
            if cur_agent.finished:
                cur_agent._finished = False
                logger.info(f"{cur_agent.id()} agent be be handed off, so finished state reset to False.")
        return "normal", terminated, observation

    def _get_step_span_id(self, step, cur_agent_name):
        key = (step, cur_agent_name)
        if key not in self.step_agent_counter:
            self.step_agent_counter[key] = 0
        else:
            self.step_agent_counter[key] += 1
        exp_index = self.step_agent_counter[key]

        return f"{self.task.id}_{step}_{cur_agent_name}_{exp_index}"
