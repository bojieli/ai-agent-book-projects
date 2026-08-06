---
name: R5 Delivery Sync
story_id: R5
org_domain: eng
orchestration_mode: playbook
maturity_level: L2
classification: internal
continuum_write_class: wide
default_embed_gate: confirm_only
production_effect_cap: draft_only
governance_status: draft
scenario_type: delivery_sync
---

# R5｜交付周会 Skill Pack

## 目的

管理向交付同步：里程碑红灯、阻塞、下周承诺；会前 Continuum **必须召回 open 阻塞**。

## 成功标准

1. retrieve Continuum open 阻塞；不得假装「本周从零」  
2. 里程碑状态变更建议可写回交付看板草稿  
3. 执行层新缺陷须拆成独立 action，不与管理状态混散文  
4. production_effect ≤ draft_only  

## 必产 Artifact

| kind | schema |
|------|--------|
| metrics | milestone_board@1.0.0 |
| action_items | action_items@1.0.0 |

## Policy

- playbook；retrieve 对 series_id **不可跳过**（本场景 override）  
- 无 sop/

## Eval

正例：召回上次未关闭阻塞；负例：跳过 Continuum 仍标全绿。
