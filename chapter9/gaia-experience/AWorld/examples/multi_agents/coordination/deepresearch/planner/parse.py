# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import json
import traceback

from aworld.logs.util import logger
from examples.multi_agents.coordination.deepresearch.planner.models import Plan, StepInfos


def parse_step_infos(step_infos: dict) -> StepInfos:
    """Parse step information dictionary into StepInfos object"""
    try:
        return StepInfos.model_validate(step_infos)
    except Exception as e:
        logger.error(f"Error parsing step infos: {traceback.format_exc()}")
        return StepInfos(steps={}, dag=[])


def parse_step_json(step_json: str) -> StepInfos:
    """Parse JSON string into StepInfos object"""
    try:
        data = json.loads(step_json)
    except Exception as e:
        logger.error(f"Failed to parse step JSON: {e}")
        return StepInfos(steps={}, dag=[])
    return parse_step_infos(data)


def parse_plan(plan_text: str) -> Plan:
    """Parse JSON string into Plan object"""
    return Plan.parse_raw(plan_text)
