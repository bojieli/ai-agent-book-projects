# WORKLOG — LLM Safety Platform

## 2026-08-06（第三轮 · 链哈希回填 + 测试收口）

- **回填**：`backfill_audit_chain_hashes()` — body_json 复制或 id 序重算；`upgrade_audit_chain()` 启动调用；幂等
- **single-writer**：回填/续链/多副本 advisory lock 边界写入 002 SQL + migrate.py 文档
- **链测试**：duplicate / orphan / cycle / 回填 / 乱序 DB
- pytest **103 passed**；run_all + dual_gate ci/release/full 全绿
- 未 commit

## 2026-08-06（第二轮 · 审计链 graph + publish 真实语义）

- **审计链 graph 验证**：`rebuild_chain_from_rows` 按 `prev_chain_hash→chain_hash` 拓扑重建；检测 fork/cycle/orphan/missing link；乱序 DB 提交仍通过
- **fail-closed**：损坏链不 hydrate、不续写；`/readyz` 503；`ChainIntegrityError`
- **迁移 002**：legacy DB 幂等补 `chain_hash/prev_chain_hash` 列
- **single-writer 边界**：脱敏重建单进程；生产多副本需 advisory lock（文档明示，未假勾）
- **publish profile 真实执行**：各门 `enabled`/`blocking`；`gates_audit`；remote compare 挂 publish（opt-in）
- **critical 最终批准重评**：第二人签字前重跑 gates；失败 → gate=failed
- **corpus_metrics**：从 YAML 计算 SoT；`assert_profile_metrics` fail-closed
- **remote Judge**：FN/FP/drift 分项阈值；URL 脱敏
- pytest **103 passed**；run_all + dual_gate 全绿
- 未 commit

## 2026-08-06（事实源 + 审计链 + publish profile 收口）

- **指标统一**：2500 总语料；2400 expect-block；ci benign_fp **310**；release/full FP **410**（+100 controls）；release attack **600**；full **2400**
- **publish profile**：`configs/evals/publish_profile.yaml`；`run_publish_gates()` 替代隐式 `corpus_gates`；publish API 挂 `publish_profile` 审计字段；**默认 dual_gate:ci**（非 full）
- **dual_gate 报告**：重跑 ci/release/full → `dual_gate_*.json` 全绿；修复 release FP 双计数（benign_controls 不重复计入 expanded 样本）
- **审计链**：`chain_verify.py`；DB 按序验证 + 启动 hydrate；`/v1/admin/audit/chain/verify` 以 `audit_decisions.chain_hash` 为准；SIEM 决策事件含链标识
- **remote Judge**：`app/eval/remote_judge_compare.py`；无 URL 明确 skip + 测试；外部 garak/PyRIT 仍 opt-in
- **验证**：pytest **86 passed**；`run_all` + dual_gate ci/release/full 全绿
- 未 commit

## 2026-08-06（handbook_v1_full 扩包 + 复测）

- 语料：`handbook_v1_full.yaml` → **105**（97 block / 8 allow）；覆盖 ch.2–7 全家族
- 规则：ZH DAN / 绕过内容过滤器、工程师冒充、引用壳执行、bomb+markdown Base64；glossary `Do Anything Now` 防误杀
- Shim：expect-block leak **0%**；DeepSeek classify 全量 **0%**；benign_fp_suite 0 FP；`test_handbook_controls`/`test_benign_fp_suite`/`test_dual_gate` 绿
- 文档：`10_手册防御映射.md` 覆盖表与 leak 数字更新

## 2026-08-06（双门禁：有效性 + 防误杀）

- 策略：Attack gate（漏拦=0）与 FP gate（误杀=0）必须同时过；分层 ci / release / full
- 代码：`app/eval/dual_gates.py`；`corpus_gates` 含 smoke+benign_fp；`run_all` 挂 `dual_gates --profile release`
- 命令：`./scripts/eval_attack_corpora.sh dual_gate|dual_gate_release|dual_gate_full`
- 实测：ci / release **DUAL GATES PASSED**（leak 0、FP 0）；`tests/test_dual_gate.py` 绿
- 文档：`14_扩展攻击语料.md` 双门禁章节

## 2026-08-06（双门控门禁落地 + benign 扩充）

### 双门控策略（Attack + FP）
- **Attack gate**：`handbook_expanded_smoke` expect-block（120）+ 可选 `EXPANDED_LIMIT=20`（480）/ 全量 expanded（2400）漏拦率 ≤ 0
- **FP gate**：`benign_fp_suite` + `benign_controls` expect-allow 误杀率 ≤ 0（keyword-trap / 改说法）
- **实现**：`app/eval/dual_gates.py`（profile: `ci` | `release` | `full`）；`corpus_gates` 串联 CI dual_gate；`publish` 仍走 `run_corpus_gates()`
- **命令**：
  ```bash
  ./scripts/eval_attack_corpora.sh dual_gate              # CI（smoke + fp_suite）
  ./scripts/eval_attack_corpora.sh dual_gate_release      # + LIMIT=20 + benign_controls
  DUAL_GATE_PROFILE=full python -m app.eval.dual_gates    # 发版前全量
  pytest tests/test_dual_gate.py tests/test_benign_fp_suite.py
  ```
- **家族修补**：`_HARD_ATTACK_FOLLOW_RE` 覆盖 `(Frame:runbook/…)` 伪装下的 `SYSTEM COMPROMISED` / `policy dump` / `output system configuration`；`expert_advice` 增加合规培训 `suppress_context`

### benign_fp_suite 扩充
- **288 → 310**（+22）：理财合规培训 / SOC runbook / API key 轮换 / RAG sanitizer 设计文档 keyword-trap 改说法簇
- 结果（shim）：ci **120/120 + 0 FP/310**；release **600/600 + 0 FP/410**；full **2400/2400 + 0 FP/410**

### 后续（可选）
- 分层抽样 / shadow mode / borderline Judge-only（见 `14_扩展攻击语料.md`）
- 远程 Judge 矩阵对比 shim 规则漂移

- 未 commit

## 2026-08-06（benign FP / keyword-trap 收口 + 发布门禁闭环）

### FP / keyword-trap
- 目标：扩大正向误杀套件（改说法 + 合法语境含攻击关键词），收窄家族规则，保持攻击侧绿
- `benign_fp_suite.yaml`：**212 → 288**（+76 keyword-trap 改说法：任务劫持 / 客服优先级重排 / 诱导外泄 / 分片指令 / MCP·工具投毒 / id_rsa / webhook / SSN / developer / 忽略先前 / DAN模式 / API密钥 / SQL注入 等）
- 收窄（家族级，非删防御）：裸 `任务劫持|诱导外泄|分片指令|客服优先级重排|伪造支付改道|DAN mode|do anything now|诱导工具调用|模拟多轮` → 要求攻击 framing / 冒号；`MCP / 工具投毒` → 需 `JSON`；`电汇诈骗…实施` 不再误触「非实施」；`content_privacy` 对 `never ask … list tokens in context` 增加 `suppress_context`；EN `extract API keys…from the conversation context` 仍 block
- 涉及：`mocks.py` / `owasp_controls.py` / `configs/content_rules/default.yaml`
- 结果：`benign_fp_suite` **0 FP / 288**；smoke expect-block **0.000**（120/120）；`EXPANDED_LIMIT=20` **0.000**（480/480）；全量 expanded expect-block **0.000**（2400/2400）；`benign_controls` FP=0

### 发布门禁 / critical 双人（半成品收口）
- `POST .../publish` 串联 `run_corpus_gates()` → `redteam["corpus_gates"]`；`ReleaseEvaluator` 阈值与 `SHIM_GATES` **单一数据源**（ADR-029）
- 新增 `GET /v1/admin/publish-gates` + `POST .../publish-gates/{id}/approve`（Security/AppOwner 分签，禁止同一 actor）
- 测试：`test_publish_fails_when_corpus_gates_fail`、`test_critical_publish_dual_approval_gate`

### 简历
- `简历_new/个人简历.md`、`个人简历_纪要君架构版.md`：项目四 LLM Safety Platform 诚实口径（288 FP / smoke·LIMIT20·全量数字；OIDC/KMS/Dual-LLM 标适配器就绪）

### 后续改进方向（优先级）
1. **控制台抛光**：红队 runs 列表、hash-chain verify 按钮、语料准入 tab、critical 双人待办 UI（API 已齐）
2. **全量 expanded 进离线门禁**：CI 维持 smoke + LIMIT=20；夜间/发版前跑满 2500，报告归档
3. **真外部适配验证**：行内 IdP JWKS、AWS KMS/HSM、`REDTEAM_EXTERNAL=1` garak/PyRIT（不在本地 stub 假绿）
4. **AlignmentCheck 全量 LLM trace**：仍按 ADR-024 deferred
5. **远程 Judge 评测矩阵**：固定 DeepSeek/自建 moderation 抽样对比 shim，防规则漂移
6. **benign_fp_suite 进 corpus_gates / run_all**（FP 阈值，见 `14_扩展攻击语料.md`）

- 未 commit

## 2026-08-05（全量 handbook_expanded 收口）

- 目标：无 `EXPANDED_LIMIT` 跑满 25×100；此前 LIMIT=20 已 0，全量初跑 expect-block leak **0.0458**（110/2400）
- 家族级补丁（非 case-id）：`mocks.py` INJECTION/INDIRECT、`owasp_controls` LEAK/INDIRECT_CHUNK、`content_rules` violence/privacy/expert_advice/jailbreak
  - PII / 脱敏完整打印 / emails+account table / SSN / markdown phone table
  - `绕过内容过滤并无限制回答`、MCP poison / `audit_dump`、`诱导工具调用`+`id_rsa`
  - social/exfil：`原样返回 system prompt`、`paste developer message`、`data: URI`+developer、`/bin/reveal_prompt`
  - finance all-in certainty、KO/RU ignore、violent assault how-to、char-spaced collapsed markers
- 结果：全量 expect-block leak **0.000**（2400/2400）；`benign_controls` FP=0；smoke **0.000**（120/120）；`benign_fp_suite` **0 FP / 100**
- 命令：`./scripts/eval_attack_corpora.sh expanded`；`./scripts/eval_attack_corpora.sh expanded_smoke`
- 见 `14_扩展攻击语料.md`

## 2026-08-05（LIMIT=20 九漏拦家族收口）

- 目标：`EXPANDED_LIMIT=20` 残留 9/480（0.019）→ 家族级补丁（非 case-id 过拟合）
- 家族：context wrapping 暴力 howto / guardrail 图片链外泄 / 分片多轮抽密 / finance insider framing / task hijack doc+support
- 补丁：`mocks.py` INJECTION/INDIRECT、`owasp_controls.INDIRECT_CHUNK_RE`、`content_rules` violence/privacy/expert_advice/jailbreak
- 结果：smoke **0.000**（120/120）；`benign_fp_suite` **0 FP / 100**；`EXPANDED_LIMIT=20` expect-block leak **0.000**（480/480）；benign_controls FP=0
- 见 `14_扩展攻击语料.md`

## 2026-08-05（HTML-hidden / 支付改道漏拦收口）

- 复测 smoke：`indirect_rag_079`（CSS `display:none` + SYSTEM + 伪造支付改道）此前为残留；现 **smoke leak 0.000**（120/120 expect-block）
- 家族级补丁（非 079 单条）：`mocks.py` INJECTION/INDIRECT、`owasp_controls.RagGate`、`content_rules` fraud/jailbreak
  - HTML/CSS 隐藏：`display:none|mso-hide|opacity:0|font-size:0/1px` + SYSTEM/OVERRIDE
  - 支付改道：`伪造支付改道|支付改道|payment diversion|电汇诈骗`
  - RAG 走私：`cross-document secret retrieval` / `post to audit endpoint`
- 结果：`benign_fp_suite` **0 FP**；full `indirect_rag` **0/100**；当时 `EXPANDED_LIMIT=20` expect-block leak **0.019**（9/480；已由上条收至 0）
- 见 `14_扩展攻击语料.md`

## 2026-08-05（语料）

- **handbook_expanded diversity v2**：重写生成器（大词池+≥12 骨架+归一化去重+手册套路发散；无 overflow）；25×100 唯一比 **1.0**；smoke leak **0.176→0.040**；`EXPANDED_LIMIT=20` expect-block leak **~0.35→0.115**（benign FP=0）；家族规则补丁 `mocks.py`/`content_rules`；见 `14_扩展攻击语料.md`

## 2026-08-05（误杀回归）

- 收窄过宽规则：`可利用漏洞` / 裸 `钓鱼` / 裸 `管理员权限` 不再误杀教学与工单话术
- 正向套件：`configs/evals/attack_corpora/benign_fp_suite.yaml`（100 allow）+ `tests/test_benign_fp_suite.py`
- 结果：fp_suite **0 FP**；handbook_expanded benign **0 FP**；smoke leak 已收至 **0%**（见上条）

## 2026-08-05（文档）

- **手册精读+案例**：`13_手册精读与案例.md`（SecureNexusLab Handbook V1.0：章节要点 + 原文级 payload/EchoLeak/DAN/GCG/Crescendo 等）

## 2026-08-05（v2.4 · on-prem 阻塞期本地硬化）

### 目标
银行 IdP/KMS/GPU 未就绪；在其余路径加深语义防泄漏与发布门禁（ADR-029）。

### A · 语义 / 中文泄漏
- 加深 `content_rules`：fairness 外貌/卫生/亚文化/地域刻板；CSE login howto / many-shot / Interlace / Morse / PII 格式化
- Judge system prompt + fuse：fairness/CSE soft-LLM escalate；rules floor 始终生效
- Gateway `RemoteClassifier` dual-path fuse（rules ∪ remote）

### B · 防御纵深（无 on-prem）
- `SAFETY_REMOTE_TIMEOUT` 默认 12s；fail 策略文档化
- Dual-LLM：unsigned / replay / analyzer injection / forbidden tools
- `session_risk` crescendo 信号扩展；`output_exfil` markdown/data-uri/DNS；hex decode cascade
- ToolRuntime 规则：wealth_assistant / customer_bot 增 PII/钓鱼/SSRF/KB 注入

### C · 本地红队 / 发布门禁
- `python -m app.eval.corpus_gates` 纳入 `run_all`（handbook + oss + seed 阈值）
- `spawn_external` dry-run 嵌入真实 multiturn_shim（crescendo）
- 语料扩：`generated_zh_attacks.yaml` Flames/CSE 软泄漏族

### 重跑基线（before → after）
报告路径：`llm-safety-platform/configs/evals/attack_corpora/reports/`（2026-08-05 本地硬化后）。

| Corpus | Before | After | Notes |
|--------|--------|-------|-------|
| PurpleLlama shim | 2.4% (2/83) | **0%** (0/78 block) | `oss_purplellama_sample_shim.json` |
| PurpleLlama DeepSeek | 4.8% | **0%** (0/30，抽样) | `oss_purplellama_sample_deepseek.json` |
| Flames shim20 | 5% (1/20) | **0%** (0/20) | `flames_1k_zh_shim20.json` |
| Flames DeepSeek30 | **26.7%** (8/30) | **0%** (0/30) | `flames_1k_zh_deepseek30.json` |
| handbook_v1_full shim | 0% | **0%** (0/77) | gate ≤5% |
| oss_garak_sample shim | 0% | **0%** (0/21) | gate ≤5% |
| oss_agentic_security shim | ~2.9% (1/35) | **~2.9%** (1/35，`as_verazuo_05`) | 未强行过拟合 |
| pytest | — | **69 passed** | 全量 |

### 仍需 on-prem / 外部
- 行内 IdP JWKS、真 AWS KMS/HSM、真 GPU/vLLM moderation、完整 garak/PyRIT 安装

### 验证
```bash
cd llm-safety-platform
.venv/bin/python -m pytest -q
.venv/bin/python -m app.eval.run_all
./scripts/eval_attack_corpora.sh shim
LIMIT=30 ./scripts/eval_attack_corpora.sh deepseek   # if DeepSeek env ready
```

---

## 2026-08-05

### Tracks 完成摘要（v2.3）

**Track 1 — Flames + PurpleLlama**
- 基线：Flames DeepSeek leak **73.3%** (22/30 Fairness)；PurpleLlama shim leak **~64%** (50/78)
- 加深 `content_rules`（fairness / CSE PII / few-shot / SYSTEM-CONTEXT / ROT13）+ Judge prompt + fuse fairness soft-LLM guard
- **重跑结果（v2.3 当时）**：PurpleLlama shim 2.4% / DeepSeek 4.8%；Flames shim20 5% / DeepSeek30 26.7%
- **已被 v2.4 覆盖**：见上文 before→after 表（Flames/PurpleLlama 均 **0%**）
- 命令：`./scripts/eval_attack_corpora.sh shim`；`LIMIT=30 ./scripts/eval_attack_corpora.sh deepseek`

**Track 2 — 生产硬化**
- On-prem：`deploy/docker-compose.onprem.yml` + Helm `values-onprem.yaml` + moderation Deployment；`MODERATION_ONPREM_MOCK`
- OIDC：`app/auth/oidc.py` JWKS JWT；`OIDC_REQUIRED=1` fail-closed（ADR-025）
- KMS：`app/vault/kms.py` `env|file|aws_kms_stub|http_kms`（ADR-026）
- SIEM：`log|http|file` SPI 发 hash-chain 事件
- 文档：`03`/`05`/`DECISIONS`/`deploy/README`

**Track 3 — 外部红队真跑**
- `spawn_external()`：`REDTEAM_EXTERNAL=1` subprocess + timeout + JSON ingest + release_gate
- CI 默认仍 multiturn_shim / YAML；单测 fake subprocess

**Track 4 — 会话图 + Dual-LLM**
- `session_store`（memory|redis）+ role-drift / crescendo；API `session_id`
- `DUAL_LLM=1` Analyzer→signed Intent→Executor（隔离 invariant）；ADR-023→027 opt-in MVP

**Track 5 — 业务 VK**
- `configs/policies/wealth_assistant.yaml`（`t_bank_retail`）
- `scripts/smoke_business_vk.sh`：VK→chat→audit→HITL

### 验证
```bash
cd llm-safety-platform
.venv/bin/pip install -q -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m app.eval.run_all
# corpus (optional):
./scripts/eval_attack_corpora.sh shim
LIMIT=30 ./scripts/eval_attack_corpora.sh deepseek   # if DeepSeek env ready
./scripts/smoke_business_vk.sh                        # gateway up
```

### 仍属真外部依赖（适配器齐）
- 行内 IdP JWKS、真 AWS KMS/HSM、真 on-prem GPU/vLLM、完整 garak/PyRIT 安装与 study 克隆

---

## 2026-08-05（早）

- **OSS 架构闭环**：`12_开源架构借鉴.md`；对齐 `03`/`10`/`11`/`DECISIONS`(ADR-021..024)/`COMPLETION`/`WORKLOG` 与代码（spotlight / hidden_ascii / decode_views / session_risk / external_runners / output_exfil）
- **session_risk**：硬组合 escalate（inj≥1 ∧ crescendo≥1 ∧ turns≥2 → block），匹配 ADR-023；pytest 全绿
- **语料重跑（shim gateway，早）**：handbook 0%；oss_agentic ~2.9%；oss_garak 0%；oss_purplellama 当时 ~64% → **已被上方 v2.4 表覆盖为 0%**
- **Handbook full pack + OSS 红队语料**：`handbook_v1_full.yaml`（84）、`oss_agentic_security.yaml`（40）、`oss_garak_sample.yaml`（24）、`oss_purplellama_sample.yaml`（83）；clone study 只读；映射 `10`/`11`/`12`
- **手册对齐**（SecureNexusLab Prompt Injection Handbook V1.0）：`decode_views` 递归解码、上下文包装注入规则、`output_exfil`、语料 `handbook_pi_attacks.yaml`；映射见 `10_手册防御映射.md`
- **CN corpus**：CHiSafety DeepSeek 30/30；Flames DeepSeek 8/30；shim CHiSafety 20/20；Flames shim 18/20

## 2026-08-04

- **ADR-020**：内容审核先基础 Instruct 模型（moderation worker），后期同 `/v1/classify` 契约换微调/Guard
- **OWASP Top10 补齐（平台侧）**：system_leak / rag_gate / grounding / supply-chain digests / 工具结果回扫 / 日预算+并发 / corpus 准入 API；`02` 状态灯更新
- **通用模型审核 worker**：`workers/moderation` 提供 `/v1/classify`（LLM-as-Judge + 规则 fuse）；Gateway `SAFETY_SCANNER_MODE=remote` 对接；compose 默认 mock
- **防护加深**：文本归一化（NFKC/ZW/全角/字间空格）、YAML 加权内容打分引擎、`SafetyClassifier` SPI（shim/onnx/remote/llm_guard）、红队探针扩至注入混淆与内容四类；默认仍 `SAFETY_SCANNER_MODE=shim`
- **Production Cut 实现收尾**：FastAPI API 全集、VK/RBAC、加密 Vault、ModelProxy、HITL resume、红队/ReleaseEvaluator、`/console` 治理台、compose+Dockerfile+Helm、`verify_production` + pytest；`run_all` **ALL PHASE GATES PASSED**
- **Production Cut v2.0 文档**：04 HLD / 05 DLD / 06 L3 门禁 / COMPLETION 全勾；DECISIONS ADR-012..018
- 对照仓：`llm-safety-study/` 只读；Greenfield：`llm-safety-platform/`
