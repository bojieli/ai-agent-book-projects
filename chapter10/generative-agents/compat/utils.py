"""Runtime configuration overlay for the pinned Generative Agents source.

The upstream project asks users to put a plaintext API key in its ``utils.py``.
Experiment 10-7 instead imports this overlay ahead of the upstream source and
reads credentials exclusively from the environment.
"""

from __future__ import annotations

import os


openai_api_key = os.environ["DASHSCOPE_API_KEY"]
openai_api_base = os.environ.get(
    "GA_OPENAI_API_BASE",
    "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)
key_owner = "ai-agent-book Experiment 10-7"

maze_assets_loc = os.environ["GA_MAZE_ASSETS_ROOT"]
env_matrix = f"{maze_assets_loc}/the_ville/matrix"
env_visuals = f"{maze_assets_loc}/the_ville/visuals"

fs_storage = os.environ["GA_STORAGE_ROOT"]
fs_temp_storage = os.environ["GA_TEMP_STORAGE_ROOT"]

collision_block_id = "32125"
debug = False

