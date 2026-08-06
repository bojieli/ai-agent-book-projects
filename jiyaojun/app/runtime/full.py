"""End-to-end runtime composing Phase 1–4 (Orchestrator core stays stable)."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from app.agents.artifact_agent import ArtifactAgent
from app.agents.evaluator import Evaluator
from app.connectors.persistent_defect import PersistentDefectConnector
from app.connectors.departments import department_connectors
from app.connectors.work_embed import WorkEmbedService
from app.delivery.service import DeliveryService
from app.domain_layer import validate_envelope
from app.events import DomainEvent, DomainEventType, EventLog
from app.harness import ToolRuntime
from app.ops.chaos import ChaosProxy
from app.policy import AmbiguityService, max_strict_embed_gate, policy_hooks_ok
from app.render import RenderService
from app.schedule.service import CalendarDirectory, ScheduleService
from app.security.hardening import RateLimiter, redact_artifact
from app.store.meetings import MeetingStore
from app.knowledge import KnowledgePlane, RagPipeline
from app.knowledge.embedding import BgeM3ShimProvider
from app.knowledge.transcript import TranscriptAdapter
from app.understanding.agent import UnderstandingAgent


class FullRuntime:
    """New connectors register on ToolRuntime — Orchestrator/runtime wiring unchanged."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.events = EventLog()
        self.store = MeetingStore(root / "data" / "meetings_e2e.json")
        self.calendar = CalendarDirectory(root / "fixtures" / "calendar")
        self.schedule = ScheduleService(self.store, self.calendar, self.events)
        self.understanding = UnderstandingAgent()
        self.artifact_agent = ArtifactAgent()
        self.evaluator = Evaluator()
        self.ambiguity = AmbiguityService()
        self.runtime = ToolRuntime()
        self.defect = PersistentDefectConnector(root / "data" / "defects.json")
        self.runtime.register(self.defect)
        for c in department_connectors():
            self.runtime.register(c)
        self.work_embed = WorkEmbedService(self.runtime, self.events)
        self.render = RenderService(root / "app" / "render" / "default")
        self.delivery = DeliveryService(self.render, self.events)
        self.limiter = RateLimiter(max_per_window=50, window_sec=10)
        self.knowledge = KnowledgePlane(RagPipeline(BgeM3ShimProvider()))
        self.knowledge.seed_demo()
        self.transcript_adapter = TranscriptAdapter()

    def register_chaos_on_defect(self, *, fail_next: int = 0, timeout_next: int = 0) -> ChaosProxy:
        proxy = ChaosProxy(self.defect, fail_next=fail_next, timeout_next=timeout_next)
        self.runtime.register(proxy)  # overwrite by id
        self.runtime._tools[proxy.id] = proxy
        return proxy

    def run_meeting_lifecycle(
        self,
        *,
        event_id: str,
        purpose: str,
        idempotency_key: str,
        user_id: str,
        segments: list[str],
        hitl_approve: bool = True,
        allowlist: list[str] | None = None,
    ) -> dict[str, Any]:
        if not self.limiter.allow(user_id):
            raise PermissionError("rate_limited")

        scheduled = self.schedule.schedule_from_calendar(
            event_id=event_id,
            purpose=purpose,
            idempotency_key=idempotency_key,
            created_by=user_id,
        )
        meeting = scheduled["meeting"]

        if scheduled["needs_hitl"]:
            if not hitl_approve:
                return {"stage": "awaiting_schedule_hitl", "meeting_id": meeting.meeting_id}
            meeting = self.schedule.resolve_hitl(
                meeting.meeting_id, "schedule_confirm", "approve"
            )

        # Phase 2 understanding
        doc, und = self.understanding.understand(
            meeting_id=meeting.meeting_id,
            org_domains=meeting.org_domains,
            segments=segments,
        )
        self.events.emit(
            DomainEvent(
                DomainEventType.TRANSCRIPT_READY,
                meeting.meeting_id,
                {
                    "transcript_document_id": doc.transcript_document_id,
                    "object_key": doc.object_key,
                    "hotword_profile_id": doc.hotword_profile_id,
                    "segment_count": doc.segment_count,
                },
                producer="transcript",
            )
        )
        self.events.emit(
            DomainEvent(
                DomainEventType.UNDERSTANDING_COMPLETED,
                meeting.meeting_id,
                {
                    "quality": und.quality,
                    "unknown_terms": und.unknown_terms,
                    "blocks_decision": und.blocks_decision,
                    "wrong_domain_hits": und.wrong_domain_hits,
                },
                producer="understanding",
            )
        )
        indexed = self.knowledge.ingest_transcript(
            doc,
            org_domain=meeting.org_domains[0],
            classification=meeting.classification,
            acl_principals=meeting.participants or [user_id],
            title=meeting.purpose,
            series_id=meeting.series_id,
            write_class="sealed" if meeting.classification == "critical" else "domain",
        )
        meeting.transcript_document_id = doc.transcript_document_id
        meeting.transcript_object_key = doc.object_key
        self.store.update(meeting)

        # X1 ambiguity if 灰度 and multi-domain
        if "灰度" in "".join(segments) and set(meeting.org_domains) >= {"eng", "business"}:
            rec = self.ambiguity.open(
                meeting.meeting_id,
                "灰度",
                [
                    {"sense_id": "eng_release_canary", "org_domain": "eng", "gloss": "发布灰度"},
                    {"sense_id": "biz_cohort_gray", "org_domain": "business", "gloss": "客群灰度"},
                ],
            )
            self.events.emit(
                DomainEvent(
                    DomainEventType.AMBIGUITY_OPENED,
                    meeting.meeting_id,
                    {
                        "ambiguity_record_id": rec.ambiguity_record_id,
                        "term": "灰度",
                        "effect_on_embed_gate": "block",
                    },
                    producer="ambiguity",
                )
            )
            if hitl_approve:
                self.ambiguity.resolve(rec.ambiguity_record_id, "eng_release_canary", user_id)
                self.events.emit(
                    DomainEvent(
                        DomainEventType.AMBIGUITY_RESOLVED,
                        meeting.meeting_id,
                        {
                            "ambiguity_record_id": rec.ambiguity_record_id,
                            "resolved_sense": "eng_release_canary",
                            "resolver_user_id": user_id,
                        },
                        producer="ambiguity",
                    )
                )

        if und.blocks_embed:
            meeting.pipeline_terminal = "awaiting_hitl"
            meeting.status = "blocked_understanding"
            self.store.update(meeting)
            return {
                "stage": "blocked_understanding",
                "meeting_id": meeting.meeting_id,
                "understanding": und.__dict__,
                "events": self.events.types(),
            }

        artifact = self.artifact_agent.build_action_items_envelope(
            meeting_id=meeting.meeting_id,
            org_domains=meeting.org_domains,
            scenario_type=meeting.scenario_code,
            skill_pack_id=meeting.skill_pack_id or "eng/R1_req_sync@0.1.0",
            segments=segments,
            classification=meeting.classification,
            continuum_write_class="sealed" if meeting.classification == "critical" else "wide",
        )
        artifact = redact_artifact(artifact)
        env_errs = validate_envelope(artifact)
        effect = "none" if meeting.classification == "critical" else "draft_only"
        cap = "none" if meeting.classification == "critical" else "draft_only"
        policy_fail = policy_hooks_ok(
            classification=artifact["classification"],
            continuum_write_class=artifact["continuum_write_class"],
            production_effect=effect,
            production_effect_cap=cap,
            embed_gate=max_strict_embed_gate(
                "confirm_only" if meeting.classification != "critical" else "block"
            ),
            maturity="L2",
        )
        if meeting.classification == "critical":
            # critical: no auto embed
            eval_res = self.evaluator.evaluate(artifact=artifact, policy_failures=policy_fail)
            meeting.artifacts = [artifact]
            deliveries = self.delivery.deliver_pack(
                meeting_id=meeting.meeting_id,
                artifacts=[artifact],
                participants=meeting.participants,
                classification=meeting.classification,
                purpose=meeting.purpose,
                allowlist=allowlist,
            )
            meeting.deliveries = [asdict(d) if hasattr(d, "__dataclass_fields__") else d.__dict__ for d in deliveries]
            meeting.pipeline_terminal = "succeeded"
            meeting.status = "closed_no_embed"
            self.store.update(meeting)
            return {
                "stage": "critical_no_embed",
                "meeting_id": meeting.meeting_id,
                "artifact": artifact,
                "deliveries": meeting.deliveries,
                "eval_passed": eval_res.passed,
                "envelope_errors": env_errs,
                "events": self.events.types(),
            }

        eval_res = self.evaluator.evaluate(artifact=artifact, policy_failures=policy_fail)
        self.events.emit(
            DomainEvent(
                DomainEventType.ARTIFACT_PERSISTED,
                meeting.meeting_id,
                {"artifact_ids": [artifact["artifact_id"]]},
                producer="artifact",
            )
        )
        if not eval_res.passed or env_errs:
            self.events.emit(
                DomainEvent(
                    DomainEventType.EVALUATION_FAILED,
                    meeting.meeting_id,
                    {"failures": eval_res.failures or env_errs},
                    producer="evaluator",
                )
            )
            meeting.pipeline_terminal = "awaiting_hitl"
            self.store.update(meeting)
            return {
                "stage": "eval_failed",
                "meeting_id": meeting.meeting_id,
                "failures": eval_res.failures,
                "envelope_errors": env_errs,
            }

        self.events.emit(
            DomainEvent(
                DomainEventType.EVALUATION_PASSED,
                meeting.meeting_id,
                {"checks": eval_res.checks},
                producer="evaluator",
            )
        )

        # open ambiguity unresolved blocks embed
        open_amb = [r for r in self.ambiguity.records.values() if r.meeting_id == meeting.meeting_id and r.status == "open"]
        if open_amb:
            meeting.pipeline_terminal = "awaiting_hitl"
            self.store.update(meeting)
            return {"stage": "ambiguity_open", "meeting_id": meeting.meeting_id}

        title = artifact["payload"]["items"][0]["title"]
        wo = self.work_embed.embed_defect(
            meeting_id=meeting.meeting_id,
            title=title,
            org_domain=meeting.org_domains[0],
            artifact_id=artifact["artifact_id"],
            production_effect_cap="draft_only",
            hitl_passed=hitl_approve,
            source_spans=artifact["source_spans"],
        )
        wo = self.work_embed.sync(wo, status="open", sync_fn=self.defect.sync_status)

        deliveries = self.delivery.deliver_pack(
            meeting_id=meeting.meeting_id,
            artifacts=[artifact],
            participants=meeting.participants,
            classification=meeting.classification,
            purpose=meeting.purpose,
            allowlist=None,
        )

        meeting.artifacts = [artifact]
        meeting.work_objects = [wo.to_dict()]
        meeting.deliveries = [d.__dict__ for d in deliveries]
        meeting.pipeline_terminal = "succeeded"
        meeting.status = "closed"
        self.store.update(meeting)
        self.events.emit(
            DomainEvent(
                DomainEventType.PIPELINE_TERMINAL,
                meeting.meeting_id,
                {"terminal": "succeeded"},
                producer="runtime",
            )
        )
        return {
            "stage": "succeeded",
            "meeting_id": meeting.meeting_id,
            "org_domains": meeting.org_domains,
            "scenario_code": meeting.scenario_code,
            "work_object": wo.to_dict(),
            "defect_persisted": self.defect.get(wo.idempotency_key),
            "deliveries": meeting.deliveries,
            "transcript_chunks_indexed": len(indexed),
            "events": self.events.types(),
        }
