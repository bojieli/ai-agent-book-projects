# 架构完成确认（对照审计）

> 更新日期：2026-08-06  
> **脱敏重建版**：[`jiyaojun/`](../../jiyaojun/) · 外部系统 Mock/SPI · **禁止改** `jiyaojun-preview/`  
> 全量门禁：`cd jiyaojun && .venv/bin/python -m app.eval.run_all` → **ALL PHASE GATES PASSED**

---

## 0. 诚实边界（必读）

| 项 | 本仓库状态 |
|----|-----------|
| 架构形态 | 生产架构的**脱敏重建**；非线上实例 |
| 外部连接器 | Jira/企微/SSO/ASR 等均为 **Mock / SPI** |
| 编排模型 | **阶段式状态机**（`StepEngine`）；未知 step/hook/tool **fail closed** |
| Continuum briefing | SeriesStore 与 Continuum 桥接；**ACL + write_class 过滤**；`none` 不索引不返回 |
| Usage 计量 | **`measurement_mode=simulated`**；token/耗时为演示值非实测 |
| Embedding | **CI 默认 `bge-m3-shim`** + **内存索引**；`embedding_report()` 暴露 fallback |
| Session 记忆 | journal=短期轨迹；Continuum=跨会；Glossary=术语；**三者不混** |
| Agent loop | **Mock planner** 有界循环（tool→observation→再决策）；会后 SOP 仍阶段式状态机 |
| 调度/MQ | **in-process** + **合作式 cancel**（不可强杀线程）；重启 orphan；无真实 MQ |
| Session compaction | **DeterministicExtractiveSummarizer**（非 LLM 假摘要） |
| Journal 并发 | 同 session **RLock** 原子 append；JSONL **仅同进程**多线程安全 |
| 对象级授权 | session owner/org **不可变**；BFF 传 principal；跨用户拒绝 |

---

## 1. 结论：**可模拟范围内全部完成**

| 范围 | 状态 | 验证 |
|------|------|------|
| Phase 0–4 | **完成** | smoke + pytest phases |
| 03 §9 必做 1–17 | **完成** | `verify_architecture` 30/30 |
| 05 BFF/管理端/内部回调 | **完成（Mock）** | `BffApp` + `tests/features` |
| **Session journal + compaction** | **完成** | branch marker=active leaf · 50 并发不丢 · forward parent fail closed |
| **Bounded agent loop** | **完成（Mock planner）** | observation 多轮 · HITL suspend/resume · reject terminal |
| **Lazy tool discovery** | **完成** | min_score · 递归 sanitizer · grant 审计 |
| **In-process scheduler** | **完成** | **合作式 cancel** · journal 状态 · orphan on restart |
| **Story gates Ch6** | **完成** | R4 StepEngine wall · X1 cross_req_align · H5 citation 字段 · `story_gates_report.json` |
| Playbook 降级 | **完成** | `playbook_executor` + `platform/general` L0 fallback |
| Skill Pack 运行时校验 | **完成** | `SkillPack` schema / checklist / 成功标准参与 validate & evaluate |
| 系列 Continuum | **完成** | `MeetingSeriesStore` + `SeriesContinuumBridge`（统一 open items） |
| 图表绑定 / 禁臆造 | **完成** | `render/charts.py` |
| AuthZ + 审计 | **完成** | `MockAuthZ` |
| MCP Server | **完成** | `MockMcpServer` tools/list+call |
| Skill/词表治理 | **完成** | SkillAdmin + GlossaryAdmin |
| 夜间容量策略 | **完成** | `ops/capacity.py` |
| 幻觉检测 | **完成** | `detect_hallucination` |
| ASR / 向量 / Jira / 企微 / LLM Eval | **完成（Mock）** | `tests/mocks` |
| **RAG 主路径 + Embedding 选型** | **完成（CI shim）** | [09](./09_RAG与Embedding选型.md) · ADR-011 · `tests/rag`；**生产 BGE-M3 需单独部署** |
| **结构感知分块 + 检索测评** | **完成** | `chunking.py` · `retrieval_quality` · `rag_golden.yaml` |
| **Grounded 问答（Dialog/BFF）** | **完成** | `grounding.py` · `DialogPlane.ask` · BFF 知识聊天 |
| **内部转写回调 → RAG 入库** | **完成** | BFF `internal_transcripts` + `FullRuntime` 理解后 `ingest_transcript` |
| **Orchestrator 多场景隔离** | **完成** | `begin_run()` 预算/事件/trace 不串台；`orchestration_mode` 真路由 |
| **L3 独立 LLM Evaluator** | **完成** | `Phase0Pipeline` maturity=L3 走 `IndependentLLMEvaluator` |
| 负例目录可执行 | **完成** | `run_negative_catalog` |
| 功能矩阵 31 项 | **完成** | `verify_features` 31/31 |
| V1 12 Pack + 26 backlog Stub | **完成** | 38 SKILL.md |
| 03 §8 V1 不做（实时语音等） | **接口预留** | `VoiceInterfaceStub` |

**仍不绑死商品名 / 不接真网**：ASR 供应商、向量库品牌、真实 SSO——契约与 Mock 已齐，换适配器即可。

---

## 2. 一键验证

```bash
cd jiyaojun && source .venv/bin/activate
python -m app.eval.run_all
```

期望：

1. SKILL SMOKE PASSED (12 V1)  
2. Phase0 SMOKE PASSED  
3. verify_architecture **30/30**  
4. verify_features **31/31**  
5. **retrieval_quality PASSED**（Hit/MRR/Faithfulness）  
6. **story_gates PASSED**（R4 StepEngine wall · X1 cross_req_align · H5 citation）  
7. pytest **117 全绿**（含 memory 并发 · dialog 授权 · agent loop · nDCG source 去重 · 基础设施配置契约）

---

## 3. 功能矩阵（`verify_features`）

BFF：chat SSE · meetings · HITL · render · admin skills/glossary/quotas/usage · internal transcript/webhook  

平台：AuthZ · SOP runner · charts · hallucination · night capacity · MCP · series continuum · skill admin · LLM eval · ASR · vector · Jira · WeCom · voice stub · negative runners · MockedPlatform · **RAG pipeline · BGE-M3 · chunking · grounding · retrieval_quality**  

---

## 4. 明确排除（架构原文）

- Ch9 会中全双工语音实现（仅 stub）  
- Ch7 RL / Ch8 自动造工具 / 自由设计器  
- 空壳 SOP（backlog 保持 playbook）  
