# LLM Safety Platform（内容安全中台）v2.0 Production Cut

企业级 LLM 安全控制面：Gateway · 虚拟密钥 · 四层护栏 · 加密 Vault · ModelProxy · HITL · 红队门禁 · 治理控制台 · Helm。

## 权威设计

[`docs/llm-safety-platform/`](../docs/llm-safety-platform/)（**03 为架构 SoT**）· 验收 [`COMPLETION.md`](../docs/llm-safety-platform/COMPLETION.md)

## 本地开发（shim，无需外网模型）

```bash
cd llm-safety-platform
uv venv .venv && uv pip install -r requirements.txt
.venv/bin/python -m app.eval.run_all
.venv/bin/uvicorn app.api.main:app --port 8080
# 控制台: http://127.0.0.1:8080/console/
# Admin: Authorization: Bearer admin-dev-token
```

## 通用模型审核（LLM-as-Judge worker）

用任意 OpenAI 兼容模型做内容分类，替代 llm-guard：

```bash
# 终端 1：审核 worker（无上游时 MODERATION_MOCK=1 走规则）
MODERATION_MOCK=1 .venv/bin/uvicorn workers.moderation.app:app --port 8091

# 终端 2：Gateway 走 remote
SAFETY_SCANNER_MODE=remote \
SAFETY_CLASSIFIER_URL=http://127.0.0.1:8091/v1/classify \
.venv/bin/uvicorn app.api.main:app --port 8080
```

详见 [`workers/moderation/README.md`](workers/moderation/README.md)。

### OpenAI-compatible 商业模型配置

商业模型地址、凭据和模型名统一使用 `MODEL_BASE_URL`、`MODEL_API_KEY`、`MODEL_NAME`（也支持 `SAFETY_MODEL_*` 覆盖）。默认空值继续使用离线确定性模型；真实端点必须是 HTTPS 或本地 HTTP。超时、输入/输出 token、每日调用和月预算由 `app/config.py` 统一校验，公开摘要不会输出 API Key。真实模型必须逐项出现在调用方 allowlist 中，`mock-llm` 不能成为放行其他模型的通配符。

本地环境样例见 [`../deploy/local/.env.example`](../deploy/local/.env.example)。自动化测试不依赖商业 API。

## Docker Compose（PG + Redis + Gateway + Moderation）

```bash
cd llm-safety-platform
docker compose -f deploy/docker-compose.yml up --build
curl -s http://127.0.0.1:8080/healthz
curl -s http://127.0.0.1:8091/healthz
```

## Helm（行内 K8s）

```bash
helm upgrade --install llm-safety deploy/helm/llm-safety-platform \
  -f deploy/helm/llm-safety-platform/values.yaml
```

详见 [`deploy/README.md`](deploy/README.md)。

## 目录

```text
app/api/           FastAPI（/v1/safety、OpenAI-compatible、/v1/tools/authorize|execute、admin、approvals、redteam）
app/auth/          VK + OIDC/dev RBAC
app/vault/         AES-GCM Vault
app/providers/     ModelProxy
app/approvals/     HITL
app/redteam/       Offline runners + ReleaseEvaluator
workers/moderation LLM-as-Judge（/v1/classify，接通用模型）
console/           治理台（public 静态 SPA + Vite/React 源码）
deploy/            compose + helm
migrations/        Postgres DDL
```

## 变更记录（节选）

### 2026-08-06 · M6 商业 Judge 抽样契约

- `publish_profile.yaml`：`sample_limit=100`（每周 opt-in），`sample_limit_pre_release=300`。
- `SAFETY_JUDGE_SAMPLE_LIMIT` 可覆盖；无 `SAFETY_CLASSIFIER_URL` 时 skip。

### 2026-08-06 · M5 审计链双副本

- 新增 `app/observability/audit_lock.py`：`audit_chain_lock`（可选 `SAFETY_AUDIT_ADVISORY_LOCK=1` + PG advisory lock）与 `simulate_dual_writer_fork`（证明分叉可检测）。
- `HashChainLedger.write` 经进程锁串行；多副本仍需 advisory lock 或专用 writer（文档边界不变）。
- 验收：`pytest tests/test_audit_dual_writer.py -q`

### 2026-08-06 · M3 工具授权干跑（纪要君接入）

- 新增 `ToolRuntime.authorize()`：只返回五态决策，**不执行**工具副作用。
- 新增 `POST /v1/tools/authorize`：业务侧本地授权后调用；默认不强制安全平台业务白名单（风险上限 + denylist），与 `/v1/tools/execute` 分离（ADR-0004）。
- 请求可带 `trace_id` / `org_domain` / `policy_binding` 贯穿审计。
- 验收：`pytest tests/test_tools_authorize.py -q`

### 2026-08-06 · API 生命周期收口

- FastAPI 初始化由已废弃的 `on_event("startup")` 迁移到 `lifespan`，启动时继续执行共享状态初始化与审计链完整性检查。

### 2026-08-06 · 第三轮：链哈希回填 + 完整性测试收口

- **回填迁移**：`backfill_audit_chain_hashes()` 幂等从 `body_json` 复制或按 `id` 序重算；`upgrade_audit_chain()` 启动时 schema+data 一并执行
- **single-writer 边界**：回填与续链均假定单写者；多副本需 `pg_advisory_lock` 或专用 audit writer（文档明示，未实现分布式锁）
- **链检测测试**：duplicate / orphan / cycle（防御）/ 乱序 DB / hydrate fail-closed / 回填幂等
- pytest **103 passed**；`run_all` + dual_gate ci/release/full 全绿
- **单写者**：脱敏重建默认 single-writer；多副本需 PG advisory lock / 专用 writer（未宣称已解决多副本一致性）
- **publish profile**：`corpus_shim/fp_gates/dual_gate/remote_judge_compare` 各门 `enabled+blocking` 真实执行；`gates_audit` 逐门审计
- **critical 双人**：最终批准前重跑 `run_publish_gates()`；失败 gate=failed + 事件
- **指标 SoT**：`corpus_metrics.py` 从 YAML 计算（2500/2400/310/410/600）；语料漂移 fail-closed
- **remote Judge**：attack FN / benign FP / decision drift 分项 + 阈值；URL 脱敏
- pytest **103 passed**；`run_all` + dual_gate ci/release/full 全绿

### 2026-08-06 · 事实源收口 + 审计链跨重启 + publish profile

- **脱敏重建说明**：本仓为生产架构脱敏重建；shim/static 语料 **0 leak/FP 仅表示离线门禁通过**，不等于线上零事故
- **指标 SoT**：总语料 **2500**（2400 expect-block + 100 benign_controls）；ci FP **310**；release/full FP **410**；release attack **600**；full attack **2400**
- **publish profile**：`configs/evals/publish_profile.yaml` + `app/eval/publish_profile.py`；`POST .../publish` 显式跑 **dual_gate:ci**（非 full），响应含 `publish_profile` 审计元数据
- **审计链**：`app/observability/chain_verify.py`；`AuditDecisionRow` 按序验证；启动时 hydrate ledger；SIEM 事件带 `chain_hash`/`prev_chain_hash`
- **remote Judge**：`python -m app.eval.remote_judge_compare`；无 `SAFETY_CLASSIFIER_URL` 时 **skip**（不假装绿）；garak/PyRIT 仍 `REDTEAM_EXTERNAL=1` opt-in
- **报告**：`dual_gate_ci.json` / `dual_gate_release.json` / `dual_gate_full.json` 已重跑全绿
- pytest：**86 passed**；`run_all` 全绿

### 2026-08-06 · 双门控门禁 + benign 扩充

- **双门控**：`app/eval/dual_gates.py`（`ci` / `release` / `full`）；`corpus_gates` 串联 CI profile；`./scripts/eval_attack_corpora.sh dual_gate|dual_gate_release|dual_gate_full`
- `benign_fp_suite`：**288 → 310**（理财合规 / SOC runbook / API 轮换 / sanitizer keyword-trap）
- 家族修补：`_HARD_ATTACK_FOLLOW_RE` 防 `(Frame:runbook/…)` 绕过；`expert_advice` 合规培训 `suppress_context`
- 实测：ci **120/120 + 0/310 FP**；release **600/600 + 0/410 FP**；full **2400/2400 + 0/410 FP**
- pytest：`tests/test_dual_gate.py` + `test_benign_fp_suite`；`pytest` **79 passed**

### 2026-08-06 · benign FP / keyword-trap + 发布门禁

- 正向套件 `configs/evals/attack_corpora/benign_fp_suite.yaml`：**212 → 288**（合法语境含攻击关键词的改说法：钓鱼培训 / jailbreak 术语 / 支付改道防诈 / API key 轮换 / display:none 消毒 / RBAC / 任务劫持·MCP·诱导外泄 等）
- 收窄 `app/scanners/mocks.py`、`owasp_controls.py`、`configs/content_rules/default.yaml`：分类标签需攻击 framing；`suppress_context` / `_META_EDU_RE` 覆盖培训否定句
- 发布：`publish` 挂 `corpus_gates`（与 `SHIM_GATES` 同源）；`GET/POST /v1/admin/publish-gates*` 完成 critical 双人签字
- 评测：`benign_fp_suite` 0 FP / 288；`expanded_smoke` 0 leak；`EXPANDED_LIMIT=20` 与全量 expanded expect-block 0 leak
- **双门禁**：`python -m app.eval.dual_gates --profile ci|release|full`（Attack leak=0 且 FP=0 才过）；`./scripts/eval_attack_corpora.sh dual_gate`
- 说明见 [`docs/llm-safety-platform/14_扩展攻击语料.md`](../docs/llm-safety-platform/14_扩展攻击语料.md) 与 [`WORKLOG.md`](../docs/llm-safety-platform/WORKLOG.md)
