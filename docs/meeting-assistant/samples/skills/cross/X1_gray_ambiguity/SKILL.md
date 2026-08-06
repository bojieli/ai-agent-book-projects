---
name: X1 Gray Ambiguity
story_id: X1
org_domains: [business, eng]
orchestration_mode: playbook
maturity_level: L2
classification: internal
continuum_write_class: wide
default_embed_gate: confirm_only
production_effect_cap: draft_only
governance_status: draft
scenario_type: cross_req_align
---

# X1｜业务 × 科技需求对齐（灰度消歧）Skill Pack

## 目的

跨域同词异义（如「灰度」= 发布灰度 vs 客群灰度）：必须打开 `ambiguity_record` 并裁决，**未决不得自动 embed**，禁止写成「各方同意」糊弄过关。

## 成功标准

1. 检测到跨域歧义术语 → `ambiguity.opened`  
2. 未 `ambiguity.resolved` 前 embed_gate 至少升至 confirm_only，建议 block 自动写回  
3. 分域产物可拆：业务侧 / 科技侧语义分别落 references  
4. 负例：「消歧未决却各方同意」必须 fail evaluate  

## 必产 Artifact

| kind | schema |
|------|--------|
| verdict | disambiguation_ruling@1.0.0 |
| action_items | action_items@1.0.0 |

## Policy

- playbook；可绑定多 Skill（meeting_skill_binding primary/secondary）  
- **无 sop/**  
- 消歧未决 → 禁止 work embed  

## Eval

正例：Cards + 历史会用法消歧；负例：未决写「各方同意」。
