# RAG 与 Embedding 选型（必做）

> 对齐架构 **v7.7** §2.4 / §2.19 · 实现：`jiyaojun/app/knowledge/rag.py` · `embedding.py`  
> 决策记录：[DECISIONS.md ADR-011](./DECISIONS.md)  
> **诚实声明**：本仓库为脱敏重建版；**CI/本地默认 `bge-m3-shim` + 内存索引**，不得对外宣称「生产 BGE-M3 已部署完成」。

---

## 1. 为什么纪要君必须做真 RAG（不是点缀）

1. 行内文档是事实源：制度、接口规范、策略说明、检查清单——没有 RAG 只能通识猜。  
2. 会是连续体：上次 Go 条件、整改 open 项、经营动作必须从 Continuum 召回。  
3. 书 Ch3：长期能力在可检索外部化知识，不是把历史塞进当前 context。

---

## 2. Embedding 选型结论

### 选定：**BGE-M3**（BAAI/bge-m3）

| 维度 | 结论 |
|------|------|
| 主模型 | **BGE-M3** |
| 通道 | **同一模型产出 Dense + Sparse（lexical weights）**，可选 multi-vector |
| 部署 | 开源权重，**可私有化/行内推理**，满足金融数据不出域 |
| 备选 | 若行内已统一采购且评测不低于 M3：可换，但须保持 Hybrid 双通道契约 |
| CI/无权重环境 | `bge-m3-shim`（同接口双通道；**不得宣称生产 embedding**） |
| 索引后端（本仓库） | **内存 `MockHybridIndex`**；CI 全绿 ≠ 生产 Milvus/ES 已上线 |

### 为什么选 BGE-M3（对照否决项）

| 候选 | 为何不作为默认 |
|------|----------------|
| **OpenAI text-embedding-3-*** | 默认出域；无内置 sparse；采购与审计链路长；与「先原则后商品名」冲突若绑死云 API |
| **纯 m3e / bge-small-zh 仅 dense** | 中文够用，但架构 **Hybrid Dense+Sparse 必做**；制度文号、策略 ID、服务名靠 sparse，单 dense 易漏专名 |
| **纯 BM25/ES sparse only** | 语义召回弱（「上次那个超时约定」类改写 query） |
| **多向量模型拼凑两套服务** | 运维双栈；版本漂移；M3 已统一 dense+sparse 出口 |
| **多语言通用但中文弱的小模型** | 纪要君语料以中文金融黑话为主 |

### 正向理由（必须写进评审）

1. **对齐架构契约**：§2.19 Hybrid Dense+Sparse；M3 原生双通道，避免「先 dense 召回再补关键词」的假 Hybrid。  
2. **中文金融场景**：制度条文、策略 ID、灰度/Shadow 等短专名 + 长文档段落并存；M3 对 short query / long passage 都有公开评测支撑。  
3. **行内可落地**：开源可私有化；不把会议/制度原文默认送出公有云。  
4. **与条线分库兼容**：embedding 与索引元数据分离；ACL/`org_domain`/`write_class` 在算相似**之前**过滤（§2.4.2）。  
5. **可替换**：`EmbeddingProvider` 接口稳定；换行内自研模型只换 Provider，不改 RAG 管线。

### 运行配置

```bash
# 生产/集成（需安装 FlagEmbedding 或 sentence-transformers 并拉权重）
export JIYAOJUN_EMBEDDING=bge-m3

# 本地 CI / 无 GPU（默认）：同接口 shim，测试管线与契约
export JIYAOJUN_EMBEDDING=bge-m3-shim
```

运行时报告（禁止误称 CI shim 为生产模型）：

```python
from app.knowledge.embedding import embedding_report
embedding_report()  # → provider_kind, model_id, fallback, ci_default
```

---

## 3. RAG 管线（实现必须具备）

```text
Query（purpose + 议程 + org_domains + series/project）
  → ACL / org_domain / classification **预过滤**
  → Hybrid：Dense(BGE-M3) + Sparse(M3 lexical)
  → 轻量 Rerank（同域加权 + open Continuum 加权）
  → Contextual chunk 已在入库时打前缀（制度/项目/会议）
  → 召回不足 → **bounded multi-hop rule rewrite**（确定性；预算封顶；非 LLM Agentic）
  → 返回摘录 + references[] citation（禁止灌整本手册）
```

语料两库：**docs** / **continuum**，索引与鉴权分离；critical 默认 sealed，禁止 wide。

---

## 4. 分块策略（已落地）

| 语料 | 策略 | 说明 |
|------|------|------|
| 制度/文档 | 标题分段 + overlap 软窗 | 不同 `##/决议/待办` 段落不盲目合并，便于按主题召回 |
| 会议转写 | **说话人轮次**合并到字符预算 | 不在一句/一轮中间切开；保留 speaker、start_ms/end_ms、section |
| 索引前缀 | Contextual prefix | `[corpus][org_domain][title][meeting][section][speakers][chunk]` |

实现：`jiyaojun/app/knowledge/chunking.py` → `RagPipeline.index_doc` / `index_transcript`。

**相关（非 RAG 本体）**：会前 Dialog 的 session tree / compaction / Mock agent loop 见 `jiyaojun/app/memory/` 与 `05 §6.7`；**合作式 cancel** 见 `05 §6.8`。

## 5. 检索评测

黄金集：`jiyaojun/fixtures/eval/rag_golden.yaml`（文档 / 转写 / Continuum / ACL 负例）。

指标：Hit@k、Recall@K、MRR、nDCG@k、Faithfulness；ACL 拒绝用例期望空召回。失败打印 `RAG_EVAL_FAILED` 且非零退出（已接入 `run_all`）。

```bash
cd jiyaojun
./.venv/bin/python -m pytest tests/rag -q
./.venv/bin/python -m app.eval.retrieval_quality
./.venv/bin/python -m app.eval.verify_features   # 含 rag / chunking / grounding / retrieval_quality
```

## 6. 后续改进方向

1. 生产向量库（ES/pgvector）替换内存 HybridIndex，保持 ACL 预过滤契约。  
2. 转写 topic segmentation（LLM/规则）替代纯关键词 section。  
3. 扩大黄金集至 50–100 query；抽样人工 faithfulness。  
4. Reranker 独立模型（当前为轻量规则加权）。
