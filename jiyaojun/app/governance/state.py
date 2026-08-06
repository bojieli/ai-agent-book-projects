"""Governance: only approved skills loadable by production pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class GovernanceStatus(StrEnum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REVOKED = "revoked"


@dataclass
class SkillGovernanceRecord:
    skill_pack_id: str
    status: GovernanceStatus
    story_id: str
    orchestration_mode: str
    maturity_level: str


def can_load_in_production(rec: SkillGovernanceRecord) -> bool:
    return rec.status == GovernanceStatus.APPROVED
