# coding: utf-8
# Copyright (c) 2025 inclusionAI.

import logging
import sys
from typing import Dict, List

from aworld.core.factory import Factory
from aworld.logs.util import logger


class ActionManager(Factory):
    def __init__(self, type_name: str = None):
        super(ActionManager, self).__init__(type_name)
        self._tool_action_mapping: Dict[str, str] = {}
        self._tool_action_cache: Dict[str, List[str]] = {}

    def __call__(self, name: str, tool_name: str = None, **kwargs):
        if name is None:
            raise ValueError("action name is None")
        if tool_name is None:
            tool_name = ""

        final_name = tool_name + name
        try:
            if final_name in self._cls:
                act = self._cls[final_name](**kwargs)
            else:
                raise RuntimeError("The action was not registered.\nPlease confirm the package has been imported.")
        except Exception:
            err = sys.exc_info()
            logging.warning("Failed to create action with name '%s':\n%s" % (name, err[1]), exc_info=err)
            act = None

        if act is None:
            act = UnknownAction(name=name, **kwargs)
            act.name = name
        return act

    def register(self, name: str, desc: str, **kwargs):
        def func(cls):
            tool_name = kwargs.get("tool_name")
            if not tool_name:
                logger.warning("tool name is empty")
                tool_name = ""
            if name in self._cls and self._tool_action_mapping.get(name) == tool_name:
                logger.warning(f"{tool_name} tool {name} action already in {self._type} factory, will override it.")

            self._tool_action_mapping[name] = tool_name
            final_name = tool_name + name
            self._cls[final_name] = cls
            self._desc[final_name] = desc
            self._ext_info[final_name] = kwargs
            return cls

        return func

    def get_actions_by_tool(self, tool_name: str):
        if tool_name in self._tool_action_cache:
            return self._tool_action_cache[tool_name]

        actions = []
        for action_name, v in self._tool_action_mapping.items():
            if tool_name == v:
                actions.append(action_name)
        self._tool_action_cache[tool_name] = actions
        return actions


ActionFactory = ActionManager("action_type")


class UnknownAction(object):
    def __init__(self, name: str, *args, **kwargs):
        self.options = {}
        self._args = args
        self._kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, t, v, traceback):
        pass

    def act(self, *args, **kwds):
        """Perform optimization and return an SolverResults object."""
        self._solver_error('act')

    async def async_act(self, *args, **kwds):
        self._solver_error('async_act')

    def reset(self):
        """Reset the state of an optimizer"""
        self._solver_error('reset')

    def set_options(self, istr):
        """Set the options in the optimizer from a string."""
        self._solver_error('set_options')

    def __bool__(self):
        return self.available()

    def __getattr__(self, attr):
        self._solver_error(attr)

    def _action_error(self, method_name):
        raise RuntimeError(
            f"""Attempting to use an unavailable action. The ActionFactory was unable to create the 
action "{self.type}" and returned an UnknownAction object. This error is raised at the point where 
the UnknownAction object was used as if it were valid (by calling method "{method_name}").""")
