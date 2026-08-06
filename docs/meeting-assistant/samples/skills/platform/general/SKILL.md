---
name: General Fallback
story_id: general
org_domain: platform
orchestration_mode: playbook
maturity_level: L0
classification: internal
continuum_write_class: none
default_embed_gate: block
production_effect_cap: none
governance_status: approved
scenario_type: unknown
---

# general｜未知场景降级 Skill Pack

## 目的

无法绑定已批准场景时的平台降级：可产只读纪要视图，**本场不 embed**，不写 Continuum 宽库。

## 成功标准

1. maturity=L0；embed_gate=block；write_class=none；cap=none  
2. Pipeline 跳过 embed（playbook skip_if）  
3. 不得宣称深嵌入已支持  
4. 引导用户会前补 scenario / 选 Skill  

## 必产 Artifact

| kind | schema |
|------|--------|
| summary_view | minutes_only@1.0.0 |

## Policy

- 唯一预置 `governance_status=approved` 的降级包（平台内置）  
- **无 sop/**  
- 禁止 discover 写回类 connectors  

## Eval

负例：L0 仍调用 embed connector。
