# COMPLETION — L3 生产验收清单

> Production Cut **v2.4** · 目标成熟度 **L3**（见 [06](./06_控制成熟度与发布门禁.md)）  
> 状态：**脱敏重建 · on-prem blocked；local harden + 事实源收口 done** · 2026-08-06

**诚实边界**：本仓为生产架构脱敏重建；离线 shim/static 语料 0 leak/FP **不等于** 生产线上零事故。行内 IdP/KMS/GPU、完整 garak/PyRIT、远程 Judge 矩阵需凭据外置。

---

## A. Gateway 与 API

- [x] FastAPI Safety Gateway 可启动；`GET /healthz` 返回存活
- [x] `POST /v1/safety/chat` 端到端（L1→L2→ModelProxy→L3→L4）；支持 `session_id`
- [x] `POST /v1/safety/scan` 仅扫描不调模型
- [x] `POST /v1/chat/completions` OpenAI-compatible 且走同一护栏
- [x] `POST /v1/tools/execute` 唯一侧效路径（ADR-008）
- [x] 统一决策五态；SafetyDecision 信封符合 07

## B. 数据面（ADR-012）

- [x] PostgreSQL 持久化表模型 + `migrations/001_init.sql`（本地/CI 默认 SQLite 同契约）
- [x] Redis 限流（无 Redis 时内存降级）与 VK budget；可选 session store
- [x] migrations + `deploy/docker-compose.yml` 一键起 PG+Redis+Gateway

## C. 鉴权与治理（ADR-013 / ADR-015 / ADR-025）

- [x] Virtual Keys：创建、哈希存储、鉴权、吊销；上游 Key 不下发
- [x] OIDC：JWKS JWT 校验；`OIDC_REQUIRED=1` fail-closed；本地默认 admin token
- [x] RBAC：Admin / Security / AppOwner / Auditor 权限边界可测
- [x] Admin API：policies / virtual-keys / audit / dashboard / chain verify
- [x] 第二租户示例：`t_bank_retail` / `wealth_assistant` + `scripts/smoke_business_vk.sh`

## D. 防护与 Vault（ADR-026）

- [x] Scanner 模式 `shim|onnx|remote`（CI 默认 shim；onnx 适配位）
- [x] Encrypted Vault AES-GCM；KMS SPI `env|file|aws_kms_stub|http_kms`
- [x] high/critical fail-closed（策略校验强制）
- [x] ModelProxy 多上游路由 / failover / token 记账元数据

## E. HITL 与 Tool

- [x] confirm_only → ApprovalWorkbench 排队
- [x] `/v1/approvals*` approve/deny；approve 后 resume 执行
- [x] tool allowlist + effect_cap + MCP 工具过滤
- [x] tool_denylist + 平台硬禁（黑名单优先白名单，ADR-019）
- [x] ToolRiskClassifier 参数级危险操作识别；全量工具审计 / tool.risk_flagged

## F. Offline 与发布（ADR-009 / ADR-018 / ADR-028）

- [x] `/v1/redteam/run` + `/v1/redteam/runs`；报告入库
- [x] ReleaseEvaluator：failed 时 publish API 拒绝
- [x] critical 双人签字（缺审批人则 awaiting_dual_approval）
- [x] policy_binding 只追加
- [x] `python -m app.eval.run_all`（shim）全绿
- [x] `REDTEAM_EXTERNAL=1` 真 subprocess（timeout + JSON ingest + gate）；CI 默认 shim

## G. 可观测与合规（ADR-017）

- [x] 每请求 audit_decisions + hash_chain append
- [x] `/v1/admin/audit/chain/verify`（graph 拓扑重建；fork/断链 fail-closed；非 id 序）
- [x] 启动 hydrate 前验证；损坏链 readyz 503 + 禁止续写
- [x] `migrations/002` 幂等补 chain 列 + **legacy 行回填**（`backfill_audit_chain_hashes`）
- [x] publish profile 各门 enabled/blocking + gates_audit
- [x] critical 最终批准前重跑 publish gates
- [x] `corpus_metrics.py` YAML 计算 SoT
- [x] remote Judge FN/FP/drift 分项 + URL 脱敏
- [ ] 多副本 audit chain — **single-writer 脱敏重建；生产需 advisory lock**（未假勾）
- [x] Prometheus `/metrics` + OTel span recorder
- [x] SIEMSink SPI（`log|http|file`）发 hash-chain 事件（含 `chain_hash`/`prev_chain_hash`）

## H. 控制台与部署（ADR-016）

- [x] Governance Console（`/console/` 静态 SPA + Vite/React 源码）
- [x] `deploy/docker-compose.yml` + `docker-compose.onprem.yml`
- [x] Helm chart + `values-onprem.yaml`（moderation Deployment 可选）
- [x] 延迟目标写入 HLD；规则路径以 shim 度量

## I. 故事回归（见 06）

- [x] S1 注入 / S2 PII / S3 Tool deny / S5 BanTopics / S6 Token / S7 策略追加 + 间接注入（shim 红队套件）

## J. OSS / 手册纵深（v2.3–v2.4 · ADR-021..029）

- [x] Spotlight datamark（`app/gateway/spotlight.py`）
- [x] `hidden_ascii` + `decode_views`（含 hex）+ L3 `output_exfil`（markdown/data-uri）
- [x] 会话图 + role-drift / crescendo（`session_store` + `session_risk`）
- [x] Dual-LLM opt-in MVP（unsigned/replay/analyzer-injection 边角；ADR-027）
- [x] `external_runners` 真 subprocess + dry-run 嵌入 `multiturn_shim`（不 import study）
- [x] 语料：`handbook_v1_full` / `oss_*`；`run_all` corpus shim gates（ADR-029）
- [x] publish profile 显式配置（`configs/evals/publish_profile.yaml`；默认 dual_gate:ci）
- [x] dual_gate ci/release/full 报告与指标 SoT 一致（2500/2400/310/410/600）
- [x] remote Judge compare 入口（无 URL skip；`remote_judge_compare.json`）
- [x] Flames fairness + PurpleLlama CSE 规则/Judge 加深 + dual-path fuse（见 WORKLOG v2.4）
- [ ] AlignmentCheck 全量 LLM trace — **deferred**（ADR-024）
- [ ] 真银行 IdP / 真 AWS KMS / 真 on-prem GPU — **external / blocked**（适配器齐，凭据外置；本地硬化已做）

---

**DoD**：上表 A–I 已勾 + compose/Helm 齐 + `run_all`（含 corpus gates + release dual_gate）shim 全绿；J 中 deferred/external 不得假勾。  
**诚实状态**：脱敏重建；on-prem 阻塞；local harden + 事实源/审计链/publish profile 已完成。
