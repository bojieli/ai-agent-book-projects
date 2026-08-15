# coding: utf-8
# Copyright (c) 2025 inclusionAI.
from typing import Any, List

from aworld.core.common import ActionResult, Observation

DEFAULT_VIRTUAL_ENV_ID = "env_0"


def build_observation(observer: str,
                      ability: str,
                      container_id: str = None,
                      content: Any = None,
                      dom_tree: Any = None,
                      action_result: List[ActionResult] = [],
                      image: str = '',
                      images: List[str] = [],
                      **kwargs):
    return Observation(container_id=container_id if container_id else DEFAULT_VIRTUAL_ENV_ID,
                       observer=observer,
                       ability=ability,
                       content=content,
                       action_result=action_result,
                       dom_tree=dom_tree,
                       image=image,
                       images=images,
                       info=kwargs)
