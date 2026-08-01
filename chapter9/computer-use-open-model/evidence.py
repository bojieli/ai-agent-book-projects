"""Small, dependency-free helpers for retaining Computer Use evidence."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def retain_step_screenshots(history_data: dict[str, Any], run_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Copy browser-use's temporary screenshots into the retained run.

    The returned history points to paths relative to ``run_dir``. Missing
    screenshots remain explicit records instead of being silently ignored.
    """

    retained = copy.deepcopy(history_data)
    screenshot_dir = run_dir / "screenshots"
    records: list[dict[str, Any]] = []

    for index, item in enumerate(retained.get("history", []), start=1):
        state = item.get("state") or {}
        raw_path = state.get("screenshot_path")
        record: dict[str, Any] = {"step": index, "source_present": False, "path": None, "sha256": None}
        if raw_path:
            source = Path(raw_path).expanduser()
            record["source_present"] = source.is_file()
            if source.is_file():
                screenshot_dir.mkdir(parents=True, exist_ok=True)
                suffix = source.suffix if source.suffix else ".png"
                target = screenshot_dir / f"step-{index:03d}{suffix}"
                shutil.copyfile(source, target)
                relative = target.relative_to(run_dir).as_posix()
                state["screenshot_path"] = relative
                record.update({"path": relative, "sha256": sha256_file(target)})
            else:
                state["screenshot_path"] = None
        records.append(record)

    return retained, records


def write_manifest(run_dir: Path, metadata: dict[str, Any]) -> Path:
    """Hash every retained artifact except the manifest itself."""

    artifacts = []
    for path in sorted(run_dir.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            artifacts.append(
                {
                    "path": path.relative_to(run_dir).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    target = run_dir / "manifest.json"
    write_json(target, {"schema_version": 1, **metadata, "artifacts": artifacts})
    return target
