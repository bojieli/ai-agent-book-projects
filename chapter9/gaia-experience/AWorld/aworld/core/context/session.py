# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import time
import uuid
from typing import List, Optional

from pydantic import BaseModel, Field


class Session(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4().hex))
    last_update_time: float = time.time()
    trajectories: List = []
