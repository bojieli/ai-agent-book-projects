#!/usr/bin/env python3
"""Runtime compatibility for legacy action-arena response cleanup.

The pinned upstream prompt asks the model for ``{arena}``, then removes only
the closing brace.  Current models reliably follow that format, leaving an
invalid leading brace at the spatial-memory boundary.  This module wraps only
``generate_action_arena`` and maps its output back to an arena that the
persona can access in the selected sector.
"""

from __future__ import annotations

import datetime as dt
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class ArenaNormalization:
    value: str
    reason: str | None
    fallback: bool


def _strip_response_wrappers(value: Any) -> str:
    """Remove response-only braces, quotes, and surrounding whitespace."""

    return str(value).strip(" \t\r\n{}\"'`")


def normalize_action_arena(
    raw_output: Any,
    accessible_arenas: Iterable[str],
    current_arena: str | None = None,
) -> ArenaNormalization:
    """Return an exact accessible arena, using a bounded deterministic fallback.

    Matching is case-insensitive after removing response wrappers.  Invalid
    output falls back to the current arena when it is among the target
    sector's accessible arenas; otherwise it uses the first arena in the
    upstream spatial-memory order.  The function never invents an arena or
    returns an output outside ``accessible_arenas``.
    """

    allowed = [item.strip() for item in accessible_arenas if item.strip()]
    if not allowed:
        raise RuntimeError("action-arena compatibility has no accessible fallback")

    raw_text = str(raw_output)
    candidate = _strip_response_wrappers(raw_text)
    by_casefold = {item.casefold(): item for item in allowed}
    matched = by_casefold.get(candidate.casefold())
    if matched is not None:
        if raw_text == matched:
            return ArenaNormalization(matched, None, False)
        reason = "case_insensitive_exact_match"
        if candidate == matched:
            reason = "stripped_response_wrappers"
        return ArenaNormalization(matched, reason, False)

    if current_arena:
        current = by_casefold.get(current_arena.strip().casefold())
        if current is not None:
            return ArenaNormalization(
                current, "invalid_output_current_arena_fallback", True
            )
    return ArenaNormalization(
        allowed[0], "invalid_output_first_accessible_fallback", True
    )


class CorrectionRecorder:
    """Crash-resistant append-only writer for credential-free corrections."""

    def __init__(self) -> None:
        self.path: Path | None = None

    def set_path(self, path: Path) -> None:
        self.path = path

    def record(self, row: dict[str, Any]) -> None:
        if self.path is None:
            raise RuntimeError("action-arena correction receipt path is unset")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = (
            json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        descriptor = os.open(
            self.path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600
        )
        try:
            written = os.write(descriptor, payload)
            if written != len(payload):
                raise OSError(
                    f"short action-arena correction write: {written}/{len(payload)}"
                )
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def install() -> CorrectionRecorder:
    """Install the upstream wrapper once and return its mutable recorder."""

    from persona.cognitive_modules import plan

    installed = getattr(plan.generate_action_arena, "_exp10_7_compat", None)
    if installed is not None:
        return installed

    original = plan.generate_action_arena
    recorder = CorrectionRecorder()

    def generate_action_arena(
        act_desp: str,
        persona: Any,
        maze: Any,
        act_world: str,
        act_sector: str,
    ) -> str:
        raw_output = original(act_desp, persona, maze, act_world, act_sector)
        accessible = [
            item.strip()
            for item in persona.s_mem.get_str_accessible_sector_arenas(
                f"{act_world}:{act_sector}"
            ).split(",")
            if item.strip()
        ]
        tile = maze.access_tile(persona.scratch.curr_tile)
        current_arena = None
        if tile.get("world") == act_world and tile.get("sector") == act_sector:
            current_arena = tile.get("arena")
        result = normalize_action_arena(raw_output, accessible, current_arena)
        if result.reason is not None:
            recorder.record(
                {
                    "schema_version": 1,
                    "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "kind": "action_arena_compatibility_correction",
                    "persona": persona.scratch.name,
                    "action_description": act_desp,
                    "world": act_world,
                    "sector": act_sector,
                    "raw_output": str(raw_output),
                    "normalized_output": result.value,
                    "accessible_arenas": accessible,
                    "reason": result.reason,
                    "fallback": result.fallback,
                }
            )
        return result.value

    generate_action_arena._exp10_7_compat = recorder  # type: ignore[attr-defined]
    plan.generate_action_arena = generate_action_arena
    return recorder
