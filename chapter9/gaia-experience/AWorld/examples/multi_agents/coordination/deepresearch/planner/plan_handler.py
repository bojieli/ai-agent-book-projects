# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import asyncio
import uuid
from typing import AsyncGenerator

from aworld.core.common import ActionModel, Observation, TaskItem
from aworld.core.event.base import AgentMessage, Constants, TopicType, Message
from aworld.core.exceptions import AWorldRuntimeException
from aworld.logs.util import logger
from aworld.output.base import StepOutput
from aworld.runners import HandlerFactory
from aworld.runners.handler.agent import AgentHandler
from aworld.utils.run_util import exec_agent, exec_tool
from examples.multi_agents.coordination.deepresearch.planner.models import StepInfo
from examples.multi_agents.coordination.deepresearch.planner.parse import parse_plan


@HandlerFactory.register(name=f'__{Constants.PLAN}__')
class PlanHandler(AgentHandler):
    def is_valid_message(self, message: Message):
        if message.category != Constants.PLAN:
            return False
        return True

    async def handle(self, message: Message) -> AsyncGenerator[Message, None]:
        if not self.is_valid_message(message):
            return

        logger.info(f"PlanHandler|handle|taskid={self.task_id}|is_sub_task={message.context._task.is_sub_task}")
        content = message.payload
        # data is List[ActionModel]
        for action in content:
            if not isinstance(action, ActionModel):
                # error message, p2p
                yield Message(
                    category=Constants.OUTPUT,
                    payload=StepOutput.build_failed_output(name=f"{message.caller or self.name()}",
                                                           step_num=0,
                                                           data="action not a ActionModel.",
                                                           task_id=self.task_id),
                    sender=self.name(),
                    session_id=message.session_id,
                    headers=message.headers
                )
                msg = Message(
                    category=Constants.TASK,
                    payload=TaskItem(msg="action not a ActionModel.", data=content, stop=True),
                    sender=self.name(),
                    session_id=message.session_id,
                    topic=TopicType.ERROR,
                    headers=message.headers
                )
                logger.info(f"agent handler send task message: {msg}")
                yield msg
                return

        logger.info(f"PlanHandler|content|{content}")
        plan = parse_plan(content[0].policy_info)
        logger.info(f"PlanHandler|plan|{plan}")
        step_infos = plan.step_infos
        steps = step_infos.steps
        dag = step_infos.dag
        if not steps or not dag:
            if plan.answer:
                logger.info(f"FINISHED|PlanHandler|plan|finished|{plan.answer}")
                yield Message(
                    category=Constants.TASK,
                    payload=plan.answer,
                    sender=self.name(),
                    session_id=message.session_id,
                    topic=TopicType.FINISHED,
                    headers=message.headers
                )
            else:
                raise AWorldRuntimeException("no steps and answer.")

        group_id = self.runner.task.group_id if self.runner.task.group_id else uuid.uuid4().hex
        self.runner.task.group_id = group_id
        merge_context = message.context
        for node in dag:
            if isinstance(node, list):
                logger.info(f"PlanHandler|parallel_node|start|{node}")
                # can parallel
                tasks = []

                for n in node:
                    new_context = merge_context.deep_copy()
                    step_info: StepInfo = steps.get(n)
                    agent = self.swarm.agents.get(step_info.id)
                    if agent:
                        tasks.append(exec_agent(step_info.input, agent, new_context,
                                                outputs=merge_context.outputs,
                                                sub_task=True,
                                                task_group_id=group_id))
                    else:
                        names = step_info.id.split("__")
                        action_name = '__'.join(names[1:]) if len(names) > 1 else ''
                        tasks.append(exec_tool(tool_name=names[0],
                                               action_name=action_name,
                                               params=step_info.parameters,
                                               agent_name=message.sender,
                                               context=new_context,
                                               sub_task=True,
                                               outputs=merge_context.outputs,
                                               task_group_id=group_id))

                res = await asyncio.gather(*tasks)
                for idx, t in enumerate(res):
                    merge_context.merge_context(t.context)
                    merge_context.save_action_trajectory(steps.get(node[idx]).id, t.answer)
                logger.info(f"PlanHandler|parallel_node|end|{res}")
            else:
                logger.info(f"PlanHandler|single_node|start|{node}")
                step_info: StepInfo = steps.get(node)
                agent = self.swarm.agents.get(step_info.id)
                new_context = merge_context.deep_copy()
                if agent:
                    res = await exec_agent(step_info.input, agent, new_context, outputs=merge_context.outputs,
                                           sub_task=True, task_group_id=group_id)
                else:
                    names = step_info.id.split("__")
                    action_name = '__'.join(names[1:]) if len(names) > 1 else ''
                    res = await exec_tool(tool_name=step_info.id,
                                          action_name=action_name,
                                          params=step_info.parameters,
                                          agent_name=message.sender,
                                          context=new_context,
                                          outputs=merge_context.outputs,
                                          sub_task=True,
                                          task_group_id=group_id)
                merge_context.merge_context(res.context)
                merge_context.save_action_trajectory(step_info.id, res.answer, agent_name=agent.id())
                logger.info(f"PlanHandler|single_node|end|{res}")
        new_plan_input = Observation(content=merge_context.task_input)
        yield AgentMessage(session_id=message.session_id,
                           payload=new_plan_input,
                           sender=self.name(),
                           receiver=self.swarm.communicate_agent.id(),
                           headers={'context': merge_context})
