# 项目升级可验收任务

> 来源：[`PROJECT-UPGRADE-ROADMAP.md`](PROJECT-UPGRADE-ROADMAP.md)。  
> 原则：每个任务必须有可执行验收命令、失败路径和 README 记录；未通过前不进入依赖任务。

## M0 · 领域与架构共识

- [x] 建立两个领域上下文与上下文地图。
- [x] 固化单向安全依赖、商业模型协议、数据出站和双接口安全集成 ADR。
- [x] 明确 12 周范围、功能冻结、SLO 和故障矩阵。

验收：`CONTEXT-MAP.md`、两个 `CONTEXT.md`、`docs/adr/0001～0004` 和升级路线可相互引用且无冲突。

## M1 · Compose Core

### M1.1 分层环境

- [x] 新增仓库级 Compose；Core 默认启动，`worker`、`identity`、`secrets`、`observability` profiles 在后续里程碑加入。
- [x] Core 包含 PostgreSQL、Redis、SeaweedFS（S3）、Qdrant。
- [x] 固定服务名、端口、网络、持久化卷和 ARM64 兼容镜像。
- [x] 不复制安全平台已有数据库迁移职责。

验收：

```bash
docker compose -f deploy/local/docker-compose.yml config
docker compose -f deploy/local/docker-compose.yml up -d
python3 scripts/verify_local_stack.py
```

### M1.2 配置契约

- [x] 提供不含真实凭据的 `.env.example`。
- [x] 统一数据库、Redis、对象存储、向量库和 OpenAI-compatible 模型变量。
- [x] 未配置商业 API Key 时默认离线，不影响现有测试。
- [ ] confidential/critical 不得因配置缺失而降级出站。

验收：配置单测覆盖默认值、缺失凭据、非法 URL、预算上限和高敏出站拒绝。

### M1.3 健康检查

- [x] 检查 PostgreSQL、Redis、SeaweedFS、Qdrant 连通性与 Compose 运行状态。
- [x] 输出机器可读 JSON 与明确退出码。
- [x] Docker 未运行和服务未启动均有明确错误原因；凭据错误随真实适配器在 M2 补齐。

验收：正常环境退出 0；任意停止一个 Core 服务后退出非 0 并指出服务。

## M2 · 纪要君真实数据面

### M2.1 PostgreSQL 持久化

- [x] Meeting Work Unit、Session Journal、任务投影表（`app_task_projection`）、Work Object Link 使用 PostgreSQL 运行时表（`002_app_runtime.sql`）。
- [x] 保留内存实现供单测使用，通过 `JIYAOJUN_STORAGE_BACKEND`（memory|postgres）与 factory 切换。
- [x] 数据迁移幂等（`app_schema_migration` + `python -m app.persistence.migrate`）；进程重启后 meeting / journal / work_link / task_projection 可恢复。
- [x] postgres 模式下 `TaskProjectionJournalHook` 同步写任务投影（`DialogSessionService.with_settings`）。

验收：双 repo 实例读取同一会话；重启后 active branch、HITL 和 work link 不丢失（`tests/integration/test_postgres_persistence.py`）。

### M2.2 Redis 与 Worker

- [x] Redis 保存短期会话投影（`SessionProjectionCache`）、幂等键（`IdempotencyCache`）；`JIYAOJUN_REDIS_BACKEND`（memory|redis）。
- [x] Celery Worker 执行长流水线（`run_pipeline_job` + `CeleryScheduler`）。
- [x] Worker 重启后任务可恢复，不重复写回（`mark_orphaned_on_restart` + `IdempotencyCache.set_nx`）。

验收：执行中重启 Worker，任务最终进入明确终态；外部工作对象只创建一次（`tests/integration/test_celery_worker.py`）。

### M2.3 SeaweedFS 与 Qdrant

- [x] 大转写和大产物进入对象存储（`S3ObjectStore` + `JIYAOJUN_OBJECT_BACKEND=mock|s3`）。
- [x] RAG 使用真实 Qdrant collection（`QdrantHybridIndex` + `JIYAOJUN_VECTOR_BACKEND=memory|qdrant`）。
- [x] Embedding provider 与索引元数据可观测（`embedding_report` + vector payload）。

验收：删除应用进程后重启，历史文档仍可检索；ACL 负例保持空召回（`tests/integration/test_qdrant_seaweed.py`）。

## M3 · 模型与安全控制面

### M3.1 OpenAI-compatible 安全代理

- [x] 纪要君模型调用只指向安全代理。
- [x] 安全代理调用外部商业 API，凭据外置。
- [x] 离线测试使用确定性 provider。

验收：代码和配置扫描不存在纪要君直连外部模型的旁路；无 API Key 时离线门禁全绿。

### M3.2 数据出站与预算

- [x] public/internal 脱敏后允许出站。
- [x] confidential/critical、密封内容、凭据和真实身份阻断出站。
- [x] 输入 8K、输出 2K、每日 100 次、月度 200 元预算可配置但不能被普通调用放宽。
- [x] 商业 Judge 仅处理灰区。

验收：高敏数据测试证明外部 provider 调用次数为 0；预算耗尽后高风险流程 fail-closed。

### M3.3 工具安全授权

- [x] 工具执行前分别计算业务权限和安全风险上限。
- [x] 最终结果取更严格值。
- [x] trace_id、org_domain、policy_binding 贯穿审计。

验收：安全平台无法授予业务侧拒绝的工具；任一安全接口失败不得产生副作用。

```bash
cd jiyaojun
pytest tests/safety/test_m3_safety_gateway.py -q
python -m app.eval.run_all
cd ../llm-safety-platform
pytest tests/test_tools_authorize.py -q
```

## M4 · R1 旗舰闭环

- [x] 技术评审生成结构化会议产物。
- [x] HITL 通过后调用 Jira 模拟器创建缺陷。
- [x] Jira 模拟器支持幂等、超时、失败、回调和状态变化。
- [x] 企微模拟器发送可追踪通知。
- [x] webhook 更新 Work Object Link 和 Continuum。
- [x] 下一场会议 briefing 召回未关闭事项。

验收：同一请求重复运行不会重复建单；关闭缺陷后下一场会议不再列为 open item。

```bash
cd jiyaojun
python -m app.demo.r1_flagship_loop
pytest tests/connectors/test_jira_simulator.py tests/integration/test_r1_flagship_loop.py -q
```

## M5 · 可靠性、安全与观测

- [x] Keycloak 和 OpenBao 作为可选 profile 接入。
- [x] OpenTelemetry 覆盖模型、RAG、HITL、工具授权和写回。
- [x] Prometheus/Grafana/Tempo 提供演示看板与 trace。
- [x] 审计链双副本并发写不会产生未检测分叉。
- [x] 自动运行商业模型超时、Qdrant 暂停、Redis/Worker 重启、重复 webhook、PostgreSQL 不可用、安全阻断和预算耗尽场景。

验收：每个故障均有终态、审计事件、指标和恢复说明。

```bash
# 可选 profile（不进默认 Core）
docker compose --profile identity --profile secrets --profile observability \
  -f deploy/local/docker-compose.yml up -d

cd jiyaojun
python -m app.eval.fault_matrix
pytest tests/eval/test_fault_matrix.py -q

cd ../llm-safety-platform
pytest tests/test_audit_dual_writer.py -q
```

## M6 · 质量与交付

- [x] RAG 黄金集不少于 60 条。
- [x] Agent 主路径与失败故事不少于 30 条。
- [x] ACL、密封数据、跨域越权负例不少于 20 条。
- [x] 商业 Judge 每周 opt-in 100 条、发布前 300 条。
- [x] 满足路线文档中的性能与可靠性目标。
- [x] 提供一键启动、演示脚本、故障演示、操作手册和最终证据报告。
- [x] Compose 验收后再使用 kind 验证 Helm。

验收：新环境按 README 可独立完成启动、正常演示、故障演示和全量门禁。

```bash
./scripts/demo_one_click.sh          # 需 Docker；Core + 演示 + 门禁
./scripts/demo_faults.sh
cd jiyaojun && python -m app.eval.m6_quality_gates
# 商业 Judge opt-in：
cd llm-safety-platform
SAFETY_JUDGE_SAMPLE_LIMIT=100 python -m app.eval.remote_judge_compare
SAFETY_JUDGE_SAMPLE_LIMIT=300 python -m app.eval.remote_judge_compare
# kind+Helm：docs/ops/KIND-HELM.md
```

操作手册：[`ops/OPERATOR-MANUAL.md`](ops/OPERATOR-MANUAL.md) · 证据模板：[`ops/EVIDENCE-REPORT.md`](ops/EVIDENCE-REPORT.md)

