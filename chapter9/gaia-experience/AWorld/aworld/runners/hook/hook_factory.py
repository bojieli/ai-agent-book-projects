# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import sys
from typing import Dict, List

from aworld.core.factory import Factory
from aworld.logs.util import logger
from aworld.runners.hook.hooks import Hook, StartHook, HookPoint


class HookManager(Factory):
    def __init__(self, type_name: str = None):
        super(HookManager, self).__init__(type_name)

    def __call__(self, name: str, **kwargs):
        if name is None:
            raise ValueError("hook name is None")

        try:
            if name in self._cls:
                act = self._cls[name](**kwargs)
            else:
                raise RuntimeError("The hook was not registered.\nPlease confirm the package has been imported.")
        except Exception:
            err = sys.exc_info()
            logger.warning(f"Failed to create hook with name {name}:\n{err[1]}")
            act = None
        return act

    def hooks(self, name: str = None) -> Dict[str, List[Hook]]:
        vals = list(filter(lambda s: not s.startswith('__'), dir(HookPoint)))
        results = {val.lower(): [] for val in vals}

        for k, v in self._cls.items():
            hook = v()
            if name and hook.point() != name:
               continue

            results.get(hook.point(), []).append(hook)

        return results


HookFactory = HookManager("hook_type")
