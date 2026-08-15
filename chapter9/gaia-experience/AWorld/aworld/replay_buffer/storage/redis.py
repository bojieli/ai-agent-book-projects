import json
from typing import Dict, List
from aworld.replay_buffer.base import Storage, DataRow, ExpMeta, Experience
from aworld.logs.util import logger
from aworld.utils.import_package import import_package
from aworld.replay_buffer.query_filter import QueryCondition, QueryBuilder
from aworld.core.common import Observation, ActionModel
import_package("redis")  # noqa
from redis import Redis  # noqa
from redis.commands.json.path import Path  # noqa
import redis.commands.search.aggregation as aggregations  # noqa
import redis.commands.search.reducers as reducers  # noqa
from redis.commands.search.field import TextField, NumericField, TagField  # noqa
from redis.commands.search.index_definition import IndexDefinition, IndexType  # noqa
from redis.commands.search.query import Query  # noqa
import redis.exceptions  # noqa


class RedisSearchQueryBuilder:
    """
    Build redis search query from query condition
    """

    def __init__(self, query_condition: QueryCondition):
        self.query_condition = query_condition

    def _build_condition(self, condition: QueryCondition) -> str:
        if condition is None:
            return ""

        if "field" in condition and "op" in condition:
            field = condition["field"].split('.')[-1]
            op = condition["op"]
            value = condition.get("value")

            if op == "eq":
                return f"@{field}:{{{value}}}"
            elif op == "ne":
                return f"-@{field}:{{{value}}}"
            elif op == "gt":
                return f"@{field}:[{value} +inf]"
            elif op == "gte":
                return f"@{field}:[{value} +inf]"
            elif op == "lt":
                return f"@{field}:[-inf {value}]"
            elif op == "lte":
                return f"@{field}:[-inf {value}]"
            elif op == "in":
                return f"@{field}:{{{'|'.join(str(v) for v in value)}}}"
            elif op == "not_in":
                return f"-@{field}:{{{'|'.join(str(v) for v in value)}}}"
            elif op == "like":
                return f"@{field}:*{value}*"
            elif op == "not_like":
                return f"-@{field}:*{value}*"
            elif op == "is_null":
                return f"-@{field}:*"
            elif op == "is_not_null":
                return f"@{field}:*"

        elif "and_" in condition:
            conditions = [self._build_condition(c) for c in condition["and_"]]
            return " ".join(conditions)
        elif "or_" in condition:
            conditions = [self._build_condition(c) for c in condition["or_"]]
            return f"({'|'.join(conditions)})"

        return ""

    def build(self) -> Query:
        query_str = self._build_condition(self.query_condition)
        logger.info(f"redis search query: {query_str}")
        return Query(query_str)


class RedisStorage(Storage):
    def __init__(self,
                 host: str = 'localhost',
                 port: int = 6379,
                 db: int = 0,
                 password: str = None,
                 key_prefix: str = 'AWORLD:RB:',
                 index_name: str = 'idx:AWORLD:RB',
                 recreate_idx_if_exists=False):
        self._redis = Redis(host=host, port=port, db=db, password=password)
        self._key_prefix = key_prefix
        self._index_name = index_name
        self._recreate_idx_if_exists = recreate_idx_if_exists
        self._create_index()

    def _create_index(self):
        try:
            existing_indices = self._redis.execute_command('FT._LIST')
            if self._index_name.encode('utf-8') in existing_indices:
                logger.info(f"Index {self._index_name} already exists")
                if self._recreate_idx_if_exists:
                    self._redis.ft(self._index_name).dropindex()
                    logger.info(f"Index {self._index_name} dropped")
                else:
                    return
            self._redis.ft(self._index_name).create_index(
                (
                    TagField("id"),
                    TagField("task_id"),
                    TextField("task_name"),
                    TagField("agent_id"),
                    NumericField("step"),
                    NumericField("execute_time"),
                    TagField("pre_agent")
                ),
                definition=IndexDefinition(
                    prefix=[self._key_prefix], index_type=IndexType.HASH)
            )
        except redis.exceptions.ResponseError as e:
            logger.error(f"Create index {self._index_name} failed. {e}")

    def _get_object_key(self, key: str) -> str:
        return f"{self._key_prefix}{key}"

    def _serialize_to_str(self, value) -> str:
        if str is None:
            return ""
        if isinstance(value, (int, float)):
            return str(value)
        return str(value) if value is not None else ""

    def _serialize(self, data: DataRow) -> Dict[str, str]:
        dict_data = {
            'id': data.id,
            'task_id': data.exp_meta.task_id,
            'task_name': data.exp_meta.task_name,
            'agent_id': data.exp_meta.agent_id,
            'step': data.exp_meta.step,
            'execute_time': data.exp_meta.execute_time,
            'pre_agent': data.exp_meta.pre_agent,
            'state': data.exp_data.state.model_dump_json(),
            'actions': "[" + ", ".join(action.model_dump_json()
                                       for action in data.exp_data.actions) + "]",
            'reward_t': data.exp_data.reward_t,
            'adv_t': data.exp_data.adv_t,
            'v_t': data.exp_data.v_t
        }
        return {k: self._serialize_to_str(v) for k, v in dict_data.items()}

    def _deserialize(self, data: Dict) -> DataRow:
        if not data:
            return None
        return DataRow(
            id=data.get('id'),
            exp_meta=ExpMeta(
                task_id=data.get('task_id'),
                task_name=data.get('task_name'),
                agent_id=data.get('agent_id'),
                step=int(data.get('step', 0)),
                execute_time=float(data.get('execute_time', 0)),
                pre_agent=data.get('pre_agent')
            ),
            exp_data=Experience(
                state=Observation.model_validate_json(data.get('state', '{}')),
                actions=[ActionModel.model_validate_json(json.dumps(action))
                         for action in json.loads(data.get('actions', '[]'))],
                reward_t=float(data.get('reward_t', 0)) if data.get(
                    'reward_t') is not '' else None,
                adv_t=float(data.get('adv_t', 0)) if data.get(
                    'adv_t') is not '' else None,
                v_t=float(data.get('v_t', 0)) if data.get(
                    'v_t') is not '' else None
            )
        )

    def add(self, data: DataRow):
        key = self._get_object_key(data.id)
        self._redis.hset(key, mapping=self._serialize(data))

    def add_batch(self, data_batch: List[DataRow]):
        pipeline = self._redis.pipeline()
        for data in data_batch:
            if not data or not data.exp_meta:
                continue
            key = self._get_object_key(data.id)
            pipeline.hset(key, mapping=self._serialize(data))
        pipeline.execute()

    def search(self, key: str, value: str) -> DataRow:
        result = self._redis.ft(self._index_name).search(
            Query(f"@{key}:{{{value}}}"))
        logger.info(f"Search result: {result}")

    def size(self, query_condition: QueryCondition = None) -> int:
        '''
        Get the size of the storage.
        Returns:
            int: Size of the storage.
        '''
        if not query_condition:
            return self._redis.ft(self._index_name).info()['num_docs']
        query_builder = RedisSearchQueryBuilder(query_condition)
        query = query_builder.build()
        return self._redis.ft(self._index_name).search(query).total

    def get_paginated(self, page: int, page_size: int, query_condition: QueryCondition = None) -> List[DataRow]:
        '''
        Get paginated data from the storage.
        Args:
            page (int): Page number.
            page_size (int): Number of data per page.
        Returns:
            List[DataRow]: List of data.
        '''
        if not query_condition:
            result = self._redis.ft(self._index_name).search(
                Query("*").paging(page, page_size))
        else:
            query_builder = RedisSearchQueryBuilder(query_condition)
            query = query_builder.build().paging(page, page_size)
            result = self._redis.ft(self._index_name).search(query)
        return [self._deserialize(doc.__dict__) for doc in result.docs]

    def get_all(self, query_condition: QueryCondition = None) -> List[DataRow]:
        '''
        Get all data from the storage.
        Returns:
            List[DataRow]: List of data.
        '''
        if not query_condition:
            result = self._redis.ft(self._index_name).search(Query("*"))
        else:
            query_builder = RedisSearchQueryBuilder(query_condition)
            query = query_builder.build()
            result = self._redis.ft(self._index_name).search(query)
        return [self._deserialize(doc.__dict__) for doc in result.docs]

    def get_by_task_id(self, task_id: str) -> List[DataRow]:
        '''
        Get data by task_id from the storage.
        Args:
            task_id (str): Task id.
        Returns:
            List[DataRow]: List of data.
        '''
        query_condition = QueryBuilder().eq("task_id", task_id).build()
        return self.get_all(query_condition)

    def get_bacth_by_task_ids(self, task_ids: List[str]) -> Dict[str, List[DataRow]]:
        '''
        Get data by task_ids from the storage.
        Args:
            task_ids (List[str]): List of task ids.
        Returns:
            Dict[str, List[DataRow]]: Dict of task id and list of data.
        '''
        query_condition = QueryBuilder().in_("task_id", task_ids).build()
        result = self.get_all(query_condition)
        return {task_id: [data for data in result if data.exp_meta.task_id == task_id] for task_id in task_ids}

    def clear(self):
        '''
        Clear the storage.
        '''
        keys = self._redis.keys(f"{self._key_prefix}*")
        if keys:
            self._redis.delete(*keys)
