---
name: R1 Requirement Sync
story_id: R1
org_domain: eng
orchestration_mode: playbook
maturity_level: L2
classification: internal
continuum_write_class: wide
default_embed_gate: confirm_only
production_effect_cap: draft_only
governance_status: draft
scenario_type: tech_review
---

# R1｜需求澄清 / 同步 Skill Pack

## 目的

科技侧需求澄清：抽出可跟踪行动项与开放问题，确认后写入任务系统草稿（非生产变更）。

## 成功标准

1. action_items 每条有 owner 或显式 unresolved  
2. 开放问题不得伪装成已决议  
3. 确认后可建任务草稿；`production_effect` ≤ draft_only  
4. references/source_spans 可回溯转写  

## 必产 Artifact

| kind | schema |
|------|--------|
| action_items | action_items@1.0.0 |
| summary_view | （Render） |

## Policy

- 走 Default Playbook；本包可收紧 HITL，不得删 schema_validate / policy_hooks / evaluate  
- **无 sop/**（禁止空壳 SOP）

## Eval

正例：行动项→任务；负例：未确认 embed、开放问题写成决议。
