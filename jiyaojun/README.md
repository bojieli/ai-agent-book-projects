# 纪要君（绿场）

> **本目录是生产架构的脱敏重建版**（v7.7 绿场实现）。  
> 外部系统（SSO、ASR、向量库、Jira/企微等）以 **Mock / SPI** 替代，契约与真实架构对齐。  
> 禁止修改仓库内 `jiyaojun-preview/`（原始预览仅作参考/反例）。

契约与 Skill Pack 真相源：[`docs/meeting-assistant/`](../docs/meeting-assistant/)  
决策记录：[`DECISIONS.md`](../docs/meeting-assistant/DECISIONS.md) · 工作日志：[`WORKLOG.md`](../docs/meeting-assistant/WORKLOG.md)

## Phase 0 范围

- PostgreSQL DDL：`migrations/001_phase0.sql`
- 领域事件枚举：`app/events/enums.py`
- Default Playbook / Render / Skills：symlink → `docs/.../samples`
- ToolRuntime + mock connectors
- 冒烟：`python -m app.demo.phase0_smoke`

完成定义（01 §12）：假数据跑通  
`eng × tech_review` → 理解 → Envelope → mock 任务单 → work_link → acl_view → email_html，并写 trace/usage。

## 快速跑

```bash
cd jiyaojun
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.eval.run_all    # skills + DoD + 能力30 + 功能31 + RAG测评 + pytest
```

分项：

```bash
python -m app.eval.smoke_skills
python -m app.demo.phase0_smoke
python -m app.demo.r1_flagship_loop   # M4 R1 旗舰闭环
python -m app.eval.verify_architecture
python -m app.eval.verify_features
python -m app.eval.retrieval_quality   # Hit@k / MRR / nDCG / Faithfulness
python -m app.eval.story_gates         # Ch6 故事族门禁 R5/R4/H5/K1/X1
pytest tests -q
```

完成确认：[COMPLETION.md](../docs/meeting-assistant/COMPLETION.md)

## 基础设施配置契约（升级第一阶段）

`app/config.py` 统一读取 PostgreSQL、Redis、S3-compatible、Qdrant 与安全控制面地址。所有配置默认空，现有测试继续走离线实现；启用真实适配器前必须调用 `validate()`，非法协议或相对地址 fail-closed。`public_summary()` 只暴露启用状态，不输出 access key、secret 或 gateway token。

本地变量样例与 Core 启动方式见 [`../deploy/local/.env.example`](../deploy/local/.env.example) 和 [`../deploy/local/README.md`](../deploy/local/README.md)。

## M2.1 PostgreSQL / Redis 持久化（2026-08-06）

默认 `JIYAOJUN_STORAGE_BACKEND=memory`、`JIYAOJUN_REDIS_BACKEND=memory`，与 Phase 0 行为完全一致；无 env 时 `run_all` 全绿。

| 组件 | 路径 | 说明 |
|------|------|------|
| 迁移 DDL | `migrations/002_app_runtime.sql` | `app_meeting`、`app_session_journal_entry`、`app_task_projection`、`app_work_link` |
| 连接与迁移 | `app/persistence/postgres.py` | DSN 规范化、`apply_migrations` 幂等、`app_schema_migration` |
| Journal PG | `app/memory/postgres_repository.py` | `PostgresJournalRepository` 实现 Protocol |
| Meeting PG | `app/store/postgres_meetings.py` | `PostgresMeetingStore`；update 同步 `app_work_link` |
| Redis 缓存 | `app/cache/redis_client.py` | `SessionProjectionCache`、`IdempotencyCache` |
| 工厂 | `app/runtime/factory.py` | `build_journal_repository` / `build_meeting_store` / `build_session_cache` / `build_vector_index` / `build_object_store` |
| CLI 迁移 | `python -m app.persistence.migrate` | 应用 001 + 002 |

```bash
pip install -r requirements-core.txt   # psycopg[binary]、redis
export JIYAOJUN_DATABASE_URL=postgresql+psycopg://platform:platform-dev-only@127.0.0.1:55432/jiyaojun
export JIYAOJUN_REDIS_URL=redis://127.0.0.1:56379/1
export JIYAOJUN_STORAGE_BACKEND=postgres
export JIYAOJUN_REDIS_BACKEND=redis
python -m app.persistence.migrate
pytest tests/integration -q            # @pytest.mark.integration
```

## M2.2 Celery Worker（2026-08-06）

默认 `JIYAOJUN_SCHEDULER_BACKEND=memory`（`InProcessScheduler`），与 Phase 0 行为一致；仅当 `JIYAOJUN_SCHEDULER_BACKEND=celery` 时切换 `CeleryScheduler`。

| 组件 | 路径 | 说明 |
|------|------|------|
| Celery App | `app/scheduler/celery_app.py` | broker/result 指向 Redis（推荐 DB2：`JIYAOJUN_CELERY_BROKER_URL`） |
| 长任务 | `app/scheduler/celery_tasks.py` | `run_pipeline_job`；执行前 `IdempotencyCache.set_nx` 防重复写回 |
| Celery 调度器 | `app/scheduler/celery_scheduler.py` | submit/status/cancel/register_projection/mark_orphaned_on_restart |
| 任务状态 | `app/scheduler/task_state.py` | Redis `ctask:{id}`、`idem_task:{key}` |
| 工厂 | `app/runtime/factory.py` | `build_scheduler` / `build_idempotency_cache` / `build_task_state_store` |

```bash
pip install -r requirements-core.txt   # 含 celery[redis]>=5.4
export JIYAOJUN_SCHEDULER_BACKEND=celery
export JIYAOJUN_CELERY_BROKER_URL=redis://127.0.0.1:56379/2   # broker DB2
export JIYAOJUN_REDIS_URL=redis://127.0.0.1:56379/1           # 缓存 DB1
# 宿主机启动 Worker
celery -A app.scheduler.celery_app.celery_app worker -l info
# 或 Compose profile
docker compose --profile worker -f deploy/local/docker-compose.yml up -d celery-worker
pytest tests/integration/test_celery_worker.py -q
```

**Worker 重启语义**：`mark_orphaned_on_restart` 将 pending/running 标为 `orphaned/needs_resume`；同一 `idempotency_key` 重复 submit 不重复执行副作用。postgres 可用时状态同步 `app_task_projection`。

**未做**：`DialogSessionService` 仍默认进程内调度（未自动切 Celery）；身份/密钥/观测见 M5。

## M3 安全控制面接入（2026-08-06）

默认无 `JIYAOJUN_SAFETY_GATEWAY_URL` 时使用 `OfflineSafetyGateway`（确定性、零外网），`run_all` 全绿。

| 组件 | 路径 | 说明 |
|------|------|------|
| 出站门禁 | `app/safety/egress.py` | public/internal 脱敏后可出站；confidential/critical/sealed 阻断 |
| 预算 | `app/safety/budget.py` | 输入 8K / 输出 2K / 日 100 / 月 200 元，超限 fail-closed |
| 离线网关 | `app/safety/offline.py` | 本地 mock 聊天 + 工具授权干跑 |
| HTTP 网关 | `app/safety/http_client.py` | `/v1/chat/completions` + `/v1/tools/authorize`；失败 fail-closed |
| 双重授权 | `app/safety/dual_authz.py` | 业务 ∩ 安全 → `max_strict`；安全不能放宽业务拒绝 |
| 模型客户端 | `app/safety/model_client.py` | `SafetyRoutedLLMClient` 禁止旁路直连 |
| 接线 | `bounded_loop` / `step_engine` / `session_service` | 工具前授权；评估器经安全网关 |
| 配置 | `app/config.py` | `JIYAOJUN_MODEL_MAX_*` / `DAILY_CALL_LIMIT` / `MONTHLY_BUDGET_CNY` |

安全控制面新增 **`POST /v1/tools/authorize`**（只判决、不执行），与 `/v1/tools/execute` 分离（ADR-0004）。

```bash
pytest tests/safety/test_m3_safety_gateway.py -q
# 可选：指向本地安全网关
export JIYAOJUN_SAFETY_GATEWAY_URL=http://127.0.0.1:8080
export JIYAOJUN_SAFETY_GATEWAY_TOKEN=<virtual-key>
```

## M5 可靠性 / 观测 / 故障矩阵（2026-08-06）

默认不启 Keycloak/OpenBao/Grafana；离线 `fault_matrix` 与 `run_all` 全绿。

| 组件 | 路径 | 说明 |
|------|------|------|
| 遥测 | `app/observability/telemetry.py` | span：model/rag/hitl/tool_authorize/writeback；Prometheus 文本；可选 OTLP |
| 故障矩阵 | `app/eval/fault_matrix.py` | 7 场景强制 fail-closed / 幂等 / orphan |
| Agent 钩子 | `bounded_loop.py` | HITL suspend 与工具授权打点 |
| Compose | `../deploy/local/` | `--profile identity\|secrets\|observability` |

```bash
python -m app.eval.fault_matrix
pytest tests/eval/test_fault_matrix.py -q
# 可选观测栈
docker compose --profile observability -f ../deploy/local/docker-compose.yml up -d
export JIYAOJUN_OTEL_ENDPOINT=http://127.0.0.1:54318
```

## M6 质量与交付（2026-08-06）

| 组件 | 路径 | 规模/说明 |
|------|------|-----------|
| RAG 黄金集 | `fixtures/eval/rag_golden.yaml` | **70** cases（`scripts/generate_m6_corpora.py` 可重生） |
| Agent 故事 | `fixtures/eval/agent_stories.yaml` | **30**（主路径+失败） |
| 负例目录 | `fixtures/eval/negative_catalog.yaml` | **22** ACL/密封/跨域 |
| 质量门禁 | `app/eval/m6_quality_gates.py` | 规模 + 负例执行 + 离线性能 |
| 一键/手册 | `../scripts/demo_*.sh` · `../docs/ops/` | 启动/演示/故障/证据/kind |

```bash
python -m app.eval.m6_quality_gates
python -m app.eval.run_all
```

## M4 R1 旗舰闭环（2026-08-06）

默认无 env 时 `run_all` 全绿；完整路径可本地一键验收。

| 组件 | 路径 | 说明 |
|------|------|------|
| Jira 模拟器 | `app/connectors/jira_simulator.py` | `mode`: normal/timeout/fail；幂等；`transition`；`schedule_webhook_callback` / `emit_callback` |
| Mock Jira | `app/connectors/mock_saas.py` | 委托 `JiraSimulator`；Jira-shaped SPI |
| Continuum 关闭 | `app/knowledge/series_bridge.py` | `close_open_item(series_id, item_id)` → SeriesStore + `KnowledgePlane.close_continuum_item` |
| Webhook | `app/api/bff.py` | `internal_connector_webhook`：status 为 closed/done/resolved 时更新 work_objects **并**关闭 Continuum；发 `continuum.item_closed` |
| 闭环演示 | `app/demo/r1_flagship_loop.py` | 技术评审 A → HITL → 缺陷 → 企微 msgid → 幂等复跑 → webhook 关闭 → 会议 B briefing 不含已关闭项 |
| Celery 真实流水线 | `app/scheduler/celery_tasks.py` | `JIYAOJUN_CELERY_PIPELINE=orchestrator`（默认）调用 `Orchestrator.bind_and_run`；`stub` 保留占位 |
| StepEngine 桥接 | `app/planes/pipeline/step_engine.py` | 与 `KnowledgePlane.series_bridge` 共用 store，briefing 与 pipeline 写入同源 |

```bash
python -m app.demo.r1_flagship_loop
pytest tests/connectors/test_jira_simulator.py tests/integration/test_r1_flagship_loop.py -q
# Celery 单测仍可用 monkeypatch _run_pipeline_body；集成测 eager 模式无需独立 Worker
export JIYAOJUN_CELERY_PIPELINE=stub   # 仅跑占位逻辑时
```

**边界**：Celery 生产环境需独立 Worker（`celery -A app.scheduler.celery_app.celery_app worker`）；单测与 `eager` 模式在同进程同步执行 `run_pipeline_job`，不必起 Worker。

## M2.3 Qdrant / SeaweedFS（2026-08-06）

默认 `JIYAOJUN_VECTOR_BACKEND=memory`、`JIYAOJUN_OBJECT_BACKEND=mock`，无 env 时 `run_all` 全绿。

| 组件 | 路径 | 说明 |
|------|------|------|
| 向量索引协议 | `app/knowledge/vector_store.py` | `VectorIndex`；`QdrantHybridIndex`（dense + payload ACL 过滤 + sparse 重排） |
| 内存索引 | `app/knowledge/rag.py` | `HybridRagIndex` 实现 `VectorIndex` |
| 对象存储 | `app/storage/object_store.py` | `MockObjectStore` / `S3ObjectStore`（path-style，自动 create_bucket） |
| 配置 | `app/config.py` | `vector_backend`、`object_backend`、`qdrant_*`、`s3_*` |
| 工厂 | `app/runtime/factory.py` | `build_vector_index` / `build_object_store` |
| 集成测试 | `tests/integration/test_qdrant_seaweed.py` | 无 Qdrant/S3 时 skip |

```bash
pip install -r requirements-core.txt   # 含 qdrant-client、boto3
# 本地 Core Compose 已起 Qdrant(56333) + SeaweedFS S3(58333)
export JIYAOJUN_QDRANT_URL=http://127.0.0.1:56333
export JIYAOJUN_S3_ENDPOINT=http://127.0.0.1:58333
export JIYAOJUN_S3_BUCKET=jiyaojun
export JIYAOJUN_S3_ACCESS_KEY=local-dev-access
export JIYAOJUN_S3_SECRET_KEY=local-dev-secret
export JIYAOJUN_VECTOR_BACKEND=qdrant
export JIYAOJUN_OBJECT_BACKEND=s3
pytest tests/integration/test_qdrant_seaweed.py -q
```

`RagPipeline` 支持注入 `index=`（来自 factory），默认仍用内存 `HybridRagIndex`。


## Meeting Knowledge Plane / RAG（必读）

端到端路径：**ingest → structure-aware chunk → Hybrid index → ACL-first retrieve → grounded answer**。

| 模块 | 路径 | 说明 |
|------|------|------|
| Orchestrator | `app/orchestrator/service.py` | 按 `orchestration_mode` 路由 SOP / Playbook / Fallback |
| 步骤引擎 | `app/planes/pipeline/step_engine.py` | 阶段式状态机；Skill Pack schema/checklist/成功标准 |
| SOP | `app/planes/pipeline/sop_executor.py` | `steps.yaml` 驱动正式 SOP |
| Playbook | `app/planes/pipeline/playbook_executor.py` | `default.yaml` + `playbook_overrides.yaml` |
| Series 桥接 | `app/knowledge/series_bridge.py` | `MeetingSeriesStore` ↔ Continuum 统一 open items |
| Skill Pack | `app/skills_runtime/skill_pack.py` | 元数据 / schema / 示例产物 / 成功标准 |
| 分块 | `app/knowledge/chunking.py` | 标题/章节 + 说话人轮次 + 句子窗口；`JIYAOJUN_CHUNK_MAX_CHARS` / `JIYAOJUN_CHUNK_OVERLAP` |
| Embedding | `app/knowledge/embedding.py` | **CI 默认 `bge-m3-shim`**；生产可换 `bge-m3`（见 09） |
| 检索 | `app/knowledge/rag.py` | ACL→Dense+Sparse→轻量 rerank→**bounded multi-hop rule rewrite**→citation |
| Session 记忆 | `app/memory/` | **session tree** + branch marker；deterministic compaction；JSONL 全量校验 fail closed |
| Agent loop | `app/agents/bounded_loop.py` | **observation→下一轮 planner**；HITL 从 journal suspend 恢复；每 run 独立 budget |
| 工具发现 | `app/connectors/discovery.py` | 递归 sanitizer + **min_score**；`[]` allowlist = deny all |
| 调度 | `app/scheduler/tasks.py` | **合作式 cancel token**（不可强杀线程）；orphan on restart |
| Celery Worker | `app/scheduler/celery_*.py` | 可选 `JIYAOJUN_SCHEDULER_BACKEND=celery`；`JIYAOJUN_CELERY_PIPELINE=orchestrator|stub`（默认 orchestrator） |
| Dialog 会话 | `app/planes/dialog/session_service.py` | session_id resume + branch/compaction + HITL approve/reject |
| 故事门禁 | `app/eval/story_gates.py` | Ch6 + **机器可读报告** `fixtures/eval/story_gates_report.json` |
| 接地 | `app/knowledge/grounding.py` | 摘录式回答 + 句子级 Faithfulness |
| Knowledge | `app/knowledge/plane.py` | Docs / Continuum / Transcript 入库与 `answer()` |
| Dialog | `app/planes/dialog/service.py` | `briefing` + `ask`（带 citations） |
| BFF | `app/api/bff.py` | 知识类聊天走 RAG grounding，不再空回声 |
| 测评 | `app/eval/retrieval_quality.py` | 黄金集 `fixtures/eval/rag_golden.yaml` |

```bash
# 检索质量门禁（失败打印 RAG_EVAL_FAILED 并 exit 1）
python -m app.eval.retrieval_quality
python -m app.eval.retrieval_quality --golden fixtures/eval/rag_golden.yaml
```

指标：`hit_rate` · `recall_at_k` · `mrr` · `ndcg_at_k` · `faithfulness`；阈值写在 golden 的 `thresholds`（有默认兜底）。2026-08-06 全量结果：Hit@5=1.0、MRR=0.9286、nDCG@5=0.9473、Faithfulness=0.932。

## 双平面与记忆边界（Ch2/3/4）

| 层 | 模块 | 用途 |
|----|------|------|
| **Session journal** | `app/memory/` | append-only **session tree**；branch marker 持久化 active leaf；`DeterministicExtractiveSummarizer`；`build_context` 仅 active path |
| **Continuum** | `app/knowledge/plane.py` | 跨会工作记忆（open items） |
| **Glossary** | `app/knowledge/glossary.py` | 域术语治理 |
| **会后 Pipeline** | `StepEngine` | 阶段式状态机（SOP/Playbook） |
| **会前 Dialog loop** | `BoundedAgentLoop` | **Mock planner**（非生产 LLM）；tool→observation→再决策；max_steps + 每 run 独立 budget |

BFF `post_chat_completions` 经 `DialogSessionService`：同 `session_id` 可恢复；工具任务走 agent loop；知识问答走 RAG grounding。

## 变更记录（2026-08-06）

### M2.1 持久化（PostgreSQL + Redis 缓存）

- **运行时表**：`migrations/002_app_runtime.sql`（字符串 `meeting_id`，与 001 BIGSERIAL 设计表独立）。
- **Repository**：`PostgresJournalRepository`、`PostgresMeetingStore`；默认 memory 不变。
- **Redis**：`SessionProjectionCache`（`sess:{id}`）、`IdempotencyCache`（`idem:{key}`）；连接失败明确报错。
- **配置**：`JIYAOJUN_STORAGE_BACKEND`、`JIYAOJUN_REDIS_BACKEND`；postgres/redis 模式校验 URL。
- **测试**：133 pytest（含 6 项 integration）；无 env 时 128 passed + 5 skipped；`run_all` 全绿。

### M2.2 Celery Worker（2026-08-06）

- **调度后端**：`JIYAOJUN_SCHEDULER_BACKEND=memory|celery`（默认 memory）；`build_scheduler` 工厂切换。
- **Celery**：`celery_app` broker/result 用 Redis DB2；`run_pipeline_job` 长任务 + `IdempotencyCache` 防重复写回。
- **恢复**：`register_projection` + `mark_orphaned_on_restart`；postgres 时写 `app_task_projection`。
- **Compose**：`deploy/local/docker-compose.yml` 可选 profile `worker`；或宿主机 `celery -A app.scheduler.celery_app.celery_app worker -l info`。

### 第六轮：RAG 指标口径修正

- **nDCG source 级去重**：同一来源的多个 chunk 不再重复贡献相关性，避免 nDCG 大于 1。
- **回归保护**：新增重复 chunk 用例，明确断言 `0 ≤ nDCG ≤ 1`；修正后黄金集 nDCG@5=0.9473。

### 第五轮：收口六项（session/授权/调度/门禁）

- **Session tree**：branch marker **自身为 active leaf**；fork 后 append 走新分支；JSONL 跨 service resume 保留新分支并排除旧分叉；forward parent **fail closed**。
- **Journal 并发**：同 session `RLock` 原子 append；内存/JSONL **50 并发**不丢；JSONL **仅同进程**（跨进程需外锁/DB）。
- **HITL 权限**：suspend 保存**当时** discovery grant；resume = 当前 allowlist ∩ 旧 grant；中文「建任务/建缺陷」选对 connector。
- **对象级授权**：session_meta owner/org **不可变**；chat/resume/context/task/cancel 校验 owner/admin；BFF 传 principal。
- **Scheduler**：状态锁内更新并写 journal；新 service 从 journal 重建投影；未终态标 `orphaned/needs_resume`。
- **Story gates**：R4 **StepEngine** checklist wall 负例阻断；X1 `cross_req_align` 消歧未决 embed 无写回；H5 按 citation `classification/write_class/source` 检泄露。
- **测试**：并发 append、跨 repo fork、跨用户拒绝、resume 交集、task/defect 意图；`run_all` 全绿。

### 第四轮：行为完整性与测试加强（逐行复审修复）

- **Session tree**：`fork_from()` 写 branch marker；resume 恢复 active leaf；`build_context` 沿 parent 链；duplicate/missing parent/cycle/跨 session **fail closed**。
- **Compaction**：`DeterministicExtractiveSummarizer`（可换 `Summarizer` protocol）；只压 active path 未覆盖段；`covered_until_id` 指向真实最后条目；迭代合并 prior 摘要；完整日志保留。
- **JSONL 校验**：除 JSONDecodeError 外校验 entry_type/id 唯一/parent/session schema。
- **Bounded agent loop**：tool 后 append observation 并 **continue**；MockPlanner 见 tool_result 再 answer、不重复调同一工具；HITL 从 `pending_suspend` 恢复；reject → `terminal=rejected`；**每 run 新建 BudgetTracker**。
- **权限**：`tool_allowlist=None` 才默认；`[]` = deny all；resume 不得放宽 suspend 时 allowlist。
- **Discovery**：递归净化 descriptor/schema 字符串；`min_score` 阻断 0 分无关 grant；grant 带 score/reason 审计。
- **Scheduler**：合作式 `CancellationToken`（副作用前 `check()`；**不可强杀线程**）；任务状态写 journal；重启未终态 → `orphaned/needs_resume`；终态锁内不可覆盖。
- **Story gates**：`must_recall` 断言 hits/briefing；R4 负例 checklist 阻断；X1 消歧未决不写回；H5 查 series + RAG citations；报告 `fixtures/eval/story_gates_report.json`。
- **BFF 测试**：同 session 恢复、branch/compaction、HITL approve/reject、空 allowlist、两轮 observation、cancel 副作用前生效、orphan。

### 第三轮能力补齐（记忆 / Agent loop / 发现 / 调度 / 门禁）

- **Session journal（pi 模式）**：JSONL/in-memory repository；compaction + `build_context`；坏尾 fail closed。
- **Bounded agent loop（Claude Code 模式）**：planner → PreToolUse deny-first → ToolRuntime；HITL suspend/resume 重算 grant。
- **Lazy tool discovery（Ch4）**：catalog summary → policy → 词法排名 → lazy schema；MCP `tools/list` 默认 summary-only。
- **In-process scheduler**：Pipeline 后台跑；cancel → `terminal=cancelled`。
- **Story gates（Ch6）**：`fixtures/eval/story_gates.yaml` + `run_all` 门禁。
- **上下文诚实性**：RAG 改称 bounded multi-hop rule rewrite；`embedding_report()` 暴露 provider_kind/fallback。

### 主路径修正（事实与路由）

- **Orchestrator 按 `orchestration_mode` 路由**：`sop` → `sop_executor`；`playbook` → `playbook_executor`；未知 → L0 fallback。
- **阶段式状态机**：`StepEngine` 逐步执行；未知 step/hook/tool **fail closed**（不得静默 ok / 回退 connector）。
- **Skill Pack 运行时校验**：schema / checklist / 成功标准参与 validate & evaluate。
- **Series ↔ Continuum 安全桥接**：`SeriesOpenItem` 携带 org/classification/write_class/ACL；Continuum 拒绝则**不**进 SeriesStore；briefing 按 user/org/ACL 过滤；`none` 不索引不返回。
- **Usage 诚实标注**：`measurement_mode=simulated`；`llm_tokens_simulated` 非实测值。
- **测试**：`tests/orchestrator/test_routing.py` + `test_security_regression.py`。

### RAG / 管线（此前）

- **真分块**：不再整篇单块入库；文档按标题切、转写按说话人轮次合并，可配置 size/overlap。
- **转写入库**：`index_transcript` / `KnowledgePlane.ingest_transcript`，chunk 带 speaker/start_ms/section。
- **测评门禁**：黄金集 + Hit@k/MRR/nDCG/Faithfulness，接入 `run_all`。
- **可用问答**：Dialog/BFF 知识问题返回 grounded 摘录与 citation，而非纯回声。
- **转写回调闭环**：BFF `internal_transcripts` 带 segments → RAG 索引；`FullRuntime` 理解后自动入库。
- **Orchestrator 隔离**：`begin_run()` 防止多场景连续跑时 retrieve 预算串台。
- **L3 评测**：`maturity=L3` 走 `IndependentLLMEvaluator`（Mock）。

## 目录

对齐架构 03 §6 的 `app/` 树；本仓库根下用 `jiyaojun/` 包装，与 preview / 书稿隔离。
