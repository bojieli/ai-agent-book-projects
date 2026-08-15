from typing import Any, List, TypeVar, Union, Literal, TypedDict, Dict

DataRow = TypeVar('DataRow')


class BaseCondition(TypedDict):
    field: str
    value: Any
    op: Literal[
        'eq', 'ne', 'gt', 'gte', 'lt', 'lte',
        'in', 'not_in', 'like', 'not_like',
        'is_null', 'is_not_null'
    ]


class LogicalCondition(TypedDict):
    and_: List['QueryCondition']
    or_: List['QueryCondition']


QueryCondition = Union[BaseCondition, LogicalCondition]


class QueryBuilder:
    '''
    Query builder for replay buffer. result example:
    {
        "and": [
            {"field": "field1", "value": "value1", "op": "eq"}, 
            {"or": [{"field": "field2", "value": "value2", "op": "eq"}, {"field": "field3", "value": "value3", "op": "eq"}]}
        ]
    }
    '''

    def __init__(self) -> None:
        self.conditions: List[Dict[str, any]] = []
        self.logical_ops: List[str] = []

    def eq(self, field: str, value: any) -> 'QueryBuilder':
        self.conditions.append({"field": field, "value": value, "op": "eq"})
        return self

    def ne(self, field: str, value: any) -> 'QueryBuilder':
        self.conditions.append({"field": field, "value": value, "op": "ne"})
        return self

    def gt(self, field: str, value: any) -> 'QueryBuilder':
        self.conditions.append({"field": field, "value": value, "op": "gt"})
        return self

    def gte(self, field: str, value: any) -> 'QueryBuilder':
        self.conditions.append({"field": field, "value": value, "op": "gte"})
        return self

    def lt(self, field: str, value: any) -> 'QueryBuilder':
        self.conditions.append({"field": field, "value": value, "op": "lt"})
        return self

    def lte(self, field: str, value: any) -> 'QueryBuilder':
        self.conditions.append({"field": field, "value": value, "op": "lte"})
        return self

    def in_(self, field: str, value: any) -> 'QueryBuilder':
        self.conditions.append({"field": field, "value": value, "op": "in"})
        return self

    def not_in(self, field: str, value: any) -> 'QueryBuilder':
        self.conditions.append(
            {"field": field, "value": value, "op": "not_in"})
        return self

    def like(self, field: str, value: any) -> 'QueryBuilder':
        self.conditions.append({"field": field, "value": value, "op": "like"})
        return self

    def not_like(self, field: str, value: any) -> 'QueryBuilder':
        self.conditions.append(
            {"field": field, "value": value, "op": "not_like"})
        return self

    def is_null(self, field: str) -> 'QueryBuilder':
        self.conditions.append({"field": field, "op": "is_null"})
        return self

    def is_not_null(self, field: str) -> 'QueryBuilder':
        self.conditions.append({"field": field, "op": "is_not_null"})
        return self

    def and_(self) -> 'QueryBuilder':
        self.logical_ops.append("and_")
        return self

    def or_(self) -> 'QueryBuilder':
        self.logical_ops.append("or_")
        return self

    def nested(self, builder: 'QueryBuilder') -> 'QueryBuilder':
        self.conditions.append({"nested": builder.build()})
        return self

    def build(self) -> QueryCondition:
        conditions = self.conditions  # all conditions（including nested）
        operators = self.logical_ops

        # Validate condition and operator counts (n conditions need n-1 operators)
        if len(operators) != len(conditions) - 1:
            raise ValueError("Mismatch between condition and operator counts")

        # Use stack to handle operator precedence (simplified version supporting and/or)
        stack: List[Union[Dict[str, any], str]] = []

        for i, item in enumerate(conditions):
            if i == 0:
                # First element goes directly to stack (condition or nested)
                stack.append(item)
                continue

            # Pop stack top as left operand
            left = stack.pop()
            op = operators[i-1]       # Current operator (and/or)
            right = item              # Right operand (current condition)

            # Build logical expression: {op: [left, right]}
            expr = {op: [left, right]}
            # Push result back to stack for further operations
            stack.append(expr)

        # Process nested conditions (recursive unfolding)
        def process_nested(cond: any) -> any:
            if isinstance(cond, dict):
                if "nested" in cond:
                    # Recursively process sub-conditions
                    return process_nested(cond["nested"])
                # Recursively process child elements
                return {k: process_nested(v) for k, v in cond.items()}
            elif isinstance(cond, list):
                return [process_nested(item) for item in cond]
            return cond

        # Final result: only one element left in stack, return after processing nested
        result = stack[0] if stack else None
        return process_nested(result) if result else None


class QueryFilter:
    '''
    Query filter for replay buffer.
    '''

    def __init__(self, query_condition: QueryCondition) -> None:
        self.query_condition = query_condition

    def _get_field_value(self, row: DataRow, field: str) -> Any:
        '''
        Get field value from row.
        '''
        obj = row
        for part in field.split('.'):
            obj = getattr(obj, part, None)
            if obj is None:
                break
        return obj

    def _do_check(self, row: DataRow, condition: QueryCondition) -> bool:
        """
        check if row match condition
        """
        if condition is None:
            return True
        if "field" in condition and "op" in condition:
            field_val = self._get_field_value(row, condition["field"])
            op = condition["op"]
            target_val = condition["value"]

            if op == "eq":
                return field_val == target_val
            if op == "ne":
                return field_val != target_val
            if op == "gt":
                return field_val > target_val
            if op == "gte":
                return field_val >= target_val
            if op == "lt":
                return field_val < target_val
            if op == "lte":
                return field_val <= target_val
            if op == "in":
                return field_val in target_val
            if op == "not_in":
                return field_val not in target_val
            if op == "like":
                return target_val in field_val
            if op == "not_like":
                return target_val not in field_val
            if op == "is_null":
                return field_val is None
            if op == "is_not_null":
                return field_val is not None

            return False

        elif "and_" in condition or "or_" in condition:
            if "and_" in condition:
                return all(self._do_check(row, c) for c in condition["and_"])
            if "or_" in condition:
                return any(self._do_check(row, c) for c in condition["or_"])
            return False

        return False

    def check_condition(self, row: DataRow) -> bool:
        """
        check if row match condition
        """
        return self._do_check(row, self.query_condition)

    def filter(self, rows: List[DataRow]) -> List[DataRow]:
        """filter rows by condition
        Args:
            rows (List[DataRow]): List of rows to filter.
            query_condition (QueryCondition): Query condition.
        Returns:
            List[DataRow]: List of rows that match the condition.
        """
        condition = self.query_condition
        if not condition:
            return rows
        return [row for row in rows if self.check_condition(row)]
