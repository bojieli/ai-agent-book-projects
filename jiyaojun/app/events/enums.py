"""Domain event type catalog — SoT with docs/meeting-assistant/08_Domain_Event目录.md."""

from __future__ import annotations

from enum import StrEnum


class DomainEventType(StrEnum):
    MEETING_SCHEDULED = "meeting.scheduled"
    TRANSCRIPT_READY = "transcript.ready"
    UNDERSTANDING_COMPLETED = "understanding.completed"
    AMBIGUITY_OPENED = "ambiguity.opened"
    AMBIGUITY_RESOLVED = "ambiguity.resolved"
    ARTIFACT_PERSISTED = "artifact.persisted"
    EVALUATION_PASSED = "evaluation.passed"
    EVALUATION_FAILED = "evaluation.failed"
    HITL_REQUESTED = "hitl.requested"
    HITL_RESOLVED = "hitl.resolved"
    WORK_LINK_SUBMITTED = "work_link.submitted"
    WORK_LINK_SYNCED = "work_link.synced"
    CONTINUUM_WRITE_DECIDED = "continuum.write_decided"
    CONTINUUM_ITEM_CLOSED = "continuum.item_closed"
    RENDER_COMPLETED = "render.completed"
    RENDER_SKIPPED = "render.skipped"
    DELIVERY_SENT = "delivery.sent"
    DELIVERY_SUPPRESSED = "delivery.suppressed"
    PIPELINE_TERMINAL = "pipeline.terminal"
    BUDGET_EXHAUSTED = "budget.exhausted"
    POLICY_BINDING_UPDATED = "policy_binding.updated"


# Strictness order for embed_gate max_strict
EMBED_GATE_RANK = {"allow": 0, "confirm_only": 1, "block": 2}

PRODUCTION_EFFECT_RANK = {
    "none": 0,
    "draft_only": 1,
    "observe": 2,
    "production": 3,
}
