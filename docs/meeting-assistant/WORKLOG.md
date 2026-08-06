# 纪要君 Phase 0 / V1 契约落地工作日志

> 持续追加。每步含：**做了什么 · 自审结论 · 决策理由**。  
> 权威对照：[03](./03_架构v7_对照李博杰实验与全场景.md) · [06](./06_优先故事成熟度表.md) · [01 §12 Phase 0](./01_架构与实现规划.md) · [DECISIONS](./DECISIONS.md)

---

## 2026-08-03 · Session 续作

### S0 · 范围钉死（Review: PASS）

**做了什么**  
核对 06 V1 必交付 12 行；钉死「全部完成」= V1 Pack 齐备 + Phase 0 DoD 可跑 + DDL/事件/ADR/日志。  
**硬约束（用户）**：代码写入**新目录**；**不修改** `jiyaojun-preview/` 原始纪要君。

**决策理由**  
绿场与 preview 物理隔离（ADR-008），避免双栈与人情债。

---

### S1 · V1 Skill Packs 全量（Review: PASS）

**做了什么**  
在 `docs/meeting-assistant/samples/skills/` 补齐：R1/R5/B4/B5/H2/H5/K5/X1/general（既有 R4/K1/C2）。  
规则自审：`mode=sop` 必有 `sop/steps.yaml`；`mode=playbook` **无**假 SOP；critical → sealed + block。

**决策理由**  
按 06 矩阵字段一字对齐；playbook 禁止 invent SOP（03/ADR-002）。

---

### S2 · 绿场代码 `jiyaojun/`（Review: 跑冒烟）

**做了什么**

| 路径 | 内容 |
|------|------|
| `jiyaojun/migrations/001_phase0.sql` | 03§4 + 05 必建表 + org_domain seed |
| `jiyaojun/app/events/` | 08 事件枚举 + 内存 EventLog |
| `jiyaojun/app/harness/` | ToolRuntime（allowlist + effect cap） |
| `jiyaojun/app/connectors/` | mock task/defect + 禁生产 connector |
| `jiyaojun/app/policy/` | embed_gate max_strict / hooks |
| `jiyaojun/app/render/` | **先 acl_view** 再 Jinja 邮件 |
| `jiyaojun/app/observability/` | trace + usage |
| `jiyaojun/app/governance/` + fixtures | draft/approved 门禁 |
| `jiyaojun/app/planes/pipeline/phase0.py` | DoD 路径 |
| `jiyaojun/app/demo/phase0_smoke.py` | 冒烟入口 |
| `jiyaojun/app/eval/smoke_skills.py` | 12 Pack 结构门禁 |
| symlinks | `app/skills` → samples；playbook/render/envelope |

**未改**：`jiyaojun-preview/**` 任何文件。

**决策理由**  
01 Phase 0 完成定义要求假数据跑通主路径；Python 对齐 03 eval 示意。

---

### S3 · 文档交叉链接

更新 `samples/README`、`06` 全包索引、`DECISIONS` ADR-008 目录边界。

---

### S4 · 冒烟与终审（Review: PASS）

**跑测**

- `python -m app.eval.smoke_skills` → **SKILL SMOKE PASSED (12 packs)**  
- `python -m app.demo.phase0_smoke` → **SMOKE PASSED**（含 hitl → work_link.synced → render.completed + usage/trace）  
- `tests/test_policy_render.py` → critical 无 allowlist skip；embed_gate max_strict  

**自审修复**

1. Jinja `payload.items` 与 dict.items 冲突 → 模板改 `payload['items']`  
2. `confirm_only` 在 hitl_passed 时曾跳过 HITL 事件 → 强制 requested/resolved  

**边界确认**：`git diff --name-only -- jiyaojun-preview` 为空；代码仅在 `jiyaojun/` + `docs/meeting-assistant/`。

**本轮完成定义达成**：V1 矩阵 Pack 齐备 + Phase 0 DoD 可跑 + DDL/事件/ADR/WORKLOG。后续 Phase 1+（真日历/真 Connector/向量）不在本轮。

---

### S5 · 按 03 必做能力 1–17 补齐并全量验证（Review: PASS 30/30）

**做了什么**

- 补：Registry / Envelope 校验 / WorkObjectRef / Knowledge(ACL+write_class) / Glossary / Transcript+热词 / Evaluator / CostQuota / PolicyBinding 版本 / Ambiguity / MCP descriptor / Dialog / Orchestrator  
- DoD 改为 mock **缺陷单**（对齐 01 完成定义原文）  
- 修信封样例字段与 schema 一致  
- 新增 `app/eval/verify_architecture.py` + [COMPLETION.md](./COMPLETION.md)

**验证**

```
python -m app.eval.verify_architecture  → Passed 30 Failed 0
python -m app.demo.phase0_smoke         → SMOKE PASSED
```

**决策理由**  
「架构文档全部完成」按文档分期解释为 Phase0+V1 契约/必做清单；Phase1–4 与 §8 后置不得假装已交付。

---

### S6 · Phase 1–4 全量代码 + pytest 门禁（Review: PASS）

**做了什么**

| Phase | 代码 | 测试 |
|-------|------|------|
| 1 | Intent/Schedule/日历通讯录/API/幂等建会 | `tests/phase1` |
| 2 | Understanding/Artifact Map-Reduce/消歧评测 | `tests/phase2` |
| 3 | 持久化缺陷 Connector/WorkEmbed/Delivery 三件套/FullRuntime | `tests/phase3` |
| 4 | 多部门 Connector/词表审批/限流脱敏/Chaos | `tests/phase4` |

全量：`python -m app.eval.run_all`（含 pytest 全绿）。

**决策理由**  
用户要求「所有都做完、代码要写、主要是测试要 review」——以可执行测试作为完成判据，外部系统用可替换适配器，不碰 `jiyaojun-preview`。

---

### S7 · 后置项全部改 Mock（用户：「这些都可以先用模拟的」）

**做了什么**

- Mock LLM Evaluator（新鲜上下文）  
- Mock ASR + 分域热词  
- Mock Hybrid Dense+Sparse（先 ACL）  
- Mock Jira + 企微投递  
- `MockedPlatform` 组装  
- 06 §3 后续 **26** 个 Skill Stub（draft/playbook，无假 SOP）  
- `tests/mocks/test_external_mocks.py`

**验证**：全量 `run_all` / pytest 绿。

---

### S8 · 「能模拟的先模拟，直到全部完成」功能矩阵闭环

**补齐**：BFF 全表面、SOP Runner、图表绑定、AuthZ、MCP Server、系列 Continuum、Skill 治理、夜间容量、幻觉检测、负例可执行、`verify_features` 26 项。  

**门禁**：`run_all` = skills + DoD + architecture30 + features26 + pytest 全绿。  
**结论**：可模拟范围内架构功能已全部完成；真网商品名仍不绑死。

---

### S9 · RAG 主路径落地 + Embedding 选型写清（BGE-M3）

**做了什么**

- 文档：[09_RAG与Embedding选型.md](./09_RAG与Embedding选型.md) + ADR-011  
- 代码：`embedding.py`（BGE-M3 / shim 双通道）、`rag.py`（ACL→Hybrid→Rerank→Agentic→citation）、`KnowledgePlane` 改走真 RAG  
- 测试：`tests/rag/test_rag_pipeline.py`

**选型一句话**：默认 **BGE-M3**，因其原生 Dense+Sparse、中文金融友好、可私有化；CI 用 `bge-m3-shim` 同接口。

---

### S10 · 结构感知分块 + 检索黄金集评测（2026-08-06）

**做了什么**

- `chunking.py`：文档标题分段、转写说话人轮次合并、Contextual 元数据
- `rag.py`：`index_doc`/`index_transcript` 多块入库；`grounded_answer` / grounding faithfulness
- 评测：`fixtures/eval/rag_golden.yaml` + `python -m app.eval.retrieval_quality`（Hit@K / Recall@K / MRR / Faithfulness）
- 测试：`tests/rag` 全绿；文档 `09_RAG与Embedding选型.md` 补分块与评测章节

**一句话**：RAG 从「整篇单块」升级为会议场景可用的分块 + 可跑检索评测。

---

### S12 · 转写回调入库 + Orchestrator 预算隔离 + L3 Eval（2026-08-06）

**问题**
- BFF `internal_transcripts` 只发事件、不入 KnowledgePlane → 内部回调路径半成品
- `FullRuntime` 会后理解未把本场转写索引进 RAG
- `Orchestrator` 同一实例连续 `bind_and_run` 时 `retrieve` 预算串台，第三个 SOP 场景失败

**修复**
- `TranscriptAdapter.from_callback`；BFF 回调带 `segments` 时 `ingest_transcript` 并写回 meeting
- `FullRuntime` 理解完成后索引转写；返回 `transcript_chunks_indexed`
- `Phase0Pipeline.begin_run()` 隔离预算/事件/trace；L3 maturity 走 `IndependentLLMEvaluator`
- 测试：`tests/orchestrator/test_multi_run.py`；BFF/phase3 转写可检索

**验证**：`python -m app.eval.run_all` → **ALL PHASE GATES PASSED**


**问题**：RAG 入库转写 corpus=`transcript` 后，ArtifactEnvelope schema 仍只允许 `docs|continuum` → Evaluator `envelope_invalid` → 流水线卡在 `awaiting_hitl` / 无 work_objects；`run_all` / `verify_architecture` DoD 崩。

**修复**：
- `jiyaojun/app/domain_layer/artifact_envelope.json` + docs schema / `07_Artifact公共信封.md` 增加 `transcript`
- `verify_architecture.verify_phase0_dod` 空 work_objects 时给出明确失败信息而非 IndexError

**验证**：`python -m app.eval.run_all` → **ALL PHASE GATES PASSED**

---

### S13 · 主路径事实修正：orchestration 路由 + Skill Pack 运行时 + Continuum 桥接（2026-08-06）

**审计发现**
- `Orchestrator.bind_and_run` 无视 `orchestration_mode`，恒走硬编码 `Phase0Pipeline`
- Skill Pack 的 steps/schema/success criteria 未驱动主路径
- `MeetingSeriesStore` 与 KnowledgePlane Continuum open-item 语义分裂
- 文档易写成「生产 BGE-M3 已完成」

**修复**
- `Orchestrator` 按 `orchestration_mode` 路由：`sop` → `sop_executor`；`playbook` → `playbook_executor`；未知 → `platform/general` L0 fallback
- `StepEngine` 阶段式状态机（非 ReAct）；`SkillPack` 加载示例 envelope / payload schema / 成功标准；checklist 与 `policy_hooks` 在墙上真实校验
- `SeriesContinuumBridge`：SeriesStore 写入同步 Continuum 索引；briefing 可召回 open items
- 测试：`tests/orchestrator/test_routing.py`（SOP 逐步、playbook 降级、HITL、幂等、Continuum 回流、预算隔离）
- 文档：`COMPLETION.md` / `03` / `05` / `09` 标明脱敏重建、Mock/SPI、CI shim、内存索引

**验证**：`python -m app.eval.run_all` → **ALL PHASE GATES PASSED**

---

### S15 · 第三轮：Session 记忆 / Agent loop / 工具发现 / 调度 / 故事门禁（2026-08-06）

**补齐**
- `app/memory/`：session journal（pi 模式）+ JSONL 原子仓库 + context compaction
- `app/agents/bounded_loop.py`：有界 tool loop（Mock planner）；与会后 SOP 阶段式状态机分离
- `app/connectors/discovery.py`：lazy discovery + description sanitizer；MCP summary-only
- `app/scheduler/`：in-process 后台任务 + cancel
- `app/planes/dialog/session_service.py`：BFF 同 session_id resume
- `app/eval/story_gates.py` + `fixtures/eval/story_gates.yaml`（R5/R4/H5/K1/X1）
- RAG：Agentic → **bounded multi-hop rule rewrite**；`embedding_report()`

**验证**：`python -m app.eval.run_all` → **ALL PHASE GATES PASSED**（含 story_gates + 新增 pytest）

---

### S16 · 第四轮：行为完整化 + 测试/文档（2026-08-06）

**逐行复审发现「名义完成但行为不完整」→ 修复**

| 域 | 修复 |
|----|------|
| Session tree | branch marker 持久化；active path context；validation fail closed |
| Compaction | `DeterministicExtractiveSummarizer`；covered_until 准确；不重复 compact |
| Agent loop | observation→下一轮 planner；HITL 从 journal 恢复；reject terminal；run-scoped budget |
| Allowlist | `[]` deny all；resume 不放宽 |
| Discovery | 递归 sanitizer；min_score；grant 审计 |
| Scheduler | 合作式 cancel；journal 任务状态；orphan on restart；终态锁 |
| Story gates | must_recall 断言 hits；R4/X1/H5 加强；`story_gates_report.json` |
| BFF E2E | `tests/planes/test_dialog_session.py` 等端到端 |

**验证**：`python -m app.eval.run_all` → **ALL PHASE GATES PASSED**（104 pytest）

---

### S17 · 第五轮收口：六项行为边界（2026-08-06）

**收口**
| 域 | 要点 |
|----|------|
| Session tree | branch marker **自身为 leaf**；fork 后 append 新分支；跨 JSONL repo resume 排除旧分叉；forward parent illegal |
| Journal 并发 | per-session RLock 原子 append；50 并发不丢；JSONL **仅同进程** |
| HITL | suspend 存当时 discovery grant；resume = allowlist ∩ grant；中文建任务/建缺陷选对 connector |
| 对象授权 | session owner/org 不可变；BFF 传 principal；chat/resume/context/task/cancel 校验 owner/admin |
| Scheduler | 锁内状态 + journal；新 service 从 journal 重建；未终态 orphan/needs_resume |
| Story gates | R4 **StepEngine** wall 负例；X1 `cross_req_align` embed 无写回；H5 citation 字段防泄露 |

**验证**：`python -m app.eval.run_all` → **ALL PHASE GATES PASSED**（117 pytest；含 nDCG source 级去重与基础设施配置契约）

---

### S14 · Continuum/briefing ACL + fail-closed + usage 模拟标注（2026-08-06）

**问题**
- `continuum_write_class=none` 被改成 `wide` 再 sync → 宽索引泄露
- `DialogPlane.briefing` 硬编码 internal/wide；SeriesStore 标题无 ACL 过滤
- `write_open_item` 先写 SeriesStore 再判 Continuum → 拒绝后 briefing 仍泄露
- 未知 step/hook/tool 静默 ok 或回退 task connector
- `llm_tokens=1200` 固定值冒充实测

**修复**
- `SeriesOpenItem` 携带 org/classification/write_class/ACL；`visible_to()` 过滤 briefing
- `SeriesContinuumBridge.write_open_item`：Continuum 接受后才进 SeriesStore；`none` 完全不索引
- `DialogPlane.briefing` 传入场景 classification/write_class；briefing 按 user/org/ACL 过滤
- `StepEngine`：未知 step/hook/tool fail closed；embed allowlist = step 声明 ∩ 已注册 connector
- usage 标 `measurement_mode=simulated`
- 测试：`tests/orchestrator/test_security_regression.py`

**验证**：`python -m app.eval.run_all` → **ALL PHASE GATES PASSED**

