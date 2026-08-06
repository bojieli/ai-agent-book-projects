"""ArtifactAgent — Map-Reduce over transcript slots (no Flask second brain)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SlotFill:
    action_items: list[dict[str, Any]]
    open_questions: list[str]
    notes: list[str]


class ArtifactAgent:
    """Map: per-segment extract; Reduce: merge dedupe into envelope payload."""

    def map_segment(self, text: str, idx: int) -> dict[str, Any]:
        items: list[dict[str, Any]] = []
        questions: list[str] = []
        notes: list[str] = []
        if any(k in text for k in ("补", "跟进", "负责", "截止")):
            items.append(
                {
                    "title": text.strip()[:80],
                    "owner": "u_dev_a" if "你" in text or "研发" in text else "u_pm",
                    "status": "committed",
                }
            )
        if "？" in text or "?" in text or "是否" in text:
            questions.append(text.strip())
        if "决议" in text or "同意" in text:
            notes.append(text.strip())
        return {"idx": idx, "items": items, "questions": questions, "notes": notes}

    def reduce(self, mapped: list[dict[str, Any]]) -> SlotFill:
        items: list[dict[str, Any]] = []
        questions: list[str] = []
        notes: list[str] = []
        seen = set()
        for m in mapped:
            for it in m["items"]:
                key = it["title"]
                if key not in seen:
                    seen.add(key)
                    items.append(it)
            questions.extend(m["questions"])
            notes.extend(m["notes"])
        return SlotFill(action_items=items, open_questions=questions, notes=notes)

    def build_action_items_envelope(
        self,
        *,
        meeting_id: str,
        org_domains: list[str],
        scenario_type: str,
        skill_pack_id: str,
        segments: list[str],
        classification: str = "internal",
        continuum_write_class: str = "wide",
        references: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        mapped = [self.map_segment(s, i) for i, s in enumerate(segments)]
        filled = self.reduce(mapped)
        if not filled.action_items:
            filled.action_items.append(
                {
                    "title": "（未抽出明确行动项，待确认）",
                    "status": "unresolved",
                }
            )
        return {
            "artifact_id": f"art_{meeting_id}_actions",
            "meeting_id": meeting_id,
            "org_domains": org_domains,
            "scenario_type": scenario_type,
            "skill_pack_id": skill_pack_id,
            "artifact_kind": "action_items",
            "schema_id": "action_items",
            "schema_version": "1.0.0",
            "payload": {
                "items": filled.action_items,
                "open_questions": filled.open_questions,
            },
            "confidence": "med"
            if filled.action_items and filled.action_items[0].get("status") != "unresolved"
            else "low",
            "unresolved": [
                {"code": "open_question", "message": q, "blocking_embed": False}
                for q in filled.open_questions
            ],
            "source_spans": [
                {"start_ms": i * 1000, "end_ms": i * 1000 + 800, "quote": s[:60]}
                for i, s in enumerate(segments[:5])
            ],
            "references": references or [],
            "classification": classification,
            "continuum_write_class": continuum_write_class,
            "created_by_stage": "artifact",
        }
