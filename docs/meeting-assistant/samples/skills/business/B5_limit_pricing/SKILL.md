---
name: B5 Limit Pricing Review
story_id: B5
org_domain: business
orchestration_mode: sop
maturity_level: L3
classification: confidential
continuum_write_class: domain
default_embed_gate: block
production_effect_cap: draft_only
governance_status: draft
scenario_type: limit_pricing_review
---

# B5｜额度 / 定价策略业务评审 Skill Pack

## 目的

额度/定价上线前业务评审：只产出**建议草稿**；**禁止**对生产额度/定价系统自动生效。

## 成功标准

1. recommended_action ∈ {hold, pilot_draft, reject}，不得 production_enable  
2. HITL 责任人确认前 embed_gate 保持 block  
3. no_production_effect checklist 全绿  
4. 引用策略/制度 docs  

## 必产 Artifact

| kind | schema |
|------|--------|
| draft | limit_pricing_draft@1.0.0 |
| risks | risks@1.0.0 |

## Policy

- embed_gate=block；cap=draft_only  
- 工具 allowlist：草稿；禁生产生效 API  

## SOP

见 `sop/steps.yaml`、`sop/checklists/no_production_effect.yaml`。
