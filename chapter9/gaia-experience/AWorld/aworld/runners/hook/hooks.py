# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import abc

from aworld.core.context.base import Context
from aworld.core.event.base import Message
from aworld.models.model_response import ModelResponse


class HookPoint:
    START = "start"
    FINISHED = "finished"
    ERROR = "error"
    PRE_LLM_CALL = "pre_llm_call"
    POST_LLM_CALL = "post_llm_call"
    OUTPUT_PROCESS = "output_process"

class Hook:
    """Runner hook."""
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def point(self):
        """Hook point."""

    @abc.abstractmethod
    async def exec(self, message: Message, context: Context = None) -> Message:
        """Execute hook function."""


class StartHook(Hook):
    """Process in the hook point of the start."""
    __metaclass__ = abc.ABCMeta

    def point(self):
        return HookPoint.START


class FinishedHook(Hook):
    """Process in the hook point of the finished."""
    __metaclass__ = abc.ABCMeta

    def point(self):
        return HookPoint.FINISHED


class ErrorHook(Hook):
    """Process in the hook point of the error."""
    __metaclass__ = abc.ABCMeta

    def point(self):
        return HookPoint.ERROR

class PreLLMCallHook(Hook):
    """Process in the hook point of the pre_llm_call."""
    __metaclass__ = abc.ABCMeta

    def point(self):
        return HookPoint.PRE_LLM_CALL
        
class PostLLMCallHook(Hook):
    """Process in the hook point of the post_llm_call."""
    __metaclass__ = abc.ABCMeta

    def point(self):
        return HookPoint.POST_LLM_CALL

class OutputProcessHook(Hook):
    """Output process hook for processing output data for display."""
    __metaclass__ = abc.ABCMeta

    def point(self):
        return HookPoint.OUTPUT_PROCESS

    def process_output_content(self, content: str) -> str:
        """process output content

        Args:
            content: original content

        Returns:
            processed content
        """
        return content

