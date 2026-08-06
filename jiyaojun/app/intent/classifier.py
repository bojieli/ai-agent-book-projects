"""Intent: map natural language / calendar hint → scenario + org_domains."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain_layer.registry import Registry, load_or_default


@dataclass
class IntentResult:
    scenario_code: str
    org_domains: list[str]
    confidence: float
    hints_matched: list[str]


# keyword → scenario (ordered; first match wins among domain groups)
_RULES: list[tuple[list[str], str, list[str]]] = [
    (["发布", "go/no-go", "变更评审", "上线评审"], "release_review", ["eng"]),
    (["交付周会", "里程碑", "红灯", "燃尽"], "delivery_sync", ["eng"]),
    (["需求", "澄清", "接口", "超时", "评审技术方案"], "tech_review", ["eng"]),
    (["经营", "漏斗", "客群复盘"], "business_review", ["business"]),
    (["额度", "定价"], "limit_pricing_review", ["business"]),
    (["绩效", "校准"], "perf_calibration", ["hr"]),
    (["减员", "组织调整", "编制优化"], "org_change", ["hr"]),
    (["策略评审", "shadow", "误杀"], "risk_policy_review", ["risk"]),
    (["模型监控", "psi", "热切换"], "model_monitor", ["risk"]),
    (["整改", "台账", "迎检"], "remediation_tracking", ["compliance"]),
    (["灰度", "业务对齐", "科技对齐"], "cross_req_align", ["eng", "business"]),
]


class IntentClassifier:
    def __init__(self, registry: Registry | None = None) -> None:
        self.registry = registry or load_or_default()

    def classify(self, text: str, calendar_title: str | None = None) -> IntentResult:
        blob = f"{calendar_title or ''} {text}".lower()
        matched: list[str] = []
        for keywords, scenario, domains in _RULES:
            for kw in keywords:
                if kw.lower() in blob:
                    matched.append(kw)
                    # HR default high sensitivity applied at schedule time
                    return IntentResult(scenario, domains, 0.85, matched)
        return IntentResult("unknown", ["eng"], 0.2, [])
