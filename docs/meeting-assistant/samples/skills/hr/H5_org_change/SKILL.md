---
name: H5 Org Change Analysis
story_id: H5
org_domain: hr
orchestration_mode: playbook
maturity_level: L2
classification: critical
continuum_write_class: sealed
default_embed_gate: block
production_effect_cap: none
governance_status: draft
scenario_type: org_change
delivery_scope: allowlist_only
---

# H5｜减员 / 组织调整分析 Skill Pack

## 目的

极高敏组织调整分析（见 03 §3.4）：方案版本与决策状态清楚；下一步仅授权角色；**禁群发、禁宽检索、禁自动通知、禁误入 Continuum 宽库**。

## 成功标准

1. critical + sealed + block + cap=none  
2. 无 allowlist → render.skipped + delivery.suppressed  
3. 不得把名单细节写入 wide/domain 可检索面  
4. 未授权角色看不到 payload 明细（acl_view 空则 skip）  

## 必产 Artifact

| kind | schema |
|------|--------|
| draft | org_change_analysis@1.0.0 |

## Policy

- playbook；无 sop/  
- 与 H2 同 critical 模板；额外负例见 03 §5 H5_org_change  

## Eval

负例：群发、宽检索、自动通知、误入 Continuum 宽库。
