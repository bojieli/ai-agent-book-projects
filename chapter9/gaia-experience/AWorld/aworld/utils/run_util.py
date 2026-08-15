# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import asyncio
import uuid
from typing import Any, List, Dict

from aworld.agents.llm_agent import Agent
from aworld.config import RunConfig
from aworld.core.common import ActionModel, Observation
from aworld.core.context.base import Context
from aworld.core.task import Task, TaskResponse
from aworld.output.outputs import Outputs
from aworld.runners.utils import choose_runners, execute_runner


async def exec_tool(tool_name: str,
                    action_name: str,
                    params: dict,
                    agent_name: str,
                    context: Context,
                    sub_task: bool = False,
                    outputs: Outputs = None,
                    task_group_id: str = None) -> TaskResponse:
    """Utility method for executing a tool in a task-oriented manner.

    Args:
        tool_name: Name of tool, required.
        action_name: Action name of tool, required.
        params: Tool params, required.
        agent_name: Agent name, required, can be empty.
        context: Context in the runtime, required.
        sub_task: Is it a subtask with the main task set to False.
        outputs: The same outputs instance, required in subtask.
        task_group_id: ID of group of task.
    """
    actions = [ActionModel(tool_name=tool_name, action_name=action_name, params=params, agent_name=agent_name)]
    task = Task(input=actions,
                context=context,
                is_sub_task=sub_task,
                group_id=task_group_id,
                session_id=context.session_id)
    if outputs:
        task.outputs = outputs
    runners = await choose_runners([task], agent_oriented=False)
    res = await execute_runner(runners, RunConfig(reuse_process=True))
    resp: TaskResponse = res.get(task.id)
    return resp


async def exec_agent(question: Any,
                     agent: Agent,
                     context: Context,
                     sub_task: bool = False,
                     outputs: Outputs = None,
                     task_group_id: str = None) -> TaskResponse:
    """Utility method for executing an agent in a task-oriented manner.

    Args:
        question: Problems handled by agents.
        agent: Defined intelligent agents that solve specific problems.
        context: Context in the runtime.
        sub_task: Is it a subtask with the main task set to False.
        outputs: The same outputs instance.
        task_group_id: ID of group of task.
    """
    task_id = uuid.uuid1().hex
    # sub_task_context = await context.build_sub_context(question, task_id, agents = {agent.id(): agent})
    # logger.info(f"{context.task_id} build sub_task: {task_id}, sub_task_context: {sub_task_context}")
    task = Task(id=task_id,
                input=question,
                agent=agent,
                context=context,
                is_sub_task=sub_task,
                group_id=task_group_id,
                session_id=context.session_id)
    if outputs:
        task.outputs = outputs
    runners = await choose_runners([task])
    res = await execute_runner(runners, RunConfig(reuse_process=True))
    resp: TaskResponse = res.get(task.id)
    return resp


async def exec_agents(questions: List[Any],
                      agents: List[Agent],
                      context: Context,
                      sub_task: bool = False,
                      task_group_id: str = None) -> List[ActionModel]:
    """Execute the agent list with the questions, using asyncio.

    Args:
        questions: Problems handled by agents.
        agents: Defined intelligent agents that solve specific problem.
        context: Context in the runtime.
        sub_task: Is it a subtask with the main task set to False.
        task_group_id: ID of group of task.
    """
    tasks = []
    if agents:
        for idx, agent in enumerate(agents):
            tasks.append(asyncio.create_task(
                exec_agent(questions[idx], agent, context, sub_task=sub_task, task_group_id=task_group_id)))

    results = await asyncio.gather(*tasks)
    res = []
    for idx, result in enumerate(results):
        if result.success:
            con = result.answer
        else:
            con = result.msg
        res.append(ActionModel(agent_name=agents[idx].id(), policy_info=con))
    return res


async def exec_process_agents(question: Any,
                              agents: List[Agent],
                              context: Context,
                              sub_task: bool = False,
                              task_group_id: str = None):
    """Execute the agent list with the same question, using new process.

    NOTE: Mixing coroutines and processes may lead to unknown issues.

    Args:
        question: Problems handled by agents.
        agents: Defined intelligent agents that solve specific problem.
        context: Context in the runtime.
        sub_task: Is it a subtask with the main task set to False.
        task_group_id: ID of group of task.
    """
    tasks = []
    agent_map = {}
    if agents:
        for agent in agents:
            task = Task(input=question, agent=agent, context=context, is_sub_task=sub_task, group_id=task_group_id)
            agent_map[task.id] = agent.id()
            tasks.append(task)

    if not tasks:
        raise RuntimeError("no task need to run.")

    runners = await choose_runners(tasks)
    results = await execute_runner(runners, RunConfig(reuse_process=True))

    res = []
    for key, result in results.items():
        res.append(ActionModel(agent_name=agent_map[key], policy_info=result))
    return res


async def exec_tasks(tasks: List[Task], run_conf: RunConfig = RunConfig()) -> Dict[str, TaskResponse]:
    final_tasks = []
    # task list sequence-dependent execution
    if run_conf and run_conf.sequence_dependent:
        return await serial_exec_tasks(tasks=tasks, run_conf=run_conf)

    for task in tasks:
        if not task.group_id:
            task.group_id = uuid.uuid4().hex
        final_tasks.append(task)
    runners = await choose_runners(final_tasks)
    return await execute_runner(runners, run_conf)


async def serial_exec_tasks(tasks: List[Task], run_conf: RunConfig = RunConfig()) -> Dict[str, TaskResponse]:
    res = {}
    task_input = tasks[0].input
    for task in tasks:
        task.input = task_input
        runners = await choose_runners([task])
        res = await execute_runner(runners, run_conf)
        result: TaskResponse = res.get(task.id)
        if result.success:
            task_input = result.answer
        else:
            task_input = result.msg
    return res
