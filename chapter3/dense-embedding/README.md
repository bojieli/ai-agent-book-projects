# Vector Similarity Search Service (Dense Embedding) / 稠密向量相似性搜索服务

> Companion material for *AI Agents in Depth*, Chapter 3 — **Experiment 3-4**: BGE-M3 dense search with ANNOY / HNSW, plus offline CLI metrics.  
> 配套《深入理解 AI Agent》第 3 章 **实验 3-4**：BGE-M3 稠密检索与 ANNOY / HNSW 对比，含可离线 CLI。

← [Chapter 3 index / 返回第 3 章目录](../README.md)

---

## English

### Overview

Educational HTTP service for vector similarity search using BGE-M3 embeddings with configurable ANNOY or HNSW backends, plus an offline `cli.py` for Experiment 3-4 metrics.

### CLI: dense retrieval & ANN comparison (`cli.py`, Experiment 3-4)

Besides the HTTP service, `cli.py` is **ready-to-run and offline-reproducible**—no need to start the server first:

1. **Semantic power of dense embeddings** — `recall@k / precision@k / MRR` on a small labelled corpus  
2. **ANN backend comparison** (focus of Exp. 3-4) — ANNOY / HNSW from `indexing.py` vs **exact brute-force**, measuring recall, build time, query latency  

#### Usage

```bash
# 1) Single dense query (default "a cat playing"; needs embedding model)
python cli.py -q "model distillation" -k 3

# 2) Retrieval quality: recall@k / precision@k / MRR
python cli.py --eval

# 2') Offline: small cached model (no 2.3GB BGE-M3 download)
python cli.py --embedding-model sentence-transformers/all-MiniLM-L6-v2 --eval

# 3) ANN backend compare (synthetic vectors; fully offline, no model)
python cli.py --compare-ann -k 10
python cli.py --compare-ann --backend hnsw --hnsw-ef-search 200 -k 10

# Custom corpus / labels / output
python cli.py --corpus my.json --labels my_labels.json --eval -o result.json
```

`python cli.py --help` has full Chinese flag docs.

#### Common flags

| Flag | Description |
| --- | --- |
| `-q, --query` | Query (default `a cat playing`) |
| `-c, --corpus` | Corpus (`.json` array or `.jsonl`); default built-in sample |
| `-k, --top-k` | Top-k (default 5) |
| `-o, --output` | Write results/metrics JSON |
| `--embedding-model` | Model (default `BAAI/bge-m3`; offline: `sentence-transformers/all-MiniLM-L6-v2`) |
| `--pooling` | `auto` / `mean` / `cls` |
| `--eval` | Evaluate recall@k / precision@k / MRR |
| `--compare-ann` | Compare ANNOY / HNSW (synthetic vectors) |
| `--ann-base / --ann-dim / --ann-queries` | Synthetic base size / dim / queries (default 3000 / 128 / 100) |
| `--annoy-n-trees / --hnsw-M / --hnsw-ef-search` | ANN hyperparameters |

#### Measured results (real runs)

**Dense quality** (12-doc built-in, `all-MiniLM-L6-v2`, offline):

```
宏平均  recall@5=1.000  precision@5=0.320  MRR=1.000
```

Query `a cat playing` ranks docs that only say `kitten` / `feline` (no literal “cat”) at ranks 1–2—semantic strength vs BM25 (Exp. 3-5 may miss them).

**ANN compare** (3000 × 128-d unit vectors, 100 queries, top-10); HNSW recall rises with `ef_search`:

| Config | recall@10 | Mean query latency |
| --- | --- | --- |
| HNSW `ef_search=20` | 0.562 | 0.05 ms |
| HNSW `ef_search=200` | 0.991 | 0.25 ms |

> **Environment note**: each backend is health-checked by self-querying. On some macOS/arm64 setups, prebuilt `annoy==1.17.3` is broken (even self-query only returns itself); the tool warns and marks those numbers untrusted. HNSW is unaffected. Full ANNOY vs HNSW: use an environment where Annoy works (e.g. Linux x86_64).

### Service features

- **BGE-M3**: dense embeddings, 100+ languages, long context (up to 8192 tokens)  
- **Dual backends**: ANNOY (tree), HNSW (graph)  
- **Educational logging**: embed, index ops, metrics, vector stats  
- **REST API**: index / delete / search / stats  
- **In-memory** (no persistence)  

### Architecture

```
┌──────────────────┐
│   HTTP Client    │
└────────┬─────────┘
         ▼
┌──────────────────┐
│  FastAPI Server  │
└────────┬─────────┘
    ┌────┴────┐
    ▼         ▼
┌──────────┐ ┌──────────────┐
│ Document │ │  Embedding   │
│  Store   │ │   Service    │
└──────────┘ │  (BGE-M3)    │
             └──────┬───────┘
          ┌─────────┴──────────┐
          ▼                    ▼
    ┌──────────┐        ┌──────────┐
    │  ANNOY   │        │   HNSW   │
    └──────────┘        └──────────┘
```

### Installation

- Python 3.8+, macOS (M1/M2 optimized) or Linux  
- ≥4GB RAM (8GB recommended); optional CUDA GPU  

```bash
cd chapter3/dense-embedding
pip install -r requirements.txt
```

BGE-M3 (~2.3GB) downloads on first use into the HuggingFace cache.

### Starting the service

```bash
python main.py                              # HNSW (default)
python main.py --index-type annoy
python main.py --index-type hnsw --host 0.0.0.0 --port 4242 --debug --show-embeddings
```

Options: `--index-type` (`annoy`|`hnsw`, default `hnsw`), `--host` (default `0.0.0.0`), `--port` (default `4240`), `--debug`, `--show-embeddings`.

Docs: http://localhost:4240/docs · OpenAPI: http://localhost:4240/openapi.json

### API endpoints

**POST `/index`**

```json
{
  "text": "Machine learning is a subset of artificial intelligence.",
  "doc_id": "doc_001",
  "metadata": {"category": "AI", "author": "John Doe"}
}
```

**POST `/search`**

```json
{
  "query": "What is deep learning?",
  "top_k": 5,
  "return_documents": true
}
```

**DELETE `/index`** — body `{"doc_id": "doc_001"}`  
**GET `/stats`** · **GET `/documents?limit=10`**

### Testing

```bash
python test_client.py
python test_client.py --performance
```

```bash
curl -X POST http://localhost:4240/index \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a test document about machine learning."}'

curl -X POST http://localhost:4240/search \
  -H "Content-Type: application/json" \
  -d '{"query": "artificial intelligence", "top_k": 5}'
```

### Index comparison

**ANNOY**: fast build, low memory, good for static/read-heavy; rebuild for delete; trade accuracy via `n_trees`.  
**HNSW**: high recall, incremental updates, soft delete; more memory, slower build; tune `M` / `ef_*`.

### Configuration (env `VEC_` prefix)

```bash
export VEC_INDEX_TYPE=hnsw
export VEC_MODEL_NAME=BAAI/bge-m3
export VEC_USE_FP16=true
export VEC_MAX_SEQ_LENGTH=512
export VEC_MAX_DOCUMENTS=100000
export VEC_LOG_LEVEL=DEBUG
export VEC_ANNOY_N_TREES=50
export VEC_ANNOY_METRIC=angular
export VEC_HNSW_EF_CONSTRUCTION=200
export VEC_HNSW_M=32
export VEC_HNSW_EF_SEARCH=100
export VEC_HNSW_SPACE=cosine
```

Educational logging: `python main.py --debug --show-embeddings`.

### Memory / optimization notes

- Model ~2.3GB; ~4KB per doc (1024-d float32)  
- ANNOY: raise `n_trees` for accuracy; `angular` for normalized vectors; batch then build  
- HNSW: raise `M` / `ef_construction` / `ef_search` for quality vs cost  
- FP16 faster with slight accuracy trade-off  

### Troubleshooting

OOM → smaller batches, FP16, lower `max_seq_length`, prefer ANNOY. Slow index → lower `ef_construction` / `n_trees`, use GPU. Poor quality → raise `n_trees` / `M` / `ef_search`.

### References

- [BGE-M3 Paper](https://arxiv.org/abs/2402.03216) · [Model](https://huggingface.co/BAAI/bge-m3)  
- [ANNOY](https://github.com/spotify/annoy) · [HNSWlib](https://github.com/nmslib/hnswlib) · [FastAPI](https://fastapi.tiangolo.com/)

### License

Educational project for learning purposes.

---

## 中文

### 概述

基于 BGE-M3 嵌入、可切换 ANNOY / HNSW 后端的教学型向量相似性搜索 HTTP 服务，外加实验 3-4 的离线 CLI 评测。

### 命令行工具：稠密检索与 ANN 对比（cli.py，实验 3-4）

除 HTTP 服务外，`cli.py` **开箱即用、可离线复现**，无需先启动服务：

1. **稠密嵌入的语义能力**——小标注语料上算 `recall@k / precision@k / MRR`  
2. **ANN 后端对比**（实验 3-4 重点）——复用 `indexing.py` 的 ANNOY / HNSW，相对**精确暴力检索**测召回、建索引耗时与查询延迟  

#### 用法

```bash
# 1) 单条稠密查询（默认 "a cat playing"，需要嵌入模型）
python cli.py -q "model distillation" -k 3

# 2) 检索质量评测
python cli.py --eval

# 2') 离线复现：小模型（无需下载 2.3GB BGE-M3）
python cli.py --embedding-model sentence-transformers/all-MiniLM-L6-v2 --eval

# 3) ANN 后端对比（合成向量，完全离线）
python cli.py --compare-ann -k 10
python cli.py --compare-ann --backend hnsw --hnsw-ef-search 200 -k 10

# 自定义语料 / 标注 / 输出
python cli.py --corpus my.json --labels my_labels.json --eval -o result.json
```

`python cli.py --help` 提供完整中文参数说明。

#### 常用参数

| 参数 | 说明 |
| --- | --- |
| `-q, --query` | 查询（默认 `a cat playing`） |
| `-c, --corpus` | 语料（`.json` / `.jsonl`）；缺省内置示例 |
| `-k, --top-k` | Top-k（默认 5） |
| `-o, --output` | 结果 / 指标 JSON |
| `--embedding-model` | 嵌入模型（默认 `BAAI/bge-m3`；离线可用 MiniLM） |
| `--pooling` | `auto` / `mean` / `cls` |
| `--eval` | 评测 recall@k / precision@k / MRR |
| `--compare-ann` | 对比 ANNOY / HNSW |
| `--ann-base / --ann-dim / --ann-queries` | 合成底库规模 / 维度 / 查询数 |
| `--annoy-n-trees / --hnsw-M / --hnsw-ef-search` | ANN 超参 |

#### 实测结果

**稠密检索质量**（12 篇语料，`all-MiniLM-L6-v2`，离线）：

```
宏平均  recall@5=1.000  precision@5=0.320  MRR=1.000
```

查询 `a cat playing` 仍把仅含 `kitten` / `feline` 的文档排到第 1、2 名——相对 BM25（实验 3-5 会漏召回）的语义优势。

**ANN 对比**（3000 条 128 维，100 查询，top-10）：

| 配置 | recall@10 | 平均查询延迟 |
| --- | --- | --- |
| HNSW `ef_search=20` | 0.562 | 0.05 ms |
| HNSW `ef_search=200` | 0.991 | 0.25 ms |

> **环境提示**：部分 macOS/arm64 上 `annoy==1.17.3` 预编译轮子有缺陷，工具会警告并标记不可信；HNSW 不受影响。完整 ANNOY vs HNSW 请在 annoy 正常的环境（如 Linux x86_64）运行。

### 服务功能

- **BGE-M3**：稠密嵌入、多语言、长上下文（至 8192 tokens）  
- **双后端**：ANNOY（树）、HNSW（图）  
- **教学日志**、**REST API**、**纯内存**  

### 架构

（与 English 节相同示意图。）

### 安装

- Python 3.8+，macOS（M1/M2）或 Linux  
- 内存 ≥4GB（建议 8GB）；可选 CUDA  

```bash
cd chapter3/dense-embedding
pip install -r requirements.txt
```

BGE-M3（约 2.3GB）首次运行自动下载。

### 启动服务

```bash
python main.py                              # 默认 HNSW
python main.py --index-type annoy
python main.py --index-type hnsw --host 0.0.0.0 --port 4242 --debug --show-embeddings
```

选项：`--index-type`、`--host`（默认 `0.0.0.0`）、`--port`（默认 `4240`）、`--debug`、`--show-embeddings`。

文档：http://localhost:4240/docs

### API 端点

**POST `/index`** / **POST `/search`** / **DELETE `/index`** / **GET `/stats`** / **GET `/documents?limit=10`**  
请求体格式与 English 节 JSON 示例相同。

### 测试

```bash
python test_client.py
python test_client.py --performance
```

```bash
curl -X POST http://localhost:4240/index \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a test document about machine learning."}'

curl -X POST http://localhost:4240/search \
  -H "Content-Type: application/json" \
  -d '{"query": "artificial intelligence", "top_k": 5}'
```

### 索引对比

**ANNOY**：建索引快、内存低，适合静态/读多写少；删除需重建；用 `n_trees` 换精度。  
**HNSW**：召回高、可增量与软删除；内存更高、建索引更慢；调 `M` / `ef_*`。

### 配置（`VEC_` 环境变量）

```bash
export VEC_INDEX_TYPE=hnsw
export VEC_MODEL_NAME=BAAI/bge-m3
export VEC_USE_FP16=true
export VEC_MAX_SEQ_LENGTH=512
export VEC_MAX_DOCUMENTS=100000
export VEC_LOG_LEVEL=DEBUG
export VEC_ANNOY_N_TREES=50
export VEC_ANNOY_METRIC=angular
export VEC_HNSW_EF_CONSTRUCTION=200
export VEC_HNSW_M=32
export VEC_HNSW_EF_SEARCH=100
export VEC_HNSW_SPACE=cosine
```

教学日志：`python main.py --debug --show-embeddings`。

### 内存与优化

模型约 2.3GB；每文档约 4KB（1024 维 float32）。ANNOY 提高 `n_trees`；HNSW 提高 `M` / `ef_*`；可用 FP16 加速。

### 故障排查

内存不足 → 减小 batch、FP16、降低 `max_seq_length`、改用 ANNOY。建索引慢 → 降低 `ef_construction` / `n_trees`、用 GPU。检索差 → 提高 `n_trees` / `M` / `ef_search`。

### 参考与许可

- [BGE-M3 论文](https://arxiv.org/abs/2402.03216) · [模型](https://huggingface.co/BAAI/bge-m3)  
- [ANNOY](https://github.com/spotify/annoy) · [HNSWlib](https://github.com/nmslib/hnswlib)  
- 教学项目，仅供学习。

---

## Notes / 说明

- Related: [`../sparse-embedding/`](../sparse-embedding/) (Exp. 3-5), [`../retrieval-pipeline/`](../retrieval-pipeline/) (Exp. 3-6).  
- 相关：[`../sparse-embedding/`](../sparse-embedding/)（实验 3-5）、[`../retrieval-pipeline/`](../retrieval-pipeline/)（实验 3-6）。
