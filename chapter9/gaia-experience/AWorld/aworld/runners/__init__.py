# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import sys

from aworld.core.factory import Factory
from aworld.logs.util import logger


class HandlerManager(Factory):
    def __init__(self, type_name: str = None):
        super(HandlerManager, self).__init__(type_name)

    def __call__(self, name: str, asyn: bool = False, runner: 'TaskRunner' = None, **kwargs):
        if name is None or runner is None:
            raise ValueError("handler name or runner instance is None")

        try:
            if name in self._cls:
                act = self._cls[name](runner)
            else:
                raise RuntimeError("The handler was not registered.\nPlease confirm the package has been imported.")
        except Exception:
            err = sys.exc_info()
            logger.warning(f"Failed to create handler with name {name}:\n{err[1]}")
            act = None
        return act


HandlerFactory = HandlerManager("hook_type")
