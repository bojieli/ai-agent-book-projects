"""Full BFF API surface (05 §4) — in-process mock of HTTP/SSE."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterator

from app.api.app import ApiApp
from app.events import DomainEvent, DomainEventType, EventLog
from app.governance.glossary_admin import GlossaryAdmin
from app.governance.skill_admin import SkillAdmin
from app.governance.state import GovernanceStatus, SkillGovernanceRecord
from app.knowledge.embedding import BgeM3ShimProvider
from app.knowledge.glossary import GlossaryEntry
from app.knowledge.plane import KnowledgePlane
from app.knowledge.rag import RagPipeline
from app.observability import Observability, UsageLedger
from app.observability.quota import CostQuota
from app.knowledge.transcript import TranscriptAdapter
from app.planes.dialog.session_service import DialogSessionService
from app.render import RenderService
from app.render.charts import render_charts
from app.security.authz import MockAuthZ
from app.security.hardening import RateLimiter


class BffApp(ApiApp):
    # webhook 终态：同步关闭 Continuum open item
    _CLOSED_WORK_STATUSES = frozenset({"closed", "done", "resolved"})

    def __init__(self, root: Path) -> None:
        super().__init__(root)
        self.authz = MockAuthZ()
        self.limiter = RateLimiter(max_per_window=100, window_sec=10)
        self.skill_admin = SkillAdmin()
        self.glossary_admin = GlossaryAdmin()
        self.quotas: dict[str, CostQuota] = {"default": CostQuota()}
        self.obs = Observability()
        self.events = EventLog()
        self.render_svc = RenderService(root / "app" / "render" / "default")
        self.sessions: dict[str, dict[str, Any]] = {}  # mock Redis sess:
        # Knowledge / Dialog：聊天走 grounding，不再空回声
        self.knowledge = KnowledgePlane(RagPipeline(BgeM3ShimProvider()))
        self.knowledge.seed_demo()
        self.dialog_sessions = DialogSessionService(knowledge=self.knowledge)
        self.dialog = self.dialog_sessions.dialog
        self.transcript_adapter = TranscriptAdapter()
        # seed general approved
        self.skill_admin.upsert_draft(
            SkillGovernanceRecord(
                "platform/general@0.1.0",
                GovernanceStatus.DRAFT,
                "general",
                "playbook",
                "L0",
            )
        )
        self.skill_admin.submit("platform/general@0.1.0")
        self.skill_admin.approve("platform/general@0.1.0", "u_admin", "eval_seed")

    def _actor(self, token: str):
        return self.authz.authenticate(token)

    # --- Dialog ---
    def post_chat_completions(self, token: str, body: dict[str, Any]) -> Iterator[str]:
        """SSE：知识类问题走 RAG grounding，其余回显确认。"""
        p = self._actor(token)
        if not self.limiter.allow(p.user_id):
            yield "data: " + json.dumps({"error": "rate_limited"}) + "\n\n"
            return
        self.authz.authorize(p, "dialog.chat", "chat")
        msg = body.get("messages", [{}])[-1].get("content", "")
        session_id = body.get("session_id") or f"sess_{p.user_id}"
        org_domains = body.get("org_domains") or getattr(p, "org_domains", None) or ["eng"]

        is_admin = "admin" in p.roles
        chat_out = self.dialog_sessions.chat(
            session_id=session_id,
            user_id=p.user_id,
            org_domains=list(org_domains),
            message=msg,
            scenario=body.get("scenario_code", "dialog"),
            tool_allowlist=body.get("tool_allowlist"),
            is_admin=is_admin,
        )
        self.sessions[session_id] = {
            "user": p.user_id,
            "last": msg,
            "terminal": chat_out.get("terminal"),
            "mode": chat_out.get("mode"),
        }

        if chat_out.get("mode") == "rag_grounding" or chat_out.get("faithfulness") is not None:
            text = chat_out.get("answer", "")
            citations = chat_out.get("citations") or []
            faith = chat_out.get("faithfulness", 0.0)
            mid = max(1, len(text) // 2)
            yield "data: " + json.dumps(
                {
                    "id": "chunk1",
                    "delta": text[:mid],
                    "faithfulness": faith,
                    "citations": citations[:3],
                    "session_id": session_id,
                    "memory_kind": chat_out.get("memory_kind"),
                },
                ensure_ascii=False,
            ) + "\n\n"
            yield "data: " + json.dumps(
                {"id": "chunk2", "delta": text[mid:], "session_id": session_id},
                ensure_ascii=False,
            ) + "\n\n"
            yield "data: [DONE]\n\n"
            return

        if chat_out.get("terminal") == "suspended":
            yield "data: " + json.dumps(
                {
                    "id": "chunk1",
                    "delta": chat_out.get("answer", "等待人工确认"),
                    "session_id": session_id,
                    "terminal": "suspended",
                },
                ensure_ascii=False,
            ) + "\n\n"
            yield "data: [DONE]\n\n"
            return

        text = chat_out.get("answer", f"已收到：{msg[:80]}")
        yield "data: " + json.dumps(
            {"id": "chunk1", "delta": text, "session_id": session_id, "mode": chat_out.get("mode")},
            ensure_ascii=False,
        ) + "\n\n"
        yield "data: [DONE]\n\n"

    def get_session_context(self, token: str, session_id: str) -> dict[str, Any]:
        p = self._actor(token)
        self.authz.authorize(p, "dialog.chat", "chat")
        is_admin = "admin" in p.roles
        return self.dialog_sessions.get_context(
            session_id,
            user_id=p.user_id,
            org_domains=list(p.org_domains),
            is_admin=is_admin,
        )

    def post_session_resume(self, token: str, body: dict[str, Any]) -> dict[str, Any]:
        p = self._actor(token)
        self.authz.authorize(p, "dialog.chat", "chat")
        is_admin = "admin" in p.roles
        return self.dialog_sessions.resume_hitl(
            session_id=body["session_id"],
            user_id=p.user_id,
            org_domains=body.get("org_domains") or list(p.org_domains),
            message=body.get("message", ""),
            approved=body.get("approved", True),
            tool_allowlist=body.get("tool_allowlist"),
            is_admin=is_admin,
        )

    def get_task_status(self, token: str, task_id: str) -> dict[str, Any]:
        p = self._actor(token)
        self.authz.authorize(p, "dialog.chat", "chat")
        is_admin = "admin" in p.roles
        return self.dialog_sessions.task_status(task_id, user_id=p.user_id, is_admin=is_admin)

    def post_task_cancel(self, token: str, task_id: str) -> dict[str, Any]:
        p = self._actor(token)
        self.authz.authorize(p, "dialog.chat", "chat")
        is_admin = "admin" in p.roles
        return self.dialog_sessions.cancel_task(task_id, user_id=p.user_id, is_admin=is_admin)

    def patch_meeting(self, token: str, meeting_id: str, body: dict[str, Any]) -> dict[str, Any]:
        p = self._actor(token)
        self.authz.authorize(p, "meeting.patch", f"meeting:{meeting_id}")
        m = self.store.get(meeting_id)
        if not m:
            raise KeyError(meeting_id)
        if "purpose" in body:
            m.purpose = body["purpose"]
        if "scenario_code" in body:
            m.scenario_code = body["scenario_code"]
        self.store.update(m)
        return asdict(m)

    def post_render(self, token: str, meeting_id: str, body: dict[str, Any]) -> dict[str, Any]:
        p = self._actor(token)
        self.authz.authorize(p, "meeting.render", f"meeting:{meeting_id}")
        m = self.store.get(meeting_id)
        if not m:
            raise KeyError(meeting_id)
        allowlist = body.get("allowlist")
        view = self.render_svc.materialize_acl_view(
            view_id=f"acl_{meeting_id}_rerender",
            meeting_id=meeting_id,
            artifacts=m.artifacts or [{"artifact_kind": "summary_view", "payload": {"summary": m.purpose}, "unresolved": []}],
            viewer_ids=m.participants or [p.user_id],
            classification=m.classification,
            allowlist=allowlist,
        )
        charts = render_charts(view.artifacts)
        rr = self.render_svc.render_email(
            job_id=f"rj_api_{meeting_id}",
            acl_view=view,
            classification=m.classification,
            allowlist=allowlist,
            context={
                "artifacts": view.artifacts,
                "meeting": {"id": meeting_id, "purpose": m.purpose},
            },
        )
        return {
            "status": rr.status,
            "skip_reason": rr.skip_reason,
            "charts": charts,
            "html_len": len(rr.html or ""),
        }

    # --- Admin ---
    def admin_skills_list(self, token: str) -> list[dict[str, Any]]:
        p = self._actor(token)
        self.authz.authorize(p, "admin.skills", "skills")
        return [
            {
                "skill_pack_id": r.skill_pack_id,
                "status": str(r.status),
                "story_id": r.story_id,
            }
            for r in self.skill_admin.records.values()
        ]

    def admin_skills_submit(self, token: str, skill_pack_id: str) -> dict[str, Any]:
        p = self._actor(token)
        self.authz.authorize(p, "admin.skills", "skills")
        if skill_pack_id not in self.skill_admin.records:
            self.skill_admin.upsert_draft(
                SkillGovernanceRecord(skill_pack_id, GovernanceStatus.DRAFT, "?", "playbook", "L2")
            )
        r = self.skill_admin.submit(skill_pack_id)
        return {"skill_pack_id": skill_pack_id, "status": str(r.status)}

    def admin_skills_approve(self, token: str, skill_pack_id: str, eval_run_id: str) -> dict[str, Any]:
        p = self._actor(token)
        self.authz.authorize(p, "admin.skills", "skills")
        r = self.skill_admin.approve(skill_pack_id, p.user_id, eval_run_id)
        return {"skill_pack_id": skill_pack_id, "status": str(r.status)}

    def admin_glossary_approve(self, token: str, org_domain: str, term: str, gloss: str) -> dict[str, Any]:
        p = self._actor(token)
        self.authz.authorize(p, "admin.glossary", "glossary", org_domain=org_domain)
        self.glossary_admin.submit(GlossaryEntry(org_domain, term, gloss, "draft"))
        e = self.glossary_admin.approve(org_domain, term, p.user_id)
        return {"term": e.term, "status": e.governance_status}

    def admin_quotas_get(self, token: str) -> dict[str, Any]:
        p = self._actor(token)
        self.authz.authorize(p, "admin.quotas", "quotas")
        q = self.quotas["default"]
        return q.__dict__

    def admin_quotas_put(self, token: str, body: dict[str, Any]) -> dict[str, Any]:
        p = self._actor(token)
        self.authz.authorize(p, "admin.quotas", "quotas")
        q = self.quotas["default"]
        for k, v in body.items():
            if hasattr(q, k):
                setattr(q, k, v)
        return q.__dict__

    def admin_usage_get(self, token: str) -> list[dict[str, Any]]:
        p = self._actor(token)
        self.authz.authorize(p, "admin.usage", "usage")
        if not self.obs.usage:
            self.obs.record_usage(UsageLedger("eng", "tech_review", llm_tokens=100))
        return [u.__dict__ for u in self.obs.usage]

    # --- Internal callbacks ---
    def internal_transcripts(self, token: str, body: dict[str, Any], signature: str) -> dict[str, Any]:
        p = self._actor(token)
        self.authz.authorize(p, "internal.transcript", "transcript")
        if signature != "mock-sign":
            raise PermissionError("bad signature")
        mid = body["meeting_id"]
        td_id = body.get("transcript_document_id") or f"td_{mid}"
        object_key = body.get("object_key") or f"s3://mock/{mid}/transcript.json"
        mobj = self.store.get(mid)
        org_domains = body.get("org_domains") or (mobj.org_domains if mobj else ["eng"])
        segments = body.get("segments")
        chunks_indexed = 0
        if segments:
            doc = self.transcript_adapter.from_callback(
                meeting_id=mid,
                org_domains=list(org_domains),
                transcript_document_id=td_id,
                object_key=object_key,
                segments=segments,
            )
            classification = mobj.classification if mobj else "internal"
            principals = mobj.participants if mobj and mobj.participants else [p.user_id]
            indexed = self.knowledge.ingest_transcript(
                doc,
                org_domain=org_domains[0],
                classification=classification,
                acl_principals=principals,
                title=mobj.purpose if mobj else mid,
                series_id=mobj.series_id if mobj else None,
                write_class="sealed" if classification == "critical" else "domain",
            )
            chunks_indexed = len(indexed)
            if mobj:
                mobj.transcript_document_id = doc.transcript_document_id
                mobj.transcript_object_key = doc.object_key
                self.store.update(mobj)
        self.events.emit(
            DomainEvent(
                DomainEventType.TRANSCRIPT_READY,
                mid,
                {
                    "transcript_document_id": td_id,
                    "object_key": object_key,
                    "chunks_indexed": chunks_indexed,
                },
                producer="internal",
            )
        )
        return {"ok": True, "event": "transcript.ready", "chunks_indexed": chunks_indexed}

    def internal_connector_webhook(self, token: str, body: dict[str, Any]) -> dict[str, Any]:
        p = self._actor(token)
        self.authz.authorize(p, "internal.webhook", "connector")
        mid = body["meeting_id"]
        status = str(body.get("status") or "")
        work_object_id = body.get("work_object_id")
        self.events.emit(
            DomainEvent(
                DomainEventType.WORK_LINK_SYNCED,
                mid,
                {
                    "work_object_id": work_object_id,
                    "status": status,
                    "external_id": body.get("external_id"),
                },
                producer="webhook",
            )
        )
        m = self.store.get(mid)
        continuum_closed = False
        if m:
            for wo in m.work_objects:
                if wo.get("work_object_id") == work_object_id:
                    wo["status"] = status
            self.store.update(m)
            # 缺陷关闭时同步 Continuum / Series open items
            if status.lower() in self._CLOSED_WORK_STATUSES:
                series_id = body.get("series_id") or m.series_id
                item_id = body.get("item_id") or f"{mid}_open"
                if series_id:
                    continuum_closed = self.knowledge.series_bridge.close_open_item(
                        series_id, item_id
                    )
                    if continuum_closed:
                        self.events.emit(
                            DomainEvent(
                                DomainEventType.CONTINUUM_ITEM_CLOSED,
                                mid,
                                {
                                    "series_id": series_id,
                                    "item_id": item_id,
                                    "work_object_id": work_object_id,
                                    "status": status,
                                },
                                producer="webhook",
                            )
                        )
        return {
            "ok": True,
            "event": "work_link.synced",
            "continuum_closed": continuum_closed,
        }
