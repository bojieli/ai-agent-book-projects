"""OrgDomain + Scenario registry (fixtures OK; capability required)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OrgDomain:
    code: str
    display_name: str


@dataclass(frozen=True)
class ScenarioProfile:
    code: str
    org_domain: str
    orchestration_mode: str
    maturity_level: str
    default_embed_gate: str
    classification: str
    continuum_write_class: str
    production_effect_cap: str
    story_id: str
    skill_relpath: str


ORG_DOMAINS = [
    OrgDomain("eng", "研发/科技"),
    OrgDomain("business", "业务"),
    OrgDomain("hr", "人力资源"),
    OrgDomain("risk", "风控"),
    OrgDomain("compliance", "合规"),
]


def default_scenarios() -> list[ScenarioProfile]:
    return [
        ScenarioProfile("tech_review", "eng", "playbook", "L2", "confirm_only", "internal", "wide", "draft_only", "R1", "eng/R1_req_sync"),
        ScenarioProfile("release_review", "eng", "sop", "L3", "confirm_only", "confidential", "wide", "draft_only", "R4", "eng/R4_release_review"),
        ScenarioProfile("delivery_sync", "eng", "playbook", "L2", "confirm_only", "internal", "wide", "draft_only", "R5", "eng/R5_delivery_sync"),
        ScenarioProfile("business_review", "business", "playbook", "L2", "confirm_only", "confidential", "domain", "draft_only", "B4", "business/B4_business_review"),
        ScenarioProfile("limit_pricing_review", "business", "sop", "L3", "block", "confidential", "domain", "draft_only", "B5", "business/B5_limit_pricing"),
        ScenarioProfile("perf_calibration", "hr", "playbook", "L2", "block", "critical", "sealed", "none", "H2", "hr/H2_perf_calibration"),
        ScenarioProfile("org_change", "hr", "playbook", "L2", "block", "critical", "sealed", "none", "H5", "hr/H5_org_change"),
        ScenarioProfile("risk_policy_review", "risk", "sop", "L3", "block", "confidential", "domain", "draft_only", "K1", "risk/K1_policy_review"),
        ScenarioProfile("model_monitor", "risk", "sop", "L3", "block", "confidential", "domain", "draft_only", "K5", "risk/K5_model_monitor"),
        ScenarioProfile("remediation_tracking", "compliance", "sop", "L3", "confirm_only", "confidential", "domain", "draft_only", "C2", "compliance/C2_remediation"),
        ScenarioProfile("cross_req_align", "eng", "playbook", "L2", "confirm_only", "internal", "wide", "draft_only", "X1", "cross/X1_gray_ambiguity"),
        ScenarioProfile("unknown", "eng", "playbook", "L0", "block", "internal", "none", "none", "general", "platform/general"),
    ]


class Registry:
    def __init__(self) -> None:
        self.domains = {d.code: d for d in ORG_DOMAINS}
        self.scenarios = {s.code: s for s in default_scenarios()}

    def get_scenario(self, code: str) -> ScenarioProfile:
        if code not in self.scenarios:
            return self.scenarios["unknown"]
        return self.scenarios[code]

    def dump(self) -> dict:
        return {
            "org_domains": [d.__dict__ for d in self.domains.values()],
            "scenarios": [s.__dict__ for s in self.scenarios.values()],
        }


def load_or_default(path: Path | None = None) -> Registry:
    reg = Registry()
    if path and path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        # fixture may extend later; defaults already cover V1
        _ = data
    return reg
