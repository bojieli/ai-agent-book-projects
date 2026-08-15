# coding: utf-8
# Copyright (c) 2025 inclusionAI.

from aworld.core.common import ToolActionInfo, ParamInfo
from aworld.core.tool.action import ToolAction


class HumanExecuteAction(ToolAction):
    """Definition of Human execute supported action."""
    HUMAN_CONFIRM = ToolActionInfo(
        name="human_confirm",
        input_params={"confirm_content": ParamInfo(name="confirm_content",
                                                 type="str",
                                                 required=True,
                                                 desc="Content for user confirmation")},
        desc="The main purpose of this tool is to pass given content to the user for confirmation.")
