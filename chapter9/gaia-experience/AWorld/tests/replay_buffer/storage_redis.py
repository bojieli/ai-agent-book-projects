import time
from aworld.replay_buffer.base import DataRow, ExpMeta, Experience
from aworld.replay_buffer.storage.redis import RedisStorage
from aworld.replay_buffer.query_filter import QueryBuilder
from aworld.core.common import Observation, ActionModel
from aworld.logs.util import logger


def generate_data_row() -> list[DataRow]:
    rows: list[DataRow] = []
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
    return rows


def wriete_data(storage):
    storage.clear()
    rows = generate_data_row()
    storage.add_batch(rows)
    logger.info(f"Add {len(rows)} rows to storage.")


def read_data(storage):
    query_condition = (QueryBuilder()
                       .eq("exp_meta.task_id", "task_1")
                       .and_()
                       .eq("exp_meta.agent_id", "agent_1")
                       .or_()
                       .nested(QueryBuilder()
                               .eq("exp_meta.task_id", "task_4")
                               .and_()
                               .eq("exp_meta.agent_id", "agent_3")
                               .and_()
                               .gt("exp_meta.step", 4)).build())

    rows = storage.get_all(query_condition)
    for row in rows:
        logger.info(row)

    rows = storage.get_paginated(
        page=2, page_size=2, query_condition=query_condition)
    for row in rows:
        logger.info(f"get_paginated: {row}")


# if __name__ == "__main__":
#     storage = RedisStorage(host="localhost", port=6379,
#                            recreate_idx_if_exists=False)
#     wriete_data(storage)
#     read_data(storage)
