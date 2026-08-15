# coding: utf-8
# Copyright (c) 2025 inclusionAI.
from typing import List, Dict

from aworld.config import RunConfig, EngineName, ConfigDict
from aworld.core.agent.swarm import GraphBuildType

from aworld.core.task import Task, TaskResponse, Runner
from aworld.logs.util import logger
from aworld.runners.task_runner import TaskRunner
from aworld.utils.common import new_instance, snake_to_camel


async def choose_runners(tasks: List[Task], agent_oriented: bool = True) -> List[Runner]:
    """Choose the correct runner to run the task.

    Args:
        task: A task that contains agents, tools and datas.

    Returns:
        Runner instance or exception.
    """
    runners = []
    for task in tasks:
        # user custom runner class
        runner_cls = task.runner_cls
        if runner_cls:
            return new_instance(runner_cls, task)
        else:
            # user runner class in the framework
            if task.swarm:
                task.swarm.event_driven = task.event_driven
                execute_type = task.swarm.build_type
            else:
                execute_type = GraphBuildType.WORKFLOW.value

            if task.event_driven:
                runner = new_instance("aworld.runners.event_runner.TaskEventRunner",
                                      task,
                                      agent_oriented=agent_oriented)
            else:
                runner = new_instance(
                    f"aworld.runners.call_driven_runner.{snake_to_camel(execute_type)}Runner",
                    task
                )
        runners.append(runner)
    return runners


async def execute_runner(runners: List[Runner], run_conf: RunConfig) -> Dict[str, TaskResponse]:
    """Execute runner in the runtime engine.

    Args:
        runners: The task processing flow.
        run_conf: Runtime config, can choose the special computing engine to execute the runner.
    """
    if not run_conf:
        run_conf = RunConfig()

    name = run_conf.engine_name
    if run_conf.cls:
        runtime_backend = new_instance(run_conf.cls, run_conf)
    else:
        runtime_backend = new_instance(
            f"aworld.core.runtime_engine.{snake_to_camel(name)}Runtime", run_conf)
    runtime_engine = runtime_backend.build_engine()

    if run_conf.engine_name != EngineName.LOCAL or run_conf.reuse_process == False:
        # distributed in AWorld, the `context` can't carry by response
        for runner in runners:
            if not isinstance(runner, TaskRunner):
                logger.info("not task runner in AWorld, skip...")
                continue
            if runner.task.conf:
                runner.task.conf.resp_carry_context = False
            else:
                runner.task.conf = ConfigDict(resp_carry_context=False)
    return await runtime_engine.execute([runner.run for runner in runners])


def endless_detect(records: List[str], endless_threshold: int, root_agent_name: str):
    """A very simple implementation of endless loop detection.

    Args:
        records: Call sequence of agent.
        endless_threshold: Threshold for the number of repetitions.
        root_agent_name: Name of the entrance agent.
    """
    if not records:
        return False

    threshold = endless_threshold
    last_agent_name = root_agent_name
    count = 1
    for i in range(len(records) - 2, -1, -1):
        if last_agent_name == records[i]:
            count += 1
        else:
            last_agent_name = records[i]
            count = 1

        if count >= threshold:
            logger.warning("detect loop, will exit the loop.")
            return True

    if len(records) > 6:
        last_agent_name = None
        # latest
        for j in range(1, 3):
            for i in range(len(records) - j, 0, -2):
                if last_agent_name and last_agent_name == (records[i], records[i - 1]):
                    count += 1
                elif last_agent_name is None:
                    last_agent_name = (records[i], records[i - 1])
                    count = 1
                else:
                    last_agent_name = None
                    break

                if count >= threshold:
                    logger.warning(f"detect loop: {last_agent_name}, will exit the loop.")
                    return True

    return False
