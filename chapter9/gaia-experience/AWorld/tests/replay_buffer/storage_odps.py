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
from aworld.replay_buffer.storage.odps import OdpsStorage


buffer = ReplayBuffer(storage=OdpsStorage(
    table_name="adm_aworld_replay_buffer",
    project="alifin_jtest_dev",
    endpoint="",
    access_id="",
    access_key=""
))


def write_data():
    rows = []
    for id in range(5):
        task_id = f"task_{id+1}"
        for i in range(5):
            agent_id = f"agent_{i+1}"
            for j in range(5):
                step = j + 1
                execute_time = time.time() + j
                row = DataRow(
                    exp_meta=ExpMeta(
                        task_id=task_id,
                        task_name="default_task_name",
                        agent_id=agent_id,
                        step=step,
                        execute_time=execute_time,
                        pre_agent="pre_agent_id"
                    ),
                    exp_data=Experience(state=Observation(),
                                        actions=[ActionModel()])
                )
                rows.append(row)
    buffer.store_batch(rows)


def read_data():
    query = QueryBuilder().eq("exp_meta.task_id", "task_1").build()
    datas = buffer.sample_task(query_condition=query,
                               sampler=RandomTaskSample(),
                               converter=DefaultConverter(),
                               batch_size=1)
    for data in datas:
        logger.info(f"task_1 data: {data}")

    query = QueryBuilder().eq("exp_meta.agent_id", "agent_5").build()
    datas = buffer.sample_task(query_condition=query,
                               sampler=RandomTaskSample(),
                               converter=DefaultConverter(),
                               batch_size=2)
    for data in datas:
        logger.info(f"agent_5 data: {data}")
