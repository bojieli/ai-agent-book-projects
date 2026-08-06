"""LLM04 — corpus / fine-tune admission gate (process control plane)."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class CorpusAdmission:
    admission_id: str
    tenant_id: str
    name: str
    content_hash: str
    status: str  # pending|approved|rejected
    risk_flags: list[str] = field(default_factory=list)
    reviewer: str = ""
    created_at: str = ""
    note: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "admission_id": self.admission_id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "content_hash": self.content_hash,
            "status": self.status,
            "risk_flags": self.risk_flags,
            "reviewer": self.reviewer,
            "created_at": self.created_at,
            "note": self.note,
        }


POISON_HINTS = [
    "忽略以上规则",
    "ignore previous instructions",
    "hidden instruction",
    "如何制造炸弹",
]


class CorpusAdmissionService:
    """In-memory + optional DB-less registry for CI; production persists via API layer."""

    def __init__(self) -> None:
        self._items: dict[str, CorpusAdmission] = {}

    def submit(
        self,
        *,
        tenant_id: str,
        name: str,
        sample_text: str,
        note: str = "",
    ) -> CorpusAdmission:
        h = hashlib.sha256(sample_text.encode("utf-8")).hexdigest()
        flags = [p for p in POISON_HINTS if p.lower() in sample_text.lower()]
        status = "pending" if not flags else "rejected"
        item = CorpusAdmission(
            admission_id="ca_" + uuid.uuid4().hex[:12],
            tenant_id=tenant_id,
            name=name,
            content_hash=h,
            status=status,
            risk_flags=[f"poison_hint:{f}" for f in flags],
            created_at=datetime.now(timezone.utc).isoformat(),
            note=note
            or (
                "auto-rejected: poison hints in sample"
                if flags
                else "awaiting security review"
            ),
        )
        self._items[item.admission_id] = item
        return item

    def approve(self, admission_id: str, reviewer: str) -> CorpusAdmission:
        item = self._items[admission_id]
        if item.risk_flags:
            raise ValueError("cannot approve corpus with poison risk_flags")
        item.status = "approved"
        item.reviewer = reviewer
        return item

    def get(self, admission_id: str) -> CorpusAdmission | None:
        return self._items.get(admission_id)

    def list(self, tenant_id: str | None = None) -> list[CorpusAdmission]:
        rows = list(self._items.values())
        if tenant_id:
            rows = [r for r in rows if r.tenant_id == tenant_id]
        return rows

    def dump(self) -> str:
        return json.dumps([x.as_dict() for x in self._items.values()], ensure_ascii=False)
