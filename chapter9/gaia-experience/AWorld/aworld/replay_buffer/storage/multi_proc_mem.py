import multiprocessing
import traceback
import pickle
from typing import Dict, List
from aworld.replay_buffer.base import Storage, DataRow
from aworld.replay_buffer.query_filter import QueryCondition, QueryFilter
from aworld.logs.util import logger


class MultiProcMemoryStorage(Storage):

    """
    Memory storage for multi-process.
    """

    def __init__(self,
                 data_dict: Dict[str, str],
                 fifo_queue: List[str],
                 lock: multiprocessing.Lock,
                 max_capacity: int = 10000):
        self._data: Dict[str, str] = data_dict
        self._fifo_queue = fifo_queue
        self._max_capacity = max_capacity
        self._lock = lock

    def _save_to_shared_memory(self, data, task_id):
        serialized_data = pickle.dumps(data)
        try:
            if task_id not in self._data or not self._data[task_id]:
                shm = multiprocessing.shared_memory.SharedMemory(
                    create=True, size=len(serialized_data))
                shm.buf[:len(serialized_data)] = serialized_data
                self._data[task_id] = shm.name
                shm.close()
                return
            shm = multiprocessing.shared_memory.SharedMemory(
                name=self._data[task_id], create=False)
            if len(serialized_data) > shm.size:
                shm.close()
                shm.unlink()
                shm = multiprocessing.shared_memory.SharedMemory(
                    create=True, size=len(serialized_data))
                shm.buf[:len(serialized_data)] = serialized_data
                self._data[task_id] = shm.name
            else:
                shm.buf[:len(serialized_data)] = serialized_data
        except FileNotFoundError:
            shm = multiprocessing.shared_memory.SharedMemory(
                create=True, size=len(serialized_data))
            shm.buf[:len(serialized_data)] = serialized_data
            self._data[task_id] = shm.name
        shm.close()

    def _load_from_shared_memory(self, task_id):
        try:
            if task_id not in self._data or not self._data[task_id]:
                return []
            try:
                multiprocessing.shared_memory.SharedMemory(
                    name=self._data[task_id], create=False)
            except FileNotFoundError:
                return []
            shm = multiprocessing.shared_memory.SharedMemory(
                name=self._data[task_id])
            data = pickle.loads(shm.buf.tobytes())
            shm.close()
            return data
        except Exception as e:
            stack_trace = traceback.format_exc()
            logger.error(
                f"_load_from_shared_memory error: {e}\nStack trace:\n{stack_trace}")
            return []

    def _delete_from_shared_memory(self, task_id):
        try:
            if task_id not in self._data or not self._data[task_id]:
                return
            shm = multiprocessing.shared_memory.SharedMemory(
                name=self._data[task_id])
            shm.close()
            shm.unlink()
            del self._data[task_id]
        except FileNotFoundError:
            pass

    def add(self, data: DataRow):
        if not data:
            raise ValueError("Data is required")
        if not data.exp_meta:
            raise ValueError("exp_meta is required")

        with self._lock:
            current_size = sum(len(self._load_from_shared_memory(task_id))
                               for task_id in self._data.keys())
            while current_size >= self._max_capacity and self._fifo_queue:
                oldest_task_id = self._fifo_queue.pop(0)
                if oldest_task_id in self._data.keys():
                    current_size -= len(self._load_from_shared_memory(oldest_task_id))
                    self._delete_from_shared_memory(oldest_task_id)

            task_id = data.exp_meta.task_id
            existing_data = self._load_from_shared_memory(task_id)
            existing_data.append(data)
            self._save_to_shared_memory(existing_data, task_id)
            self._fifo_queue.append(task_id)

    def add_batch(self, data_batch: List[DataRow]):
        with self._lock:
            for data in data_batch:
                self.add(data)

    def size(self, query_condition: QueryCondition = None) -> int:
        with self._lock:
            return len(self._get_all_without_lock(query_condition))

    def get_paginated(self, page: int, page_size: int, query_condition: QueryCondition = None) -> List[DataRow]:
        with self._lock:
            if page < 1:
                raise ValueError("Page must be greater than 0")
            if page_size < 1:
                raise ValueError("Page size must be greater than 0")
            all_data = self._get_all_without_lock(query_condition)
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            return all_data[start_index:end_index]

    def _get_all_without_lock(self, query_condition: QueryCondition = None) -> List[DataRow]:
        all_data = []
        query_filter = None
        if query_condition:
            query_filter = QueryFilter(query_condition)
        for task_id in self._data.keys():
            local_data = self._load_from_shared_memory(task_id)
            if query_filter:
                all_data.extend(query_filter.filter(local_data))
            else:
                all_data.extend(local_data)
        return all_data

    def get_all(self, query_condition: QueryCondition = None) -> List[DataRow]:
        with self._lock:
            return self._get_all_without_lock(query_condition)

    def get_by_task_id(self, task_id: str) -> List[DataRow]:
        with self._lock:
            if task_id in self._data.keys():
                return self._load_from_shared_memory(task_id)

    def get_bacth_by_task_ids(self, task_ids: List[str]) -> Dict[str, List[DataRow]]:
        with self._lock:
            result = {}
            for task_id in task_ids:
                if task_id in self._data.keys():
                    result[task_id] = self._load_from_shared_memory(task_id)
            return result
