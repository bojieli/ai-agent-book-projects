"""WorkObjectRef — Phase 0 required fields (03 §2.7)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class WorkObjectRef:
    work_object_id: str
    connector_id: str
    org_domain: str
    object_type: str
    production_effect: str
    idempotency_key: str
    meeting_id: str
    status: str = "draft"
    external_id: str | None = None
    external_url: str | None = None
    artifact_id: str | None = None
    source_spans: list[dict[str, Any]] = field(default_factory=list)
    series_id: str | None = None
    project_id: str | None = None
    owner_user_id: str | None = None
    last_synced_at: str | None = None
    sync_error: str | None = None
    acl_snapshot: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def required_fields() -> list[str]:
        return [
            "work_object_id",
            "connector_id",
            "org_domain",
            "object_type",
            "production_effect",
            "idempotency_key",
            "meeting_id",
            "status",
        ]
