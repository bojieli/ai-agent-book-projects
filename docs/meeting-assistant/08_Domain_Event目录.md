# Domain Event 目录（权威）

> 版本：v1.0 · 对齐架构 **v7.7** §2.14 · 详细设计 **05** §3  
> 跨平面通信优先事件；大对象只传 ID。

---

## 1. 公共信封

所有事件载荷外层：

```json
{
  "event_id": "uuid",
  "event_type": "transcript.ready",
  "occurred_at": "2026-08-03T10:00:00+08:00",
  "trace_id": "…",
  "meeting_id": "…",
  "pipeline_run_id": null,
  "producer": "transcript-adapter",
  "payload": {}
}
```

持久化表：`domain_event`（见 05）。

---

## 2. 事件一览

| event_type | 生产者 | 主要消费者 | payload 要点 |
|------------|--------|------------|--------------|
| `meeting.scheduled` | Schedule | Knowledge | `series_id?`, `project_id?`, `org_domains`, `skill_pack_ids` |
| `transcript.ready` | 转写 Adapter | Pipeline | `transcript_document_id`, `object_key` |
| `understanding.completed` | Understanding | Orchestrator / Policy | `quality`, `unknown_terms[]`, `blocks_decision: bool` |
| `ambiguity.opened` | Disambiguator | Policy | `ambiguity_record_id`, `term`, `effect_on_embed_gate` |
| `ambiguity.resolved` | Disambiguator / HITL | Policy | `ambiguity_record_id`, `resolved_sense`, `resolver_user_id` |
| `artifact.persisted` | Artifact | Evaluator / HITL | `artifact_ids[]` |
| `evaluation.passed` | Evaluator | Orchestrator | `eval_run_id`, `checks[]` |
| `evaluation.failed` | Evaluator | Orchestrator | `eval_run_id`, `failures[]` → **不得 embed** |
| `hitl.requested` | Orchestrator | Dialog | `task_id`, `kind`, `deadline?` |
| `hitl.resolved` | Dialog | Pipeline | `task_id`, `decision`, `patch?` |
| `work_link.submitted` | WorkEmbed | 审计 | `work_object_id`, `idempotency_key` |
| `work_link.synced` | Connector 回流 | Continuum / Dialog | `work_object_id`, `status`, `external_id` |
| `continuum.write_decided` | Knowledge | 审计 / Eval | `write_class`, `receipt_id`, `rejected_reason?` |
| `render.completed` | Render | Delivery | `render_job_id`, `acl_view_id`, `artifact_ids[]` |
| `render.skipped` | Render | 审计 | `reason`: no_acl_view \| critical_no_allowlist \| empty_view \| … |
| `delivery.sent` | Delivery | 审计 | `channel`, `recipient_set_hash`, `render_job_id` |
| `delivery.suppressed` | Delivery / Render | 审计 | `reason`: critical_policy \| empty_view \| … |
| `pipeline.terminal` | Pipeline | Dialog | `terminal`, `budget_used` |
| `budget.exhausted` | Pipeline / Knowledge | Orchestrator | `which`: llm\|retrieve\|wall_clock\|… |
| `policy_binding.updated` | Policy | 审计 | `policy_binding_id`, `version`, `reason` |

---

## 3. 载荷示例

### 3.1 `transcript.ready`

```json
{
  "transcript_document_id": "td_001",
  "object_key": "s3://…/transcript.json",
  "hotword_profile_id": "eng_default",
  "segment_count": 120
}
```

### 3.2 `evaluation.failed`

```json
{
  "eval_run_id": "er_9",
  "failures": [
    { "code": "missing_go_nogo", "message": "verdict.payload.go_nogo 缺失" },
    { "code": "unresolved_blocking", "message": "存在 blocking_embed 未决项" }
  ]
}
```

### 3.3 `continuum.write_decided`

```json
{
  "write_class": "sealed",
  "receipt_id": "cwr_12",
  "index_alias": "continuum_sealed_hr",
  "rejected_reason": null
}
```

### 3.4 `render.skipped`

```json
{
  "reason": "critical_no_allowlist",
  "classification": "critical",
  "render_job_id": "rj_3"
}
```

### 3.5 `pipeline.terminal`

```json
{
  "terminal": "awaiting_hitl",
  "budget_used": {
    "llm_calls": 12,
    "retrieve_hops": 2,
    "wall_clock_sec": 180
  }
}
```

---

## 4. 队列映射（与 05 一致）

| Topic | 典型事件 |
|-------|----------|
| `ma.transcript.ready` | transcript.ready |
| `ma.pipeline.step` | 内部步进（可选） |
| `ma.render.requested` | 触发 render（由 pipeline 发出） |
| `ma.connector.sync` | → work_link.synced |
| `ma.domain.event` | 全量投影 / 审计 |

分区键优先 `meeting_id`。

---

## 5. 兼容性

- 新增 `event_type` 必须先改本目录 + 03 §2.14 + 枚举测试。  
- payload 只增不改语义；破坏性变更升 major 并双写过渡期。
