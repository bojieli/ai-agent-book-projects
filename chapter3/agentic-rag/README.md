# Agentic RAG System / Agentic RAG 系统

> Companion material for *AI Agents in Depth*, Chapter 3 — **Experiment 3-9**: ReAct agentic vs non-agentic RAG on Chinese legal Q&A; offline multi-hop evidence recall.  
> 配套《深入理解 AI Agent》第 3 章 **实验 3-9**：ReAct 式 Agentic vs 非 Agent 式 RAG 司法问答；离线多跳证据召回对比。

← [Chapter 3 index / 返回第 3 章目录](../README.md)

---

## English

### Features

- **Agentic RAG (ReAct)**: iterative reason + tool search  
- **Non-agentic RAG**: single retrieve + answer (for compare)  
- **LLM providers**: Kimi/Moonshot, Doubao, SiliconFlow, OpenAI, OpenRouter, Groq, Together, DeepSeek  
- **Knowledge bases**:  
  - **Offline BM25** (built-in, zero deps) over bundled `laws/` — no server/API for retrieval  
  - Local retrieval pipeline (`../retrieval-pipeline`)  
  - Dify KB API  
- Chunking with paragraph respect; evaluation on Chinese legal data; conversation history; verbose logs  

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

```bash
# LLM keys (set the ones you use)
MOONSHOT_API_KEY=...
ARK_API_KEY=...
SILICONFLOW_API_KEY=...
OPENAI_API_KEY=...
OPENROUTER_API_KEY=...
GROQ_API_KEY=...
TOGETHER_API_KEY=...
DEEPSEEK_API_KEY=...

KB_TYPE=local  # "offline" | "local" | "dify"
DIFY_API_KEY=...
DIFY_DATASET_ID=...

LLM_PROVIDER=kimi
LLM_MODEL=kimi-k3
```

### Usage

#### 0. Zero-dep offline compare (recommended first; no API / no external service)

Core claim: **for complex questions, agent-style multi-hop / decomposed retrieval recalls evidence much better than a single query**. `compare_offline.py` uses built-in offline BM25 (`offline_retriever.py` over `laws/`) on a small Chinese judicial QA set—**fully offline, no API key**:

```bash
python compare_offline.py
# optional: --corpus laws  --top-k 5  --dataset evaluation/offline_qa.json  --output result.json
```

Real output (measured; 21372 law chunks / 288 docs):

```
问题                          难度    单次检索    分解检索    检索次数
------------------------------------------------------------------------------
故意伤害致人重伤的，如何处…  easy    100%        100%        1 → 1
正当防卫是怎么规定的？        easy    100%        100%        1 → 1
醉酒驾驶机动车如何处罚？      easy    100%        100%        1 → 1
故意杀人罪判几年？            hard    0%          100%        1 → 1
盗窃罪的立案标准是什么？      hard    0%          100%        1 → 1
诈骗罪的量刑标准是什么？      hard    0%          100%        1 → 1
醉酒过失致人重伤且有盗窃前…  hard    33%         100%        1 → 3
------------------------------------------------------------------------------
聚合指标（平均证据召回率）:
  全部                                48%         100%        1.0 → 1.3
  简单题                              100%        100%        1.0 → 1.0
  复杂题                              8%          100%        1.0 → 1.5
```

Reading (aligned with Exp. 3-9): **easy questions ~tied at 100%**; **hard/poorly phrased: 8% → 100%**. Metric is pure retrieval **evidence recall** (upper bound on answer quality). Gold statutes are confirmed present in `laws/`.

> Offline mode uses pre-labeled `subqueries` for “agent decomposed search” to isolate **retrieval strategy**; real systems generate subqueries in the ReAct loop. End-to-end answer quality: `evaluation/evaluate.py` (needs API key).

Full agent on offline KB (retrieval offline; **answer generation** needs API):

```bash
python main.py --kb-type offline --query "醉酒过失致人重伤且有盗窃前科如何量刑"
python main.py --kb-type offline --query "故意杀人罪判几年" --mode compare
```

#### 1. Start retrieval pipeline (for local KB)

```bash
cd ../retrieval-pipeline
python main.py
# http://localhost:4242
```

#### 2. Index documents

```bash
python index_local_laws.py
python index_local_laws.py --categories 宪法 民法典
python index_local_laws.py --max-docs 10

python main.py --index path/to/document.txt
python main.py --index path/to/documents/
python main.py --index documents/ --chunk-size 2048
```

#### 3. Run Agentic RAG

```bash
python main.py
python main.py --mode non-agentic
python main.py --verbose
python main.py --no-verbose

# Single query
python main.py --query "宪法第一条是什么？" --mode agentic
python main.py --query "盗窃罪的立案标准是什么？" --mode non-agentic
python main.py --query "故意杀人罪判几年？" --mode compare

# Batch
python main.py --batch queries.txt --output results.json
python main.py --batch queries.txt --mode non-agentic

# Providers
python main.py --provider openai --model gpt-5.6-luna
python main.py --provider doubao --model doubao-seed-1-6-thinking-250715
python main.py --provider siliconflow --query "你好"
```

Interactive: type questions; `quit`/`exit`; `clear` history; `mode` switch agentic/non-agentic.

#### 4. Evaluation

```bash
cd evaluation
python dataset_builder.py
python evaluate.py
python evaluate.py --provider kimi --kb-type local --output custom_results
```

### Project structure

```
agentic-rag/
├── config.py, agent.py, tools.py
├── offline_retriever.py, compare_offline.py
├── chunking.py, main.py, index_local_laws.py
├── quickstart.py, test_simple.py, requirements.txt
├── laws/   # Chinese law tree (宪法…程序法)
└── evaluation/
    ├── dataset_builder.py, offline_qa.json, evaluate.py
```

### How it works

**Agentic:** reason → `knowledge_base_search` → iterate → optional `get_document` → synthesize with citations → memory for follow-ups.

**Non-agentic:** one search with raw query → top-K in prompt → one LLM answer.

### Config knobs

`local_top_k`, `--verbose` / `--no-verbose`, `temperature` in `config.py`.

### Evaluation results

**Retrieval layer (offline, reproducible):** table in §0 — hard questions **8% → 100%** evidence recall.

**Generation layer (needs API):** `evaluation/evaluate.py` — success/key-concept recall, latency, citation coverage. Agentic: better multi-facet coverage and citations; slower. Non-agentic: faster; weaker on ambiguous queries.

### Troubleshooting

```bash
curl http://localhost:4242/health
cd ../retrieval-pipeline && python main.py

python index_local_laws.py
ls -la document_store.json
curl http://localhost:4242/stats
```

API keys: check env / `.env`. Indexing needs pipeline up and UTF-8 files when using local mode.

### License

Educational project.

---

## 中文

### 功能特性

- **Agentic RAG（ReAct）** 与 **非 Agentic RAG** 对照  
- 多 LLM 提供商；知识库：**离线 BM25** / 本地检索流水线 / Dify  
- 分块、中文法条评测、多轮对话、详细日志  

### 安装与配置

```bash
pip install -r requirements.txt
```

环境变量见 English 节（`MOONSHOT_API_KEY` 等；`KB_TYPE=offline|local|dify`）。

### 用法

#### 0. 零依赖离线对比（推荐先跑）

```bash
python compare_offline.py
```

实测证据召回表见 English 节：简单题两种范式均约 100%；复杂题 **8% → 100%**。也可用：

```bash
python main.py --kb-type offline --query "醉酒过失致人重伤且有盗窃前科如何量刑"
python main.py --kb-type offline --query "故意杀人罪判几年" --mode compare
```

#### 1–4. 流水线、索引、运行、评测

```bash
cd ../retrieval-pipeline && python main.py

python index_local_laws.py
python index_local_laws.py --categories 宪法 民法典
python main.py --index path/to/documents/ --chunk-size 2048

python main.py
python main.py --mode non-agentic
python main.py --query "宪法第一条是什么？" --mode agentic
python main.py --query "故意杀人罪判几年？" --mode compare
python main.py --batch queries.txt --output results.json
python main.py --provider openai --model gpt-5.6-luna

cd evaluation && python dataset_builder.py && python evaluate.py
```

交互命令：`quit`/`exit`、`clear`、`mode`。

### 项目结构与原理

与 English 节相同：`offline_retriever.py` / `compare_offline.py` / `laws/` / `evaluation/`。  
Agentic：多轮检索+引用；Non-Agentic：单次检索注入 prompt。

### 结果解读

检索层见 §0 表；生成层用 `evaluation/evaluate.py`（需 API）。Agentic 覆盖更全、更慢；Non-Agentic 更快、对复杂/歧义问题更弱。

### 故障排查

检查 `http://localhost:4242/health`、是否已 `index_local_laws.py`、API Key 与 UTF-8 编码。

### 许可

教学项目。

---

## Notes / 说明

### OpenRouter 通用回退 / Universal OpenRouter fallback

Primary provider keys take precedence; else `OPENROUTER_API_KEY` routes chat via OpenRouter with model id mapping. See `env.example`. Related: [`../agentic-rag-for-user-memory/`](../agentic-rag-for-user-memory/).
