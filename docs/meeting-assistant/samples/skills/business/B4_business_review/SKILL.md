---
name: B4 Business Review
story_id: B4
org_domain: business
orchestration_mode: playbook
maturity_level: L2
classification: confidential
continuum_write_class: domain
default_embed_gate: confirm_only
production_effect_cap: draft_only
governance_status: draft
scenario_type: business_review
---

# B4｜经营复盘 Skill Pack

## 目的

漏斗/客群经营复盘：对照上期 Continuum 经营动作，产出带 **chart_series** 的指标板与跟进动作（草稿）。

## 成功标准

1. 上期经营动作被召回  
2. chart_series 来自结构化经营指标，禁止臆造数字  
3. 跟进动作确认后写任务/看板草稿  
4. write_class=domain  

## 必产 Artifact

| kind | schema |
|------|--------|
| metrics | funnel_review@1.0.0（含 chart_series） |
| action_items | action_items@1.0.0 |

## Policy

- playbook；无 sop/  
- Render 绑 charts.yaml；数据只来自 Artifact.chart_series  

## Eval

正例：上期动作召回 + chart 绑定；负例：臆造转化率。
