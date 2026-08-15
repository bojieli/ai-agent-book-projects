import random
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, TypeVar
from abc import ABC, abstractmethod
from math import ceil

from aworld.core.common import ActionModel, Observation
from aworld.replay_buffer.query_filter import QueryCondition, QueryFilter
from aworld.logs.util import logger
from aworld.utils.serialized_util import to_serializable

T = TypeVar('T')


@dataclass
class Experience:
    '''
    Experience of agent.
    '''
    state: Observation
    actions: List[ActionModel]
    reward_t: float = None
    adv_t: float = None
    v_t: float = None
    messages: List[Dict] = None

    def to_dict(self):
        return {
            "state": to_serializable(self.state),
            "actions": to_serializable(self.actions),
            "reward_t": self.reward_t,
            "adv_t": self.adv_t,
            "v_t": self.v_t,
            "messages": self.messages
        }


@dataclass
class ExpMeta:
    '''
    Experience meta data.
    '''
    task_id: str
    task_name: str
    agent_id: str
    step: int
    execute_time: float
    pre_agent: str

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "agent_id": self.agent_id,
            "step": self.step,
            "execute_time": self.execute_time,
            "pre_agent": self.pre_agent
        }
@dataclass
class DataRow:
    '''
    Data row for storing data.
    '''
    exp_meta: ExpMeta
    exp_data: Experience
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self):
        return {
            "exp_meta": self.exp_meta.to_dict(),
            "exp_data": self.exp_data.to_dict(),
            "id": self.id
        }


class Storage(ABC):
    '''
    Storage for storing and sampling data.
    '''

    @abstractmethod
    def add(self, data: DataRow):
        '''
        Add data to the storage.
        Args:
            data (DataRow): Data to add.
        '''

    @abstractmethod
    def add_batch(self, data_batch: List[DataRow]):
        '''
        Add batch of data to the storage.
        Args:
            data_batch (List[DataRow]): List of data to add.
        '''

    @abstractmethod
    def size(self, query_condition: QueryCondition = None) -> int:
        '''
        Get the size of the storage.
        Returns:
            int: Size of the storage.
        '''

    @abstractmethod
    def get_paginated(self, page: int, page_size: int, query_condition: QueryCondition = None) -> List[DataRow]:
        '''
        Get paginated data from the storage.
        Args:
            page (int): Page number.
            page_size (int): Number of data per page.
        Returns:
            List[DataRow]: List of data.
        '''

    @abstractmethod
    def get_all(self, query_condition: QueryCondition = None) -> List[DataRow]:
        '''
        Get all data from the storage.
        Returns:
            List[DataRow]: List of data.
        '''

    @abstractmethod
    def get_by_task_id(self, task_id: str) -> List[DataRow]:
        '''
        Get data by task_id from the storage.
        Args:
            task_id (str): Task id.
        Returns:
            List[DataRow]: List of data.
        '''

    @abstractmethod
    def get_bacth_by_task_ids(self, task_ids: List[str]) -> Dict[str, List[DataRow]]:
        '''
        Get batch of data by task_ids from the storage.
        Args:
            task_ids (List[str]): List of task ids.
        Returns:
            Dict[str, List[DataRow]]: Dictionary of data.
            The key is the task_id and the value is the list of data.
            The list of data is sorted by step.
        '''


class Sampler(ABC):
    '''
    Sample data from the storage.
    '''

    def sample(self,
               storage: Storage,
               batch_size: int,
               query_condition: QueryCondition = None) -> List[DataRow]:
        '''
        Sample data from the storage.
        Args:
            storage (Storage): Storage to sample from.
            batch_size (int): Number of data to sample.
            query_condition (QueryCondition, optional): Query condition. Defaults to None.
        Returns:
            List[DataRow]
        '''


class TaskSampler(Sampler):
    '''
    Sample task data from storage, returns Dict[str, List[DataRow]] where:
    - key is task_id
    - value is list of task all data rows
    '''

    def sorted_by_step(self, task_experience: List[DataRow]) -> List[DataRow]:
        '''
        Sort the task experience by step and execute_time.
        Args:
            task_experience (List[DataRow]): List of task experience.
        Returns:
            List[DataRow]: List of task experience sorted by step and execute_time.
        '''
        return sorted(task_experience, key=lambda x: (x.exp_meta.step, x.exp_meta.execute_time))

    def sample(self,
               storage: Storage,
               batch_size: int,
               query_condition: QueryCondition = None) -> List[DataRow]:
        task_ids = self.sample_task_ids(storage, batch_size, query_condition)
        return storage.get_bacth_by_task_ids(task_ids)

    def sample_tasks(self,
                     storage: Storage,
                     batch_size: int,
                     query_condition: QueryCondition = None) -> Dict[str, List[DataRow]]:
        '''
        Sample data from the storage.
        Args:
            storage (Storage): Storage to sample from.
            batch_size (int): Number of data to sample.
            query_condition (QueryCondition, optional): Query condition. Defaults to None.
        Returns:
            Dict[str, List[DataRow]]: Dictionary of sampled data.
            The key is the task_id and the value is the list of data.
            The list of data is sorted by step.
        '''
        task_ids = self.sample_task_ids(storage, batch_size, query_condition)
        raws = storage.get_bacth_by_task_ids(task_ids)
        return {task_id: self.sorted_by_step(raws) for task_id, raws in raws.items()}

    @abstractmethod
    def sample_task_ids(self,
                        storage: Storage,
                        batch_size: int,
                        query_condition: QueryCondition = None) -> List[str]:
        '''
        Sample task_ids from the storage.
        Args:
            storage (Storage): Storage to sample from.
            batch_size (int): Number of task_ids to sample.
            query_condition (QueryCondition, optional): Query condition. Defaults to None.
        Returns:
            List[str]: List of task_ids.
        '''


class Converter(ABC):
    '''
    Convert data to dataset row.
    '''

    @abstractmethod
    def to_dataset_row(self, task_experience: List[DataRow]) -> T:
        '''
        Convert task experience to dataset row.
        Args:
            task_experience (List[DataRow]): List of task experience.
        Returns:
            T: type of dataset row.
        '''


class InMemoryStorage(Storage):
    '''
    In-memory storage for storing and sampling data.
    '''

    def __init__(self, max_capacity: int = 10000):
        self._data: Dict[str, List[DataRow]] = {}
        self._max_capacity = max_capacity
        self._fifo_queue = []  # (task_id)

    def add(self, data: DataRow):
        if not data:
            raise ValueError("Data is required")
        if not data.exp_meta:
            raise ValueError("exp_meta is required")

        while self.size() >= self._max_capacity and self._fifo_queue:
            oldest_task_id = self._fifo_queue.pop(0)
            if oldest_task_id in self._data:
                del self._data[oldest_task_id]

        if data.exp_meta.task_id not in self._data:
            self._data[data.exp_meta.task_id] = []
        self._data[data.exp_meta.task_id].append(data)
        self._fifo_queue.append(data.exp_meta.task_id)

        if data.exp_meta.task_id not in self._data:
            self._data[data.exp_meta.task_id] = []
        self._data[data.exp_meta.task_id].append(data)

    def add_batch(self, data_batch: List[DataRow]):
        for data in data_batch:
            self.add(data)

    def size(self, query_condition: QueryCondition = None) -> int:
        return len(self.get_all(query_condition))

    def get_paginated(self, page: int, page_size: int, query_condition: QueryCondition = None) -> List[DataRow]:
        if page < 1:
            raise ValueError("Page must be greater than 0")
        if page_size < 1:
            raise ValueError("Page size must be greater than 0")
        all_data = self.get_all(query_condition)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        return all_data[start_index:end_index]

    def get_all(self, query_condition: QueryCondition = None) -> List[DataRow]:
        all_data = []
        query_filter = None
        if query_condition:
            query_filter = QueryFilter(query_condition)
        for data in self._data.values():
            if query_filter:
                all_data.extend(query_filter.filter(data))
            else:
                all_data.extend(data)
        return all_data

    def get_by_task_id(self, task_id: str) -> List[DataRow]:
        return self._data.get(task_id, [])

    def get_bacth_by_task_ids(self, task_ids: List[str]) -> Dict[str, List[DataRow]]:
        return {task_id: self._data.get(task_id, []) for task_id in task_ids}

    def clear(self):
        self._data = {}
        self._fifo_queue = []


class RandomTaskSample(TaskSampler):
    '''
    Randomly sample data from the storage.
    '''

    def sample_task_ids(self,
                        storage: Storage,
                        batch_size: int,
                        query_condition: QueryCondition = None) -> List[str]:
        total_size = storage.size(query_condition)
        if total_size <= batch_size:
            return storage.get_all(query_condition)

        sampled_task_ids = set()
        page_size = min(100, batch_size * 2)
        total_pages = ceil(total_size/page_size)
        visited_pages = set()
        while len(sampled_task_ids) < batch_size and len(visited_pages) < total_pages:
            page = random.choice(
                [p for p in range(1, total_pages+1) if p not in visited_pages])
            visited_pages.add(page)

            current_page = storage.get_paginated(
                page, page_size, query_condition)
            if not current_page:
                continue
            current_page_task_ids = set(
                [data.exp_meta.task_id for data in current_page if data.exp_meta.task_id not in sampled_task_ids])
            sample_count = min(len(current_page_task_ids),
                               batch_size - len(sampled_task_ids))
            sampled_task_ids.update(random.sample(
                list(current_page_task_ids), sample_count))

        return list(sampled_task_ids)


class DefaultConverter(Converter):
    '''
    Default converter do nothing.
    '''

    def to_dataset_row(self, task_experience: List[DataRow]) -> List[DataRow]:
        return task_experience


class ReplayBuffer:
    '''
    Replay buffer for storing and sampling data.
    '''

    def __init__(
        self,
        storage: Storage = InMemoryStorage()
    ):
        self._storage = storage

    def store(self, data: DataRow):
        '''
        Store data in the replay buffer.
        '''
        if not data:
            raise ValueError("Data is required")
        self._storage.add(data)

    def store_batch(self, data_batch: List[DataRow]):
        '''
        Store batch of data in the replay buffer.
        '''
        if not data_batch:
            logger.warning("Data batch is required")
            return
        self._storage.add_batch(data_batch)

    def sample_task(self,
                    sampler: TaskSampler = RandomTaskSample(),
                    query_condition: QueryCondition = None,
                    converter: Converter = DefaultConverter(),
                    batch_size: int = 1000) -> List[T]:
        '''
        Sample Task from the replay buffer and convert to dataset row.
        DefaultConverter return List[DataRow]
        '''
        sampled_task = sampler.sample_tasks(
            self._storage, batch_size, query_condition)
        return [converter.to_dataset_row(task_experiences) for task_experiences in sampled_task.values()]

    def sample(self,
               sampler: Sampler = RandomTaskSample(),
               query_condition: QueryCondition = None,
               converter: Converter = DefaultConverter(),
               batch_size: int = 1000) -> List[T]:
        '''
        Sample data from the replay buffer and convert to dataset row.
        DefaultConverter return List[DataRow]
        '''
        sampled_data = sampler.sample(
            self._storage, batch_size, query_condition)
        return converter.to_dataset_row(sampled_data)
