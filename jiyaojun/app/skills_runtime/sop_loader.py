"""SOP loader — only for mode=sop; refuse empty shells."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_sop_steps(skill_dir: Path) -> dict[str, Any]:
    path = skill_dir / "sop" / "steps.yaml"
    if not path.exists():
        raise FileNotFoundError(f"sop steps missing: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    steps = data.get("steps") or []
    if not steps:
        raise ValueError(f"empty sop shell forbidden: {path}")
    walls = [s for s in steps if s.get("wall")]
    if not walls:
        raise ValueError(f"sop without validate walls forbidden: {path}")
    return data


def assert_no_sop_for_playbook(skill_dir: Path) -> None:
    if (skill_dir / "sop" / "steps.yaml").exists():
        raise ValueError(f"playbook must not invent sop: {skill_dir}")
