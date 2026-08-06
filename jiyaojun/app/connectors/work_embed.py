"""WorkEmbed — HITL gated writeback + sync (Phase 3)."""

from __future__ import annotations

import uuid
from typing import Any

from app.domain_layer.work_object import WorkObjectRef
from app.events import DomainEvent, DomainEventType, EventLog
from app.events.enums import PRODUCTION_EFFECT_RANK
from app.harness import ToolRuntime, idem_key


class WorkEmbedService:
    def __init__(self, runtime: ToolRuntime, events: EventLog | None = None) -> None:
        self.runtime = runtime
        self.events = events or EventLog()

    def embed_defect(
        self,
        *,
        meeting_id: str,
        title: str,
        org_domain: str,
        artifact_id: str,
        production_effect_cap: str,
        hitl_passed: bool,
        source_spans: list[dict[str, Any]] | None = None,
    ) -> WorkObjectRef:
        if not hitl_passed:
            self.events.emit(
                DomainEvent(
                    DomainEventType.HITL_REQUESTED,
                    meeting_id,
                    {"task_id": "embed_confirm", "kind": "embed_confirm"},
                    producer="work_embed",
                )
            )
            raise PermissionError("HITL required before embed")

        key = idem_key(meeting_id, "defect", title)
        result = self.runtime.call(
            "connector.defect.create",
            meeting_id,
            {"title": title},
            allowlist=["connector.defect.create"],
            max_effect=production_effect_cap,
            effect_rank=PRODUCTION_EFFECT_RANK,
            idempotency_key=key,
        )
        wo = WorkObjectRef(
            work_object_id=f"wo_{uuid.uuid4().hex[:8]}",
            connector_id="connector.defect.create",
            org_domain=org_domain,
            object_type="defect",
            production_effect=result["production_effect"],
            idempotency_key=key,
            meeting_id=meeting_id,
            status=result["status"],
            external_id=result["external_id"],
            artifact_id=artifact_id,
            source_spans=source_spans or [],
        )
        self.events.emit(
            DomainEvent(
                DomainEventType.WORK_LINK_SUBMITTED,
                meeting_id,
                {"work_object_id": wo.work_object_id, "idempotency_key": key},
                producer="work_embed",
            )
        )
        return wo

    def sync(
        self,
        wo: WorkObjectRef,
        *,
        status: str,
        sync_fn: Any | None = None,
    ) -> WorkObjectRef:
        if sync_fn:
            sync_fn(wo.idempotency_key, status)
        wo.status = status
        wo.last_synced_at = "2026-08-03T23:00:00+08:00"
        self.events.emit(
            DomainEvent(
                DomainEventType.WORK_LINK_SYNCED,
                wo.meeting_id,
                {
                    "work_object_id": wo.work_object_id,
                    "status": status,
                    "external_id": wo.external_id,
                },
                producer="work_embed",
            )
        )
        return wo
