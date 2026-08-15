import time
from aworld.replay_buffer.base import (
    DataRow,
    DefaultConverter,
    ReplayBuffer,
    ExpMeta,
    Experience,
)
from aworld.core.common import ActionModel, Observation
from aworld.replay_buffer.query_filter import QueryBuilder, QueryFilter
from aworld.logs.util import logger


def filter():
    row = DataRow(
        exp_meta=ExpMeta(
            task_id="task_1",
            task_name="default_task_name",
            agent_id="agent_1",
            step=1,
            execute_time=time.time(),
        ),
        exp_data=Experience(state=Observation(), action=[ActionModel()])
    )

    query = QueryBuilder().eq("exp_meta.task_id", "task_1").build()
    filter1 = QueryFilter(query)
    assert filter1.check_condition(row)

    query = QueryBuilder().eq("exp_meta.task_id", "task_2").build()
    filter2 = QueryFilter(query)
    assert not filter2.check_condition(row)

    query = QueryBuilder().eq("exp_meta.task_id", "task_1").and_().eq(
        "exp_meta.agent_id", "agent_2").build()
    filter3 = QueryFilter(query)
    assert not filter3.check_condition(row)
