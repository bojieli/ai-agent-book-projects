import time
from aworld.core.common import ActionModel, Observation
from aworld.replay_buffer.base import (
    DataRow,
    DefaultConverter,
    ReplayBuffer,
    ExpMeta,
    Experience,
    RandomTaskSample
)
from aworld.replay_buffer.query_filter import QueryBuilder
from aworld.logs.util import logger


buffer = ReplayBuffer()


def write_data():
    for task_id in range(5):
        for i in range(10):
            task_id = f"task_{task_id}"
            agent_id = f"agent_{i+1}"
            step = i + 1
            execute_time = time.time() + i
            row = DataRow(
                exp_meta=ExpMeta(
                    task_id=task_id,
                    task_name="default_task_name",
                    agent_id=agent_id,
                    step=step,
                    execute_time=execute_time,
                ),
                exp_data=Experience(state=Observation(),
                                    actions=[ActionModel()])
            )
            buffer.store(row)


def read_data():
    query = QueryBuilder().eq("exp_meta.task_id", "task_1").build()
    datas = buffer.sample_task(query_condition=query,
                               sampler=RandomTaskSample(),
                               converter=DefaultConverter(),
                               batch_size=2)
    for data in datas:
        logger.info(f"task_1 data: {data}")

    query = QueryBuilder().eq("exp_meta.agent_id", "agent_5").build()
    datas = buffer.sample_task(query_condition=query,
                               sampler=RandomTaskSample(),
                               converter=DefaultConverter(),
                               batch_size=2)
    for data in datas:
        logger.info(f"agent_5 data: {data}")
