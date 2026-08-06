---
name: 薪酬沟通会
story_id: H3
org_domain: hr
org_domains: ["hr"]
orchestration_mode: playbook
maturity_level: L2
classification: critical
continuum_write_class: sealed
default_embed_gate: block
production_effect_cap: none
governance_status: draft
scenario_type: comp_review
backlog: true
# 待行内真实 SOP 入库后再升 L3/sop；禁止空壳 steps.yaml
---

# H3｜薪酬沟通会（后续上线 Stub）

## 目的

契约占位 Skill Pack（06 §3）。**governance=draft**，不得进生产 Pipeline。

## 成功标准

1. 产出带 ArtifactEnvelope 的结构化笔记  
2. 遵守 classification / write_class / embed_gate  
3. 无真实行内 SOP 前保持 playbook（禁止捏造 sop/）

## 必产 Artifact

| kind | schema |
|------|--------|
| summary_view / draft | stub_notes@1.0.0 |

## Eval

负例：draft 包被生产加载；critical 写入 wide。
