# SafetyDecision 公共信封

> 版本：v1.0 · 对齐架构 **v1.0** §7 · DLD [05](./05_详细设计.md)  
> 每次 Gateway 处理至少产出一条；缺必填字段 → Evaluator **拒绝**。

---

## 1. 字段规范

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| decision_id | string | ✓ | 稳定 ID |
| request_id | string | ✓ | 请求根 ID |
| tenant_id | string | ✓ | |
| app_id | string | ✓ | |
| policy_binding_id | string | ✓ | |
| policy_version | integer | ✓ | |
| risk_tier | string | ✓ | low\|medium\|high\|critical |
| layer | string | ✓ | L1\|L2\|L3\|L4\|gateway |
| decision | string | ✓ | allow\|redact\|block\|confirm_only\|alert_only |
| reason_codes | string[] | ✓ | 可空数组 |
| scanner_results | array | ✓ | `{scanner_id, decision, risk_score, reasons[]}` |
| content_hash | string | ✓ | 对规范化后输入做 sha256；无正文时用空串哈希 |
| retention | string | ✓ | hash_only\|encrypted_full\|none |
| latency_ms | number | ✓ | |
| created_at | string | ✓ | ISO-8601 |

**铁律：** `decision=block` 时不得附带未脱敏的敏感 `model_output` 给不可信调用方。

## 2. JSON Schema（Draft 2020-12）

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://llm-safety.local/schemas/safety_decision.json",
  "title": "SafetyDecision",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "decision_id", "request_id", "tenant_id", "app_id",
    "policy_binding_id", "policy_version", "risk_tier", "layer",
    "decision", "reason_codes", "scanner_results", "content_hash",
    "retention", "latency_ms", "created_at"
  ],
  "properties": {
    "decision_id": { "type": "string", "minLength": 1 },
    "request_id": { "type": "string", "minLength": 1 },
    "tenant_id": { "type": "string", "minLength": 1 },
    "app_id": { "type": "string", "minLength": 1 },
    "policy_binding_id": { "type": "string", "minLength": 1 },
    "policy_version": { "type": "integer", "minimum": 1 },
    "risk_tier": { "type": "string", "enum": ["low", "medium", "high", "critical"] },
    "layer": { "type": "string", "enum": ["L1", "L2", "L3", "L4", "gateway"] },
    "decision": {
      "type": "string",
      "enum": ["allow", "redact", "block", "confirm_only", "alert_only"]
    },
    "reason_codes": { "type": "array", "items": { "type": "string" } },
    "scanner_results": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["scanner_id", "decision", "risk_score", "reasons"],
        "properties": {
          "scanner_id": { "type": "string" },
          "decision": {
            "type": "string",
            "enum": ["allow", "redact", "block", "confirm_only", "alert_only"]
          },
          "risk_score": { "type": "number", "minimum": 0, "maximum": 1 },
          "reasons": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "content_hash": { "type": "string", "minLength": 1 },
    "retention": { "type": "string", "enum": ["hash_only", "encrypted_full", "none"] },
    "latency_ms": { "type": "number", "minimum": 0 },
    "created_at": { "type": "string", "minLength": 1 }
  }
}
```

样例文件：[`samples/safety_decision.schema.json`](./samples/safety_decision.schema.json)

### 2.1 哈希链扩展字段（审计 / SIEM）

持久化 `audit_decisions` 与 SIEM 事件可携带：

| 字段 | 说明 |
|------|------|
| `chain_hash` | 当前决策在链上的 SHA-256 |
| `prev_chain_hash` | 前一链接哈希（首条为 `GENESIS`） |

跨进程验证：`GET /v1/admin/audit/chain/verify` 按 **graph 拓扑**（`prev_chain_hash→chain_hash`）重建，不依赖 DB 自增 id 序。损坏链：readyz 503、禁止续写。

**single-writer 边界**：脱敏重建与 legacy 回填默认单进程 writer；生产多副本需 Postgres `pg_advisory_lock` 或专用 audit writer 分区（回填与续写均须同锁）。

## 3. 归约到 gateway 决策

多 Scanner 结果按 max_strict 归约后写入顶层 `decision`；`layer=gateway` 表示整单最终决策。
