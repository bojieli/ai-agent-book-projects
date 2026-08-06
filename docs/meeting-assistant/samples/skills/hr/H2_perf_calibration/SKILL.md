---
name: H2 Performance Calibration
story_id: H2
org_domain: hr
orchestration_mode: playbook
maturity_level: L2
classification: critical
continuum_write_class: sealed
default_embed_gate: block
production_effect_cap: none
governance_status: draft
scenario_type: perf_calibration
delivery_scope: allowlist_only
---

# H2｜绩效校准 Skill Pack

## 目的

绩效校准：结构化校准结论仅对 **allowlist** 角色可见；**禁群发 / 禁宽 Continuum / 禁自动通知全员**。

## 成功标准

1. classification=critical；write_class=sealed  
2. embed_gate=block；production_effect_cap=none（本场不写生产人事生效）  
3. render：无 allowlist → render.skipped；有则仅候选收件人  
4. 不得把个人绩效细节写入 wide Continuum  

## 必产 Artifact

| kind | schema |
|------|--------|
| verdict | calibration_notes@1.0.0 |

## Policy

- playbook；无 sop/  
- delivery_scope=allowlist_only；notify 默认 suppressed unless allowlist  
- tool_allowlist 空或仅 HR 台账草稿（仍须 HITL；cap=none 则 skip embed）

## Eval

负例：群发、宽检索、误入 Continuum 宽库、自动全员通知。
