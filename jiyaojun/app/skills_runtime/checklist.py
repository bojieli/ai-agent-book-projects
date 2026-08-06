"""SOP checklist 校验 — 对照产物与 references。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_checklist(skill_dir: Path, rel_path: str) -> dict[str, Any]:
    path = skill_dir / rel_path
    if not path.exists():
        raise FileNotFoundError(f"checklist missing: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def validate_checklist(
    checklist: dict[str, Any],
    *,
    artifact: dict[str, Any],
    work_object: dict[str, Any] | None = None,
) -> tuple[bool, list[str]]:
    """按 checklist items 校验产物；返回 (passed, failures)。"""
    failures: list[str] = []
    payload = artifact.get("payload") or {}
    refs = artifact.get("references") or []

    for item in checklist.get("items") or []:
        iid = item.get("id", "")
        when = item.get("when", "")
        if when and "conditional_go" in when and payload.get("go_nogo") != "conditional_go":
            continue

        source = str(item.get("source", ""))
        ok = True
        if "payload.go_nogo" in source:
            ok = payload.get("go_nogo") in {"go", "no_go", "conditional_go"}
        elif "payload.rollback_plan" in source:
            ok = bool(payload.get("rollback_plan")) or bool(artifact.get("unresolved"))
        elif "payload.blast_radius" in source:
            ok = bool(payload.get("blast_radius"))
        elif "references[corpus=continuum]" in source:
            ok = any(r.get("corpus") == "continuum" for r in refs)
        elif "work_object.production_effect" in source:
            eff = (work_object or {}).get("production_effect", "draft_only")
            ok = eff in {"draft_only", "none"}
        elif "continuum_loaded" in iid:
            ok = any(r.get("corpus") == "continuum" for r in refs)
        elif "evidence" in iid:
            ok = bool(artifact.get("source_spans"))
        else:
            ok = True

        if not ok:
            failures.append(f"checklist:{iid}:{item.get('description', '')}")

    passed = not failures
    if checklist.get("all_must_pass") and failures:
        passed = False
    return passed, failures
