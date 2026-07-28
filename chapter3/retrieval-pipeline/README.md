# Hybrid Retrieval Pipeline with Neural Reranking / 混合检索流水线与神经重排序

> Companion material for *AI Agents in Depth*, Chapter 3 — **Experiment 3-6**: dense + sparse + fusion + rerank, with offline `evaluate.py`.  
> 配套《深入理解 AI Agent》第 3 章 **实验 3-6**：稠密 + 稀疏 + 融合 + 重排，含离线 `evaluate.py`。

← [Chapter 3 index / 返回第 3 章目录](../README.md)

---

## English

### Educational goals

1. **Dense vs sparse**: when each wins and why  
2. **Hybrid search**: combining methods  
3. **Neural reranking**: reorder candidates with transformers  
4. **Parallel processing**: multi-service index/search  
5. **Production-ish patterns**: API design and error handling  

### Architecture

```
┌──────────────────────────────────────────────┐
│            Client Application                 │
└────────────────────┬─────────────────────────┘
                     ▼
┌──────────────────────────────────────────────┐
│         Retrieval Pipeline (Port 4242)        │
│  Document Store (In-Memory)                   │
│  BGE-Reranker-v2 (Local Model)                │
└────────┬──────────────────┬─────────────────┘
         ▼                  ▼
┌─────────────────┐  ┌─────────────────┐
│  Dense Service  │  │  Sparse Service │
│   (Port 4240)   │  │   (Port 4241)   │
│   BGE-M3 Model  │  │   BM25 Engine   │
└─────────────────┘  └─────────────────┘
```

### Key concepts

**Dense (BGE-M3)**: semantic / cross-lingual / synonyms; may miss exact codes; costlier.  
**Sparse (BM25)**: exact terms / IDs; no semantics; fast.  
**Fusion (`fusion.py`)**: RRF `score(d)=Σ 1/(k+rank)` with `k=60` (rank-only, scale-free) or weighted sum after min-max normalize to `[0,1]`.  
**Rerank**: BGE-Reranker-v2-M3 (service); `BAAI/bge-reranker-base` in `evaluate.py`.

### Prerequisites

Python 3.8+, macOS M1/M2 (or adjust device), ≥8GB RAM, ~5GB disk for models.

### Installation

```bash
cd chapter3/retrieval-pipeline
pip install -r requirements.txt
# First run downloads: BGE-M3 ~2.3GB, BGE-Reranker-v2-M3 ~1.1GB
```

### Running services

```bash
./start_all_services.sh
# Dense 4240, Sparse 4241, Pipeline 4242
```

Or individually:

```bash
# Terminal 1
cd ../dense-embedding && python main.py --port 4240
# Terminal 2
cd ../sparse-embedding && python server.py --port 4241
# Terminal 3
cd ../retrieval-pipeline && python main.py --port 4242
```

### Testing with services

```bash
python test_client.py   # educational cases
python demo.py          # interactive demo
# API docs: http://localhost:4242/docs
```

### Offline evaluation CLI (`evaluate.py`)

`test_client.py` / `demo.py` need ports 4240–4242. **`evaluate.py` runs the full pipeline in one process — no service startup needed, and fully offline once the models are cached**. Note: the first run still downloads the dense/rerank models from HuggingFace, so initial execution requires network access.

```bash
python evaluate.py --help          # Chinese help
python evaluate.py                 # full stage table (default)
python evaluate.py --no-dense      # BM25 only, no models
python evaluate.py --no-rerank
python evaluate.py --query "XR-7003"
python evaluate.py --embed-model BAAI/bge-m3 --pooling cls
python evaluate.py --output result.json
```

| Stage | Default component | Offline? |
|-------|-------------------|----------|
| chunk | character-window splitter | ✅ pure Python |
| sparse | BM25 (`rank_bm25`) | ✅ no model download |
| dense | `sentence-transformers/all-MiniLM-L6-v2` (~90MB) | ✅ cached HF |
| fuse | RRF + weighted (`fusion.py`) | ✅ pure Python |
| rerank | `BAAI/bge-reranker-base` (~1.1GB first download) | ✅ once cached |

> `--no-dense` needs no ML model. Dense/rerank models download from HuggingFace on first run (network required); after that they run from local cache, and `--offline` forces loading from the local cache only. On Apple Silicon, MPS `NaN` is detected and falls back to CPU.

### Real output (reproduced)

Hard clusters: near-duplicate codes (`XR-7001..`, `HTTP-400..`) break dense; zero-lexical paraphrases break BM25.

```
Stage / Method            Recall@3         MRR      nDCG@3
------------------------------------------------------------------------------
BM25 (sparse)               0.9000      0.8500      0.8631
Dense                       1.0000      0.9000      0.9262
Hybrid-RRF                  1.0000      1.0000      1.0000
Hybrid-Weighted             1.0000      0.9500      0.9631
Hybrid-RRF+Rerank           1.0000      0.9500      0.9631
```

**How to read it:** BM25 nails codes, fails paraphrases; Dense is the mirror; **Hybrid-RRF** reaches perfect 1.00 (headline of Exp. 3-6). Weighted can be less robust (scale alignment). On this toy 17-doc set RRF is already strong; rerank value grows on larger pools / NL queries.

```
$ python evaluate.py --query "XR-7003"
[BM25 (sparse)]
  1. xr_7003        score=  3.2260  Product model XR-7003 is a smartphone available now.
[Dense]
  1. xr_7001        score=  0.5247  Product model XR-7001 ...
  2. xr_7003        score=  0.5195  Product model XR-7003 ...
[Hybrid-RRF]
  1. xr_7003        score=  0.0325  Product model XR-7003 ...
```

### Educational test cases (with services)

1. Semantic (“kitty behavior” / feline) — dense wins  
2. Exact name (“Alexander Humphrey”) — sparse wins  
3. Multilingual (“人工智能”) — dense wins  
4. Codes (“HTTP-403”) — sparse wins  
5. Concepts (“happiness and excitement”) — dense wins  

### API

```bash
POST /index
{"text": "Document content", "doc_id": "optional_id", "metadata": {"category": "example"}}

POST /search
{"query": "search terms", "mode": "hybrid", "top_k": 20, "rerank_top_k": 10}

GET /stats
GET /documents?limit=10&offset=0
```

Response includes dense/sparse rankings, reranked results, rank changes, overlap stats.

### Project structure

```
retrieval-pipeline/
├── config.py, document_store.py, retrieval_client.py
├── reranker.py, fusion.py, retrieval_pipeline.py
├── evaluate.py, main.py, test_client.py, demo.py
├── requirements.txt, start_all_services.sh, stop_all_services.sh
└── README.md
```

### Performance / takeaways

- Latency ballpark: dense 50–100ms, sparse 10–30ms, rerank 100–200ms (20 docs)  
- Memory ~4GB models + docs  
- No single method wins; hybrid usually better; rerank improves relevance  

### Troubleshooting

Ports 4240–4242 free; models downloaded; Python 3.8+. OOM → smaller batches, CPU, FP16. First run slow (downloads).

### Further reading

[BGE-M3](https://arxiv.org/abs/2402.03216) · [BM25](https://en.wikipedia.org/wiki/Okapi_BM25) · [Neural IR](https://arxiv.org/abs/2301.09191)

### License

Educational project for learning purposes.

---

## 中文

### 教学目标

1. **稠密 vs 稀疏**：各自擅长场景  
2. **混合检索**：多路互补  
3. **神经重排序**：用 Transformer 重排候选  
4. **并行处理**：多服务索引/检索  
5. **工程模式**：API 与错误处理  

### 架构

（与 English 节相同：Pipeline 4242，Dense 4240，Sparse 4241。）

### 关键概念

**稠密（BGE-M3）**：语义/跨语言/同义词；可能漏精确编码；计算更贵。  
**稀疏（BM25）**：精确词/ID；无语义；快。  
**融合（`fusion.py`）**：RRF（`k=60`）或 min-max 后加权求和。  
**重排**：服务用 BGE-Reranker-v2-M3；`evaluate.py` 用 `BAAI/bge-reranker-base`。

### 前置与安装

Python 3.8+，建议 ≥8GB 内存，约 5GB 模型空间。

```bash
cd chapter3/retrieval-pipeline
pip install -r requirements.txt
```

### 启动服务

```bash
./start_all_services.sh
```

或分别：

```bash
cd ../dense-embedding && python main.py --port 4240
cd ../sparse-embedding && python server.py --port 4241
cd ../retrieval-pipeline && python main.py --port 4242
```

### 带服务测试

```bash
python test_client.py
python demo.py
# http://localhost:4242/docs
```

### 离线评测 CLI（`evaluate.py`）

**单进程、可离线**跑通 chunk → embed → retrieve → fuse → rerank。

```bash
python evaluate.py --help
python evaluate.py
python evaluate.py --no-dense
python evaluate.py --no-rerank
python evaluate.py --query "XR-7003"
python evaluate.py --embed-model BAAI/bge-m3 --pooling cls
python evaluate.py --output result.json
```

| 阶段 | 默认组件 | 离线？ |
|------|----------|--------|
| chunk | 字符窗口切分 | ✅ 纯 Python |
| sparse | BM25 | ✅ 无需下载模型 |
| dense | MiniLM-L6-v2（~90MB） | ✅ HF 缓存 |
| fuse | RRF + weighted | ✅ 纯 Python |
| rerank | bge-reranker-base | ✅ 首次下载后缓存 |

> `--no-dense` 完全不需 ML 模型。Apple Silicon 上 MPS 出现 `NaN` 时自动回退 CPU。

### 真实输出解读

近重复编码打崩稠密；零词面重叠改写打崩 BM25。**Hybrid-RRF 全面 1.00** 是实验 3-6 的核心结论。加权融合对尺度更敏感。小语料上 RRF 已很强，重排价值在更大候选池与自然语言查询中更明显。

单查询追踪：

```
$ python evaluate.py --query "XR-7003"
[BM25 (sparse)]
  1. xr_7003        ...
[Dense]
  1. xr_7001        ...   # 稠密先排到兄弟编码
  2. xr_7003        ...
[Hybrid-RRF]
  1. xr_7003        ...   # 融合把精确匹配推回第 1
```

### 教学测试用例（需服务）

语义 / 精确人名 / 多语言 / 技术编码 / 概念词——分别观察稠密或稀疏胜出。

### API

```bash
POST /index
{"text": "Document content", "doc_id": "optional_id", "metadata": {"category": "example"}}

POST /search
{"query": "search terms", "mode": "hybrid", "top_k": 20, "rerank_top_k": 10}

GET /stats
GET /documents?limit=10&offset=0
```

响应含稠密/稀疏原始排名、重排结果、排名变化与重叠统计。

### 项目结构

```
retrieval-pipeline/
├── config.py, document_store.py, retrieval_client.py
├── reranker.py, fusion.py, retrieval_pipeline.py
├── evaluate.py, main.py, test_client.py, demo.py
├── requirements.txt, start_all_services.sh, stop_all_services.sh
└── README.md
```

### 性能与要点

- 时延量级：稠密 50–100ms，稀疏 10–30ms，重排约 100–200ms（20 文档）  
- 模型内存约 4GB  
- 没有单一最优；混合通常更好；重排提升相关性  

### 故障排查

检查 4240–4242 端口与模型下载；OOM 时减小 batch、改 CPU、开 FP16。

### 延伸阅读与许可

[BGE-M3](https://arxiv.org/abs/2402.03216) · [BM25](https://en.wikipedia.org/wiki/Okapi_BM25) · 教学项目。

---

## Notes / 说明

- Upstream services: [`../dense-embedding/`](../dense-embedding/) (4240), [`../sparse-embedding/`](../sparse-embedding/) (4241).  
- 上游服务：[`../dense-embedding/`](../dense-embedding/)（4240）、[`../sparse-embedding/`](../sparse-embedding/)（4241）。
