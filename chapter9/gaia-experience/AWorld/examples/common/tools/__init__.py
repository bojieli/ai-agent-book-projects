# coding: utf-8
# Copyright (c) 2025 inclusionAI.

from aworld.core.tool.base import Tool, AsyncTool
from aworld.core.tool.action import ExecutableAction
from aworld.utils.common import scan_packages

scan_packages("examples.common.tools", [Tool, AsyncTool, ExecutableAction])
from examples.common.tools.browsers.action.actions import *