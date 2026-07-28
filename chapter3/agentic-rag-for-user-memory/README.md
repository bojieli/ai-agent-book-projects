# Agentic RAG for User Memory / 面向用户记忆的 Agentic RAG

> Companion material for *AI Agents in Depth*, Chapter 3 — agentic multi-hop retrieval over conversation memory with offline demo and optional pipeline backend.  
> 配套《深入理解 AI Agent》第 3 章——对话记忆上的 Agentic 多跳检索；含离线演示与可选检索流水线。

← [Chapter 3 index / 返回第 3 章目录](../README.md)

---

## English

### Learning objectives

1. Chunk long conversations for indexing  
2. Integrate external retrieval pipelines (hybrid search)  
3. Agentic RAG with tool-calling and ReAct  
4. Evaluate memory with automatic LLM scoring  
5. Optimize retrieval for conversation queries  
6. Integrate evaluation frameworks across projects  

### Architecture

```
User Memory Test Cases (60 cases, 3 layers)
        → Conversation Chunker (~20-round segments + overlap + enrichment)
        → External Retrieval Pipeline (port 4242) or local BM25
             Dense + Sparse hybrid
        → Agentic RAG Agent (ReAct; search_memory / get_conversation_context / get_full_conversation)
        → LLM Evaluation (reward 0–1, pass/fail, reasoning)
```

### Key concepts

1. **Conversation chunking** — ~20 rounds, searchable, contextual, efficient  
2. **Hybrid retrieval** (optional pipeline) — dense + BM25 + fusion; scalable  
3. **Agentic RAG** — Reason → Act → Observe → iterate  
4. **LLM evaluation** — integrates user-memory-evaluation style scoring (≥0.6 pass)  
5. **Contextual enrichment** — metadata, neighbors, tags  

### Prerequisites

- Python 3.8+  
- **Port 4242 pipeline is OPTIONAL.** Default `retrieval_backend="auto"`: use pipeline if reachable, else **built-in local BM25** (offline).  
- API keys only for LLM modes (`batch` / `interactive` / `demo`).  
- **`--mode offline-demo` needs NO API key and NO port 4242.**  

### Installation

```bash
cd chapter3/agentic-rag-for-user-memory
pip install -r requirements.txt
cp env.example .env
# Edit API keys
```

### Retrieval backend

| value | behavior |
|-------|----------|
| `auto` | default — pipeline if up, else local BM25 |
| `local` | always offline BM25 |
| `pipeline` | always port 4242 |

Optional pipeline:

```bash
cd ../retrieval-pipeline
python api_server.py   # http://localhost:4242
```

### Running

```bash
# Offline multi-hop vs naive recall (no API, no 4242)
python main.py --mode offline-demo
python offline_demo.py
python offline_demo.py --output results/offline_demo.json

python test_pipeline.py
python main.py
python main.py --mode demo
python main.py --mode batch --category layer1 --backend local
```

CLI: `--mode {interactive,batch,demo,offline-demo}`, `--category`, `--test-id`, `--query`, `--provider`, `--model`, `--index-mode {dense,sparse,hybrid}`, `--backend {auto,local,pipeline}`, `--top-k`, `--rounds-per-chunk`, `--store-path`, `--test-cases-dir`, `--output`, `--config`. See `python main.py --help` (Chinese).

### Offline demo results (reproducible)

On `layer2_01_multiple_vehicles` (Honda + Tesla across sessions), real BM25:

| metric | naive single-query | agentic multi-hop |
|--------|:------------------:|:-----------------:|
| retrieval queries issued | 1 | 5 |
| memory chunks retrieved | 3 | 5 |
| decisive-evidence recall | **50%** | **100%** |
| can fully disambiguate & answer | no | yes |

Naive is dominated by “schedule service” keywords and misses Honda confirmation (`FS-447291`). Agentic discovers the second vehicle, issues focused follow-ups, recovers evidence. Numbers from actual retrieval, not hard-coded.

### Interactive options

Load / view test cases; configure chunking/index/agent; evaluate single or by category; generate reports.

### Example code

```python
from config import Config
from evaluator import UserMemoryEvaluator

config = Config.from_env()
evaluator = UserMemoryEvaluator(config)
test_cases = evaluator.load_test_cases(category="layer1")
result = evaluator.evaluate_test_case("layer1_01_bank_account")
report = evaluator.generate_report("results/evaluation_report.txt")
```

### Config highlights

```python
config.chunking.rounds_per_chunk = 20
config.chunking.overlap_rounds = 2
config.index.mode = "hybrid"
config.index.enable_contextual = True
config.agent.max_search_results = 5
config.evaluation.max_iterations = 10
```

### Test layers

- **L1** simple retrieval — “What is my checking account number?”  
- **L2** multi-conversation — “Which vehicle needs service first?”  
- **L3** complex reasoning — “What urgent issues before my trip?”  

### Components

`chunker.py`, `indexer.py`, `tools.py` (`search_memory`, `get_conversation_context`, `get_full_conversation` — full content), `agent.py` (ReAct), `evaluator.py`.

### Metrics / troubleshooting

Success rate, LLM reward, iterations, tool calls, latency, index time.  

**Top-k:** pipeline uses `top_k` (candidates) and `rerank_top_k` (final).  
**LLM eval missing:** need evaluator API + criteria.  
**Pipeline down:** not fatal with `--backend auto`; force offline with `--backend local`.

### Related

`user-memory`, `user-memory-evaluation`, `agentic-rag`, `contextual-retrieval` (chapter3 paths).

### License

Educational curriculum materials.

---

## 中文

### 学习目标

1. 长对话分块索引  
2. 对接外部混合检索流水线  
3. 工具调用 + ReAct 的 Agentic RAG  
4. LLM 自动打分评测记忆  
5. 面向对话查询的检索优化  
6. 跨项目评估框架集成  

### 架构

用户记忆用例 → 对话分块（约 20 轮 + 重叠 + 上下文增强）→ 外部流水线（4242）或本地 BM25 → Agentic Agent（ReAct 记忆工具）→ LLM 评估。

### 关键概念

分块、混合检索、Agentic ReAct、自动 LLM 评测、上下文增强——与 English 节一致。

### 前置条件

Python 3.8+。**4242 流水线可选**；默认 `auto` 回退本地 BM25。仅 LLM 模式需 API Key。**`offline-demo` 无需 Key 与 4242。**

### 安装与后端

```bash
cd chapter3/agentic-rag-for-user-memory
pip install -r requirements.txt
cp env.example .env

# 可选
cd ../retrieval-pipeline && python api_server.py
```

| 值 | 行为 |
|----|------|
| `auto` | 默认可达则用流水线，否则本地 BM25 |
| `local` | 始终离线 BM25 |
| `pipeline` | 始终 4242 |

### 运行

```bash
python main.py --mode offline-demo
python offline_demo.py
python offline_demo.py --output results/offline_demo.json

python test_pipeline.py
python main.py
python main.py --mode demo
python main.py --mode batch --category layer1 --backend local
```

CLI 标志见 English 节；`python main.py --help` 含中文说明。

### 离线演示结果

`layer2_01_multiple_vehicles` 上 naive 证据召回 **50%**、agentic **100%**（见 English 表）。

### 配置、用例层级、组件

`config.py` 分块/索引/Agent 参数；L1/L2/L3 用例；`chunker` / `indexer` / `tools` / `agent` / `evaluator`。

### 故障排查

Top-k 需同时设 `top_k` 与 `rerank_top_k`；流水线不可达时用 `--backend auto/local`；LLM 评测需有效 Key 与 `evaluation_criteria`。

### 相关与许可

见同章 `user-memory`、`user-memory-evaluation`、`agentic-rag`、`contextual-retrieval`。教学用途。

---

## Notes / 说明

### OpenRouter 通用回退 / Universal OpenRouter fallback

If primary keys are absent and `OPENROUTER_API_KEY` is set, chat LLM routes through OpenRouter with automatic model mapping. See `env.example`.
