import json
from pydantic import parse_obj_as
from typing import Any, List, Dict
from aworld.replay_buffer.base import Storage, DataRow, ExpMeta, Experience
from aworld.replay_buffer.query_filter import QueryCondition, QueryBuilder
from aworld.core.common import Observation, ActionModel
from aworld.logs.util import logger
from aworld.utils.import_package import import_package
import_package("odps")  # noqa
from odps import ODPS  # noqa
from odps.models.record import Record  # noqa


class OdpsSQLBuilder:
    ''' Example:
            query_condition = QueryBuilder().eq("field1", "value1").and_().eq("field2", "value2")
            sql_builder = OdpsSQLBuilder(query_condition)
            sql = sql_builder.build_sql()
            print(sql)  # 输出: "field1 = 'value1' AND field2 = 'value2'"
    '''

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
                return f"{field} = {self._format_value(value)}"
            elif op == "ne":
                return f"{field} != {self._format_value(value)}"
            elif op == "gt":
                return f"{field} > {self._format_value(value)}"
            elif op == "gte":
                return f"{field} >= {self._format_value(value)}"
            elif op == "lt":
                return f"{field} < {self._format_value(value)}"
            elif op == "lte":
                return f"{field} <= {self._format_value(value)}"
            elif op == "in":
                return f"{field} IN ({self._format_value(value)})"
            elif op == "not_in":
                return f"{field} NOT IN ({self._format_value(value)})"
            elif op == "like":
                return f"{field} LIKE '{value}'"
            elif op == "not_like":
                return f"{field} NOT LIKE '{value}'"
            elif op == "is_null":
                return f"{field} IS NULL"
            elif op == "is_not_null":
                return f"{field} IS NOT NULL"

        elif "and_" in condition:
            return f"({' AND '.join(self._build_condition(c) for c in condition['and_'])})"
        elif "or_" in condition:
            return f"({' OR '.join(self._build_condition(c) for c in condition['or_'])})"

        return ""

    def _format_value(self, value: Any) -> str:
        if isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, (list, tuple)):
            return ", ".join(self._format_value(v) for v in value)
        return str(value)

    def build_sql(self) -> str:
        if not self.query_condition:
            return ""
        return self._build_condition(self.query_condition)


class OdpsStorage(Storage):
    '''
        Aliyun ODPS storage.
        Table schema:
            id: int
            task_id: string
            task_name: string
            agent_id: string
            step: int
            execute_time: string
            state: string
            actions: string
            reward_t: string
            adv_t: string
            v_t: string
    '''

    def __init__(self, table_name: str, project: str, endpoint: str, access_id: str, access_key: str, **kwargs):
        self.table_name = table_name
        self.project = project
        self.endpoint = endpoint
        self.access_id = access_id
        self.access_key = access_key
        self.kwargs = kwargs
        self._init_odps()

    def _init_odps(self):
        self.odps = ODPS(self.access_id, self.access_key,
                         self.project, self.endpoint)

    def _get_table(self):
        return self.odps.get_table(self.table_name)

    def _convert_row_to_record(self, row: DataRow) -> Record:
        table = self._get_table()
        record = table.new_record()
        record["id"] = row.id
        record["task_id"] = row.exp_meta.task_id
        record["task_name"] = row.exp_meta.task_name
        record["agent_id"] = row.exp_meta.agent_id
        record["step"] = row.exp_meta.step
        record["execute_time"] = row.exp_meta.execute_time
        if row.exp_data.state:
            record["state"] = row.exp_data.state.model_dump_json()
        if row.exp_data.actions:
            record["actions"] = "[" + ", ".join(action.model_dump_json()
                                                for action in row.exp_data.actions) + "]"
        if row.exp_data.reward_t:
            record["reward_t"] = row.exp_data.reward_t
        if row.exp_data.adv_t:
            record["adv_t"] = row.exp_data.adv_t
        if row.exp_data.v_t:
            record["v_t"] = row.exp_data.v_t
        return record

    def _convert_record_to_row(self, record: Record) -> DataRow:
        return DataRow(
            id=record.id,
            exp_meta=ExpMeta(
                task_id=record['task_id'],
                task_name=record['task_name'],
                agent_id=record['agent_id'],
                step=record['step'],
                execute_time=record['execute_time'],
                pre_agent=record['pre_agent'] if 'pre_agent' in record else None
            ),
            exp_data=Experience(
                state=parse_obj_as(Observation, json.loads(record['state'])),
                actions=[parse_obj_as(ActionModel, item)
                         for item in json.loads(record['actions'])],
                reward_t=record['reward_t'] if 'reward_t' in record else None,
                adv_t=record['adv_t'] if 'adv_t' in record else None,
                v_t=record['v_t'] if 'v_t' in record else None,
            )
        )

    def _build_paginated_sql(self, page: int = None, page_size: int = None):
        if page and page_size:
            offset = (page - 1) * page_size
            limit = page_size
            return f" LIMIT {offset}, {limit}"
        return ""

    def _build_sql(self, query_condition: QueryCondition, page: int = None, page_size: int = None):
        if not query_condition:
            return f"SELECT * FROM {self.table_name}" + self._build_paginated_sql(page, page_size)
        where_builder = OdpsSQLBuilder(query_condition)
        sql = f"SELECT * FROM {self.table_name} WHERE {where_builder.build_sql()}" + self._build_paginated_sql(page,
                                                                                                               page_size)
        return sql

    def _build_count_sql(self, query_condition: QueryCondition):
        if not query_condition:
            return f"SELECT count(1) as count FROM {self.table_name}"
        where_builder = OdpsSQLBuilder(query_condition)
        sql = f"SELECT count(1) as count FROM {self.table_name} WHERE {where_builder.build_sql()}"
        return sql

    def add(self, row: DataRow):
        record = self._convert_row_to_record(row)
        self.odps.write_table(self.table_name, [record])

    def add_batch(self, rows: list[DataRow]):
        records = [self._convert_row_to_record(row) for row in rows]
        self.odps.write_table(self.table_name, records)

    def size(self, query_condition: QueryCondition = None) -> int:
        sql = self._build_count_sql(query_condition)
        with self.odps.execute_sql(sql).open_reader() as reader:
            return reader[0]["count"]

    def get_all(self, query_condition: QueryCondition = None) -> list[DataRow]:
        sql = self._build_sql(query_condition)
        logger.info(f"get_all sql: {sql}")
        with self.odps.execute_sql(sql).open_reader(tunnel=True) as reader:
            rows = []
            for record in reader:
                rows.append(self._convert_record_to_row(record))
            return rows

    def get_paginated(self, page: int, page_size: int, query_condition: QueryCondition = None) -> List[DataRow]:
        sql = self._build_sql(query_condition, page, page_size)
        logger.info(f"get_paginated sql: {sql}")
        with self.odps.execute_sql(sql).open_reader(tunnel=True) as reader:
            rows = []
            for record in reader:
                rows.append(self._convert_record_to_row(record))
            return rows

    def get_by_task_id(self, task_id: str) -> List[DataRow]:
        query_condition = QueryBuilder().eq("task_id", task_id).build()
        return self.get_all(query_condition)

    def get_bacth_by_task_ids(self, task_ids: List[str]) -> Dict[str, List[DataRow]]:
        query_condition = QueryBuilder().in_("task_id", task_ids).build()
        sql = self._build_sql(query_condition)
        logger.info(f"get_bacth_by_task_ids sql: {sql}")
        result = {}
        with self.odps.execute_sql(sql).open_reader(tunnel=True) as reader:
            for record in reader:
                row = self._convert_record_to_row(record)
                if row.exp_meta.task_id not in result:
                    result[row.exp_meta.task_id] = []
                result[row.exp_meta.task_id].append(row)
        return result
