---
name: C2 Remediation Tracking
story_id: C2
org_domain: compliance
orchestration_mode: sop
maturity_level: L3
classification: confidential
continuum_write_class: domain
default_embed_gate: confirm_only
production_effect_cap: draft_only
governance_status: draft
---

# C2｜整改推进会 Skill Pack

## 目的

跨会推进检查整改项：会前 Continuum 拉未关闭项，会后更新结构化状态；**「完成」必须绑定证据 citation**，不能口头「差不多了」。

## 成功标准

1. 会前 briefing 召回本系列 open 整改项  
2. 每条状态变更有 source_spans 或证据 references  
3. status=done 时 references 必含证据对象（docs 或附件 ID）  
4. checklist Hook 挡住「无证据标完成」  
5. 写回整改台账后可 work_link.synced  

## 必产 Artifact

| kind | schema | 说明 |
|------|--------|------|
| metrics | remediation_board@1.0.0 | 整改项状态板 |
| action_items | action_items@1.0.0 | 新增/变更动作 |

## Policy

- embed_gate = confirm_only  
- continuum write_class = domain  
- 「完成」无证据 → evaluate/checklist 失败，不得 embed 该条  

## SOP

见 `sop/steps.yaml`、`sop/checklists/evidence_required.yaml`。

## Eval

正例：跨会连续体召回；负例：无证据标完成、跳过 checklist。
