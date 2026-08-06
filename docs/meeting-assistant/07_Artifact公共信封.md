# Artifact 公共信封（契约 + JSON Schema）

> 版本：v1.0 · 对齐架构 **v7.7** §2.13 · 详细设计 **05**  
> 每条产物必须套本信封；场景差异只在 `payload`。

---

## 1. 字段规范

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| artifact_id | string | ✓ | 稳定 ID |
| meeting_id | string | ✓ | |
| org_domains | string[] | ✓ | eng/business/hr/risk/compliance |
| scenario_type | string | ✓ | |
| skill_pack_id | string | ✓ | 产物归属 Pack |
| artifact_kind | string | ✓ | decision\|action_items\|risks\|verdict\|metrics\|draft\|… |
| schema_id | string | ✓ | payload 的 schema 名 |
| schema_version | string | ✓ | semver |
| payload | object | ✓ | 场景体 |
| confidence | number\|string | ✓ | 0..1 或 low\|med\|high |
| unresolved | array | ✓ | 可空数组；未决不得装已决 |
| source_spans | array | ✓ | `{start_ms?, end_ms?, quote?, doc_id?}` |
| references | array | ✓ | `{corpus:docs\|continuum, id, span?}` |
| chart_series | array | | 仅事实序列；Render 只读此或 payload 声明字段 |
| classification | string | ✓ | |
| continuum_write_class | string | ✓ | wide\|domain\|sealed\|none |
| created_by_stage | string | ✓ | understand\|artifact\|hitl_patch\|… |

**铁律：** 缺信封字段 → Evaluator / Render **拒绝**；图表缺数 → 显示「数据不足」，禁止补造。

---

## 2. JSON Schema（Draft 2020-12）

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://jiyaojun.local/schemas/artifact_envelope.json",
  "title": "ArtifactEnvelope",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "artifact_id", "meeting_id", "org_domains", "scenario_type", "skill_pack_id",
    "artifact_kind", "schema_id", "schema_version", "payload", "confidence",
    "unresolved", "source_spans", "references", "classification",
    "continuum_write_class", "created_by_stage"
  ],
  "properties": {
    "artifact_id": { "type": "string", "minLength": 1 },
    "meeting_id": { "type": "string", "minLength": 1 },
    "org_domains": {
      "type": "array",
      "minItems": 1,
      "items": { "enum": ["eng", "business", "hr", "risk", "compliance"] }
    },
    "scenario_type": { "type": "string", "minLength": 1 },
    "skill_pack_id": { "type": "string", "minLength": 1 },
    "artifact_kind": {
      "type": "string",
      "enum": ["decision", "action_items", "risks", "verdict", "metrics", "draft", "summary_view", "other"]
    },
    "schema_id": { "type": "string" },
    "schema_version": { "type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$" },
    "payload": { "type": "object" },
    "confidence": {
      "oneOf": [
        { "type": "number", "minimum": 0, "maximum": 1 },
        { "enum": ["low", "med", "high"] }
      ]
    },
    "unresolved": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["code", "message"],
        "properties": {
          "code": { "type": "string" },
          "message": { "type": "string" },
          "blocking_embed": { "type": "boolean", "default": true }
        }
      }
    },
    "source_spans": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "start_ms": { "type": "integer", "minimum": 0 },
          "end_ms": { "type": "integer", "minimum": 0 },
          "quote": { "type": "string" },
          "doc_id": { "type": "string" }
        }
      }
    },
    "references": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["corpus", "id"],
        "properties": {
          "corpus": { "enum": ["docs", "continuum", "transcript"] },
          "id": { "type": "string" },
          "span": { "type": "string" }
        }
      }
    },
    "chart_series": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["series_id", "label", "points"],
        "properties": {
          "series_id": { "type": "string" },
          "label": { "type": "string" },
          "unit": { "type": "string" },
          "points": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["x", "y"],
              "properties": {
                "x": { "type": ["string", "number"] },
                "y": { "type": "number" }
              }
            }
          }
        }
      }
    },
    "classification": {
      "enum": ["public", "internal", "confidential", "critical"]
    },
    "continuum_write_class": {
      "enum": ["wide", "domain", "sealed", "none"]
    },
    "created_by_stage": {
      "enum": ["understand", "artifact", "hitl_patch", "system"]
    }
  }
}
```

机器可读副本：[samples/schemas/artifact_envelope.json](./samples/schemas/artifact_envelope.json)

---

## 3. 示例（R4 verdict 片段）

见 [samples/skills/eng/R4_release_review/examples/verdict_envelope.json](./samples/skills/eng/R4_release_review/examples/verdict_envelope.json)
