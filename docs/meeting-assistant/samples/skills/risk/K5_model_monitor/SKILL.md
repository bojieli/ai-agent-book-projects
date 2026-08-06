---
name: K5 Model Monitor
story_id: K5
org_domain: risk
orchestration_mode: sop
maturity_level: L3
classification: confidential
continuum_write_class: domain
default_embed_gate: block
production_effect_cap: draft_only
governance_status: draft
scenario_type: model_monitor
---

# K5｜模型 / 规则表现监控会 Skill Pack

## 目的

监控会：记录指标漂移与建议动作；**禁止热切换生产模型/规则**（负例硬挡）。

## 成功标准

1. 可产出观察任务 / 回滚计划草稿  
2. 任何 hot_swap / production_enable 工具请求 → Hook 失败  
3. embed_gate=block 直至 HITL  
4. checklist `no_hot_swap` 墙  

## 必产 Artifact

| kind | schema |
|------|--------|
| metrics | model_monitor_board@1.0.0 |
| action_items | action_items@1.0.0 |

## SOP

见 `sop/steps.yaml`、`sop/checklists/no_hot_swap.yaml`。
