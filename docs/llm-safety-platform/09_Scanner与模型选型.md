# Scanner 与模型选型

> 版本：v1.0 · 延迟预算对齐 [04](./04_概要设计.md) §4

---

## 1. 分层选型原则

1. **规则优先**：Secrets regex、TokenLimit、BanSubstrings、简单 BanTopics — 同步热路径  
2. **轻量分类器**：Prompt Injection / Toxicity — ONNX/小模型，可同步  
3. **重模型**：Llama Guard 类 — 抽样或 high/critical 同步；其余异步复核  
4. **结构化**：JSON/Schema — Guardrails AI 思想，自研 SPI 实现  

## 2. Scanner 目录（平台内建）

| id | 层 | Phase0 | 生产候选 |
|----|----|--------|----------|
| token_limit | L1 | mock | tiktoken / 本地计数 |
| secrets | L1/L3 | mock regex | detect-secrets 规则集 |
| prompt_injection | L1 | **归一化 + 关键词 + decode_views**（ZW/全角/字间空格） | 专用分类器 / Prompt Guard |
| hidden_ascii | L1 | Unicode Tags 解码+注入启发式 | LlamaFirewall 对齐（ADR-024） |
| session_risk | L1 | 同 session_id 累积 crescendo/inj | 完整会话图延期（ADR-023） |
| **content_safety** | L1/L3 | **YAML 加权规则包 + 归一化打分** | Llama Guard / 行内分类器 |
| anonymize | L1 | mock regex PII+银行卡 | Presidio / 行内 NER |
| toxicity | L1/L3 | 复用 content 子集 | 多标签分类 |
| ban_topics | L1/L3 | mock 词表 | zero-shot / Rails |
| sensitive | L3 | mock | 同 anonymize 检测；**block 不展示原文** |
| output_exfil | L3 | URL/高熵外泄启发式 | 手册 §8.4.2 |
| schema | L3 | mock JSON | Guardrails 对照 |

**展示控制原理**：block → Gateway 丢弃有害原文，返回 `refusal_message` 安全话术；PII → Vault 脱敏进模型，输出再扫 Sensitive。

## 3. SafetyClassifier SPI

实现：`llm-safety-platform/app/scanners/classifier.py`  
`SAFETY_SCANNER_MODE=shim|onnx|remote|llm_guard`（默认 **shim**，CI 不依赖权重）。

- **shim**：`ContentScoreEngine` + `configs/content_rules/default.yaml`
- **onnx**：`SAFETY_ONNX_MODEL_PATH`；未配置时回退 shim
- **remote**：`SAFETY_CLASSIFIER_URL`；错误对高风险 fail-closed  
  - 推荐对接独立进程 [`workers/moderation`](../../llm-safety-platform/workers/moderation/README.md)（通用模型 LLM-as-Judge，OpenAI 兼容）
- **llm_guard**：可选 `SAFETY_LLM_GUARD_PATH`（不硬依赖 study clone；可用 moderation worker 替代）

不整仓克隆 PurpleLlama；生产通过适配器加载：

- Meta Llama Guard / Prompt Guard  
- 行内微调分类器  
- 云厂商 Moderation API（数据出境需合规评审）

## 4. 延迟预算（单请求 Scanner 合计，不含上游 LLM）

| 路径 | P50 | P99 |
|------|-----|-----|
| 规则 only | ≤10ms | ≤50ms |
| 规则 + 轻量分类 | ≤40ms | ≤200ms |
| + Llama Guard 同步 | ≤150ms | ≤500ms |

超出 → 按 `fail_mode` 降级或 block（见 ADR-006）。

## 5. 开源对照如何用

| 项目 | 用法 |
|------|------|
| llm-guard | 抄 Scanner 组合与 Vault 模式，不依赖其 `is_valid` 语义 |
| NeMo-Guardrails | Dialog Rails / 话题流控对照 |
| garak | Offline 探针 |
| promptfoo | CI 断言与回归 |
| PyRIT | 多轮对抗红队 |
| guardrails | 输出 Schema 校验模式 |
| LiteLLM | ModelProvider 路由与虚拟密钥 |

## 6. 默认推荐（金融行内）

**内容审核（ADR-020）**：**规则 + 基础 Instruct 模型（moderation worker）→ 后期同接口换微调/Guard**。

- Online：规则（必留）+ `remote`→`workers/moderation`（先通用模型）+ Vault  
- **Dual-path（ADR-029）**：`RemoteClassifier` 与 worker 均 rules∪LLM max-fuse；soft Judge 不能放宽规则命中  
- **超时**：`SAFETY_REMOTE_TIMEOUT` 本地默认 **12s**（慢 Judge 调高）；`SAFETY_REMOTE_FAIL_CLOSED=1` 建议生产/on-prem  
- critical：可提高 Judge 采样或换更大底座；仍 fail-closed  
- 后期：同一 `MODERATION_MODEL` 槽位换成安全 SFT / Llama Guard  
- Offline：garak 周扫 + PyRIT 月度 + promptfoo PR 门禁；`run_all` 含 handbook/OSS corpus shim gates  
- CI：始终 `SAFETY_SCANNER_MODE=shim`