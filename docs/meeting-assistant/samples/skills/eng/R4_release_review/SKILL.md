---
name: R4 Release Review
story_id: R4
org_domain: eng
orchestration_mode: sop
maturity_level: L3
classification: confidential
continuum_write_class: wide
default_embed_gate: confirm_only
production_effect_cap: draft_only
governance_status: draft
# promote to approved only after eval green
---

# R4｜发布评审 Skill Pack

## 目的

技术发布 / 变更评审会：给出明确 **Go / No-Go / 有条件 Go**，对照 Continuum 上次条件项与发布清单文档，确认后写入变更系统草稿（不对生产自动生效）。

## 成功标准

1. `verdict.payload.go_nogo` 三选一且有依据 citation  
2. 有条件时拆成可跟踪 action_items，并回链 source_spans  
3. 上次未关闭条件项被召回；不得假装「全新通过」  
4. checklist Hook 全绿前不得 embed  
5. `production_effect` 实际等级 ≤ `draft_only`

## 必产 Artifact

| kind | schema | 说明 |
|------|--------|------|
| verdict | release_verdict@1.0.0 | Go/No-Go |
| action_items | action_items@1.0.0 | 条件项/跟进 |
| summary_view | （Render 用） | 可读摘要，非真相源 |

## Policy

- embed_gate 至少 `confirm_only`  
- production_effect_cap = `draft_only`  
- 工具 allowlist：变更系统草稿 Connector、任务系统；禁止生产发布开关类工具  

## SOP

见 `sop/steps.yaml` 与 `sop/checklists/release_gate.yaml`。

## Eval

见 `eval/`：正例召回上次条件；负例跳过 checklist、未确认生产生效。
