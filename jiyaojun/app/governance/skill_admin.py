"""Skill governance admin — draft → in_review → approved / revoked."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.governance.state import GovernanceStatus, SkillGovernanceRecord, can_load_in_production


@dataclass
class SkillAdmin:
    records: dict[str, SkillGovernanceRecord] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)

    def upsert_draft(self, rec: SkillGovernanceRecord) -> SkillGovernanceRecord:
        rec.status = GovernanceStatus.DRAFT
        self.records[rec.skill_pack_id] = rec
        return rec

    def submit(self, skill_pack_id: str) -> SkillGovernanceRecord:
        r = self.records[skill_pack_id]
        self.history.append({"id": skill_pack_id, "from": r.status, "to": "in_review"})
        r.status = GovernanceStatus.IN_REVIEW
        return r

    def approve(self, skill_pack_id: str, approver: str, eval_run_id: str) -> SkillGovernanceRecord:
        r = self.records[skill_pack_id]
        self.history.append(
            {
                "id": skill_pack_id,
                "from": r.status,
                "to": "approved",
                "approver": approver,
                "eval_run_id": eval_run_id,
            }
        )
        r.status = GovernanceStatus.APPROVED
        return r

    def revoke(self, skill_pack_id: str) -> SkillGovernanceRecord:
        r = self.records[skill_pack_id]
        r.status = GovernanceStatus.REVOKED
        return r

    def production_loadable(self, skill_pack_id: str) -> bool:
        return can_load_in_production(self.records[skill_pack_id])
