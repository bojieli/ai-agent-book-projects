# Domain Event 目录 — LLM Safety Platform

> 版本：v1.0 · 公共信封字段适用于所有事件

---

## 1. 公共信封

| 字段 | 必填 | 说明 |
|------|------|------|
| event_id | ✓ | |
| event_type | ✓ | 见下表 |
| occurred_at | ✓ | ISO-8601 |
| tenant_id | ✓ | |
| app_id | ✓ | |
| request_id | ✓ | 无请求上下文时用 `policy_publish_*` |
| policy_binding_id | | 有则填 |
| policy_version | | 有则填 |
| payload | ✓ | 事件体 |
| content_hash | | 涉及正文时必填 |

## 2. 事件目录

| event_type | 何时 | payload 要点 |
|------------|------|----------------|
| `safety.blocked` | 任一层 decision=block | layer, reason_codes, scanner_id? |
| `safety.redacted` | decision=redact | vault_tokens[], scanner_id |
| `safety.alert` | alert_only | reason_codes |
| `safety.confirm_required` | confirm_only | pending_action |
| `tool.denied` | L4 授权失败 / denylist / risk block | tool_id, reason, op_risk_tier?, matched_rules? |
| `tool.risk_flagged` | Classifier 识别为 medium+ 仍继续（alert/confirm） | tool_id, op_risk_tier, decision, matched_rules |
| `tool.executed` | L4 成功 | tool_id, effect, idempotency_key?, op_risk_tier |
| `policy.published` | 新 binding 版本生效 | app_id, version, reason, gate_ref |
| `eval.failed` | 发布门禁失败 | suite, defects[] |
| `eval.passed` | 门禁通过 | suite, metrics |
| `scanner.timeout` | Scanner 超时 | scanner_id, fail_mode_applied |

## 3. 投递

- Phase 0：内存 EventBus + 测试断言  
- Phase 1+：Kafka / 内网总线 → SIEMSink  
- 默认**不**在事件中携带 PII 原文（仅 hash + token 引用）
