---
name: 技术治理会
story_id: R7
org_domain: eng
org_domains: ["eng"]
orchestration_mode: playbook
maturity_level: L2
classification: confidential
continuum_write_class: domain
default_embed_gate: confirm_only
production_effect_cap: draft_only
governance_status: draft
scenario_type: tech_governance
backlog: true
# 待行内真实 SOP 入库后再升 L3/sop；禁止空壳 steps.yaml
---

# R7｜技术治理会（后续上线 Stub）

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
