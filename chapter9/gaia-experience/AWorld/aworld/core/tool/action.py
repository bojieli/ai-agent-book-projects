# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import abc
from enum import Enum, EnumMeta
from typing import Tuple, Any

from aworld.core.common import ToolActionInfo, ActionModel, ActionResult


class ExecutableAction(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def act(self, action: ActionModel, **kwargs) -> Tuple[ActionResult, Any]:
        """Execute the action."""

    @abc.abstractmethod
    async def async_act(self, action: ActionModel, **kwargs) -> Tuple[ActionResult, Any]:
        """Execute the action."""


class DynamicEnumMeta(EnumMeta):
    def __new__(metacls, cls, bases, classdict):
        for name, value in classdict.items():
            if isinstance(value, tuple) and len(value) == 2:
                classdict[name] = (value[0], value[1])
        return super().__new__(metacls, cls, bases, classdict)


class ToolAction(Enum, metaclass=DynamicEnumMeta):
    @classmethod
    def get_value_by_name(cls, name: str) -> ToolActionInfo | None:
        members = cls.members()
        name = name.upper()
        if name in members:
            if hasattr(members[name], 'value'):
                return members[name].value
            else:
                return members[name]
        return None

    @classmethod
    def members(cls):
        return dict(filter(lambda item: not item[0].startswith("_"), cls.__dict__.items()))


TOOL_ACTION = """
from aworld.core.common import ToolActionInfo, ParamInfo
from aworld.core.tool.action import ToolAction

class {name}Action(ToolAction):
    '''{name} action enum.'''
    {action_name_upper} = ToolActionInfo(name="{action_name}", desc="{desc}", input_params={params})
"""
