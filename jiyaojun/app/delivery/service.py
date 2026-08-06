"""Delivery — only after acl_view render (Phase 3)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from app.events import DomainEvent, DomainEventType, EventLog
from app.render import RenderService


@dataclass
class DeliveryRecord:
    delivery_id: str
    meeting_id: str
    channel: str
    format: str
    render_job_id: str
    acl_view_id: str
    recipient_set_hash: str
    suppressed: bool = False
    reason: str | None = None


class DeliveryService:
    def __init__(self, render: RenderService, events: EventLog | None = None) -> None:
        self.render = render
        self.events = events or EventLog()
        self.records: list[DeliveryRecord] = []

    def deliver_pack(
        self,
        *,
        meeting_id: str,
        artifacts: list[dict[str, Any]],
        participants: list[str],
        classification: str,
        purpose: str,
        allowlist: list[str] | None = None,
        formats: list[str] | None = None,
    ) -> list[DeliveryRecord]:
        formats = formats or ["email_html", "markdown", "action_table"]
        view = self.render.materialize_acl_view(
            view_id=f"acl_{meeting_id}",
            meeting_id=meeting_id,
            artifacts=artifacts,
            viewer_ids=participants,
            classification=classification,
            allowlist=allowlist,
        )
        out: list[DeliveryRecord] = []
        for fmt in formats:
            job_id = f"rj_{meeting_id}_{fmt}"
            if classification == "critical" and not allowlist:
                rec = DeliveryRecord(
                    delivery_id=f"dlv_{meeting_id}_{fmt}",
                    meeting_id=meeting_id,
                    channel="email" if fmt == "email_html" else "file",
                    format=fmt,
                    render_job_id=job_id,
                    acl_view_id=view.view_id,
                    recipient_set_hash="",
                    suppressed=True,
                    reason="critical_no_allowlist",
                )
                self.events.emit(
                    DomainEvent(
                        DomainEventType.RENDER_SKIPPED,
                        meeting_id,
                        {"reason": rec.reason, "render_job_id": job_id},
                        producer="delivery",
                    )
                )
                self.events.emit(
                    DomainEvent(
                        DomainEventType.DELIVERY_SUPPRESSED,
                        meeting_id,
                        {"reason": rec.reason},
                        producer="delivery",
                    )
                )
                out.append(rec)
                continue

            if fmt == "email_html":
                rr = self.render.render_email(
                    job_id=job_id,
                    acl_view=view,
                    classification=classification,
                    allowlist=allowlist,
                    context={
                        "artifacts": artifacts,
                        "meeting": {"id": meeting_id, "purpose": purpose},
                    },
                )
                if rr.status == "skipped":
                    rec = DeliveryRecord(
                        delivery_id=f"dlv_{meeting_id}_{fmt}",
                        meeting_id=meeting_id,
                        channel="email",
                        format=fmt,
                        render_job_id=job_id,
                        acl_view_id=view.view_id,
                        recipient_set_hash="",
                        suppressed=True,
                        reason=rr.skip_reason,
                    )
                    self.events.emit(
                        DomainEvent(
                            DomainEventType.DELIVERY_SUPPRESSED,
                            meeting_id,
                            {"reason": rec.reason},
                            producer="delivery",
                        )
                    )
                    out.append(rec)
                    continue
                body = rr.html or ""
            elif fmt == "markdown":
                body = self._markdown(artifacts, purpose)
            else:
                body = self._action_table(artifacts)

            rh = hashlib.sha256(",".join(sorted(view.recipient_ids)).encode()).hexdigest()[:16]
            rec = DeliveryRecord(
                delivery_id=f"dlv_{meeting_id}_{fmt}",
                meeting_id=meeting_id,
                channel="email" if fmt == "email_html" else "file",
                format=fmt,
                render_job_id=job_id,
                acl_view_id=view.view_id,
                recipient_set_hash=rh,
            )
            self.events.emit(
                DomainEvent(
                    DomainEventType.RENDER_COMPLETED,
                    meeting_id,
                    {
                        "render_job_id": job_id,
                        "acl_view_id": view.view_id,
                        "format": fmt,
                        "bytes": len(body),
                    },
                    producer="delivery",
                )
            )
            self.events.emit(
                DomainEvent(
                    DomainEventType.DELIVERY_SENT,
                    meeting_id,
                    {
                        "channel": rec.channel,
                        "recipient_set_hash": rh,
                        "render_job_id": job_id,
                    },
                    producer="delivery",
                )
            )
            out.append(rec)
        self.records.extend(out)
        return out

    @staticmethod
    def _markdown(artifacts: list[dict[str, Any]], purpose: str) -> str:
        lines = [f"# {purpose}", ""]
        for a in artifacts:
            lines.append(f"## {a.get('artifact_kind')}")
            lines.append(f"```json\n{a.get('payload')}\n```")
        return "\n".join(lines)

    @staticmethod
    def _action_table(artifacts: list[dict[str, Any]]) -> str:
        rows = ["title|owner|status"]
        for a in artifacts:
            if a.get("artifact_kind") != "action_items":
                continue
            for it in a.get("payload", {}).get("items", []):
                rows.append(f"{it.get('title')}|{it.get('owner','')}|{it.get('status','')}")
        return "\n".join(rows)
