---
name: K1 Policy Review
story_id: K1
org_domain: risk
orchestration_mode: sop
maturity_level: L3
classification: confidential
continuum_write_class: domain
default_embed_gate: block
production_effect_cap: draft_only
governance_status: draft
---

# K1｜策略评审会（上线前）Skill Pack

## 目的

风控策略上线前评审：明确 Shadow / 灰度 / 回滚与观察指标，产出**策略变更草稿或观察任务**；**禁止**因一句「那就先上吧」对生产策略自动生效。

## 成功标准

1. 建议动作 ∈ {shadow, gray, hold, rollback_plan_only}，不得默认为 production  
2. 策略说明文档被引用（references 含 docs）  
3. `production_effect` 实际等级 ≤ `draft_only`；生产生效类工具不可 discover  
4. HITL 责任人确认前不得 embed  
5. 未决项（样本不足、误杀基线不清）标 `unresolved`，不得写成已批准上线  

## 必产 Artifact

| kind | schema | 说明 |
|------|--------|------|
| draft | policy_change_draft@1.0.0 | 策略变更草稿建议 |
| action_items | action_items@1.0.0 | 观察/补数任务 |
| risks | risks@1.0.0 | 误杀/漏放风险 |

## Policy

- default_embed_gate = **block**（确认后升 confirm_only 仅对草稿 Connector）  
- production_effect_cap = **draft_only**  
- tool_allowlist：策略草稿、观察任务；**禁止**生产策略热切换 / 全量生效 API  
- continuum write_class = domain  

## SOP

见 `sop/steps.yaml`、`sop/checklists/no_production_effect.yaml`。

## Eval

正例：只写草稿；负例：未确认生产生效、跳过禁令 Hook。
