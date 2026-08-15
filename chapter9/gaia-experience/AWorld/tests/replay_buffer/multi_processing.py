import time
import traceback
import multiprocessing
from aworld import replay_buffer
from aworld.core.common import ActionModel, Observation
from aworld.replay_buffer.base import ReplayBuffer, DataRow, ExpMeta, Experience
from aworld.replay_buffer.query_filter import QueryBuilder
from aworld.replay_buffer.storage.multi_proc_mem import MultiProcMemoryStorage
from aworld.logs.util import logger


def write_processing(replay_buffer: ReplayBuffer, task_id: str):
    for i in range(10):
        try:
            data = DataRow(
                exp_meta=ExpMeta(
                    task_id=task_id,
                    task_name=task_id,
                    agent_id=f"agent_{i+1}",
                    step=i,
                    execute_time=time.time()
                ),
                exp_data=Experience(state=Observation(),
                                    actions=[ActionModel()])
            )
            replay_buffer.store(data)
        except Exception as e:
            stack_trace = traceback.format_exc()
            logger.error(
                f"write_processing error: {e}\nStack trace:\n{stack_trace}")
        time.sleep(1)


def read_processing_by_task(replay_buffer: ReplayBuffer, task_id: str):
    while True:
        try:
            query_condition = QueryBuilder().eq("exp_meta.task_id", task_id).build()
            data = replay_buffer.sample_task(
                query_condition=query_condition, batch_size=2)
            logger.info(f"read data of task[{task_id}]: {data}")
        except Exception as e:
            stack_trace = traceback.format_exc()
            logger.error(
                f"read_processing_by_task error: {e}\nStack trace:\n{stack_trace}")
        time.sleep(1)


def read_processing_by_agent(replay_buffer: ReplayBuffer, agent_id: str):
    while True:
        try:
            query_condition = QueryBuilder().eq("exp_meta.agent_id", agent_id).build()
            data = replay_buffer.sample_task(
                query_condition=query_condition, batch_size=2)
            logger.info(f"read data of agent[{agent_id}]: {data}")
        except Exception as e:
            logger.info(f"read_processing_by_agent error: {e}")
        time.sleep(1)


def run():
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn')
    manager = multiprocessing.Manager()

    replay_buffer = ReplayBuffer(storage=MultiProcMemoryStorage(
        data_dict=manager.dict(),
        fifo_queue=manager.list(),
        lock=manager.Lock(),
        max_capacity=10000
    ))

    processes = [
        multiprocessing.Process(target=write_processing,
                                args=(replay_buffer, "task_1",)),
        multiprocessing.Process(target=write_processing,
                                args=(replay_buffer, "task_2",)),
        multiprocessing.Process(target=write_processing,
                                args=(replay_buffer, "task_3",)),
        multiprocessing.Process(target=write_processing,
                                args=(replay_buffer, "task_4",)),
        # multiprocessing.Process(
        #     target=read_processing_by_task, args=(replay_buffer, "task_1",)),
        multiprocessing.Process(
            target=read_processing_by_agent, args=(replay_buffer, "agent_3",))
    ]
    for p in processes:
        p.start()

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        for p in processes:
            p.terminate()
        for p in processes:
            p.join()
    finally:
        logger.info("Processes terminated.")
