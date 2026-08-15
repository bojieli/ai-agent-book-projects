# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import json
import traceback
from typing import Optional, Dict, Any, Union, List

from pydantic import BaseModel, Field

from aworld.logs.util import logger


class StepInfo(BaseModel):
    """Step information details"""

    # input for agent
    input: Optional[str] = Field(..., description="Step description")
    # parameters for tools
    parameters: Optional[Dict[str, Any]] = Field(..., default_factory=dict, description="Tool or agent parameters")
    # id of tool or agent
    id: str = Field(..., description="Tool or agent ID for execution")


class StepInfos(BaseModel):
    """Defined plan structure, including steps and their sequence."""

    steps: Dict[str, StepInfo] = Field(
        default_factory=dict,
        description="step id with it info"
    )

    dag: List[Union[str, List[str]]] = Field(
        default_factory=list,
        description="dag"
    )


class Plan(BaseModel):
    """Plan structure with step information and final answer"""

    step_infos: StepInfos = Field(
        default_factory=lambda: StepInfos(steps={}, dag=[]),
        description="Step information and execution sequence"
    )
    answer: str = Field(
        default="",
        description="Final answer or result"
    )

    @classmethod
    def parse_raw(cls, json_str: str) -> "Plan":
        """Create from JSON string"""
        try:
            data = json.loads(json_str)
            return Plan.parse_obj(data)
        except Exception as e:
            logger.warning(f"{json_str} Failed to parse Plan and default to origin answer. \n{traceback.format_exc()}")
            return Plan(step_infos=StepInfos(steps={}, dag=[]), answer=json_str)
