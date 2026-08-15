# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import abc
from typing import TypeVar, Generic

from aworld.core.agent.base import AgentResult
from aworld.core.common import ActionResult
from aworld.models.model_response import ModelResponse

INPUT = TypeVar('INPUT')
OUTPUT = TypeVar('OUTPUT')


class ModelOutputParser(Generic[INPUT, OUTPUT]):
    """Model output parser."""
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    async def parse(self, content: INPUT, **kwargs) -> OUTPUT:
        """Parse the content to the OUTPUT format."""
