# Sparse Vector Search Engine (BM25) / 稀疏向量搜索引擎（BM25）

> Companion material for *AI Agents in Depth*, Chapter 3 — **Experiment 3-5**: educational BM25 / inverted-index sparse search with offline CLI evaluation.  
> 配套《深入理解 AI Agent》第 3 章 **实验 3-5**：从零理解 BM25 与倒排索引，含可离线评测的 CLI。

← [Chapter 3 index / 返回第 3 章目录](../README.md)

---

## English

### Overview

An educational sparse vector search engine using an inverted index and BM25. It demonstrates core IR concepts with extensive logging and visualization.

### Features

- **Full BM25 implementation**
- **Advanced tokenization**: numbers, codes, technical terms, mixed case
- **Inverted index** for term lookup
- **HTTP API** (FastAPI)
- **Interactive Web UI** for index/search
- **Educational logging** through index and search
- **Index visualization** APIs
- **In-memory storage** (educational simplicity)

#### Tokenization capabilities

- **Numbers**: `404`, `3.14`, `2.0.1`
- **Codes**: `XK9-2B4-7Q1`, `API_KEY_123`
- **Technical terms**: `C++`, `.NET`, `Node.js`
- **Mixed case**: `JavaScript`, `PyTorch`, `iPhone`
- **Email**: `user@example.com`
- **Hex**: `#FF5733`, `0x1234`
- **Acronyms**: `API`, `HTTP`, `NASA`
- **Alphanumeric**: `Python3`, `ES6`, `HTML5`

### Architecture

1. **TextProcessor**: tokenizer for words, numbers, codes, technical terms, mixed case  
2. **InvertedIndex**: term/document frequencies  
3. **BM25**: ranking  
4. **SparseSearchEngine**: orchestration  
5. **HTTP Server**: FastAPI surface  

BM25 uses TF, IDF, and document-length normalization. Key params: `k1` (default 1.5), `b` (default 0.75).

### Installation

```bash
pip install -r requirements.txt
```

`cli.py` (below) uses only the Python standard library and runs offline with no third-party packages; `server.py` / `demo.py` need FastAPI and the rest of `requirements.txt`.

### CLI tool `cli.py` (Experiment 3-5, recommended entry)

Fully offline CLI: BM25 on a built-in 10-doc corpus, per-term TF/IDF/BM25 contribution logs (as in the book), and labelled recall/precision/MRR. All flags have Chinese `--help`.

```bash
python cli.py --help                          # all flags (Chinese)
python cli.py                                 # default demo query "model distillation"
python cli.py -q "model distillation" --explain   # per-term TF/IDF/BM25
python cli.py --eval                          # recall@k / precision@k / MRR
python cli.py -q "cat"                        # synonym failure (kitten/feline miss)
python cli.py --corpus my.json -q "查询" -o out.json
python cli.py --k1 2.0 -b 0.5 -q "..."
python cli.py --method splade -q "..."        # SPLADE (needs downloaded model)
```

| Flag | Description |
| --- | --- |
| `-q, --query` | Query string (default `model distillation`) |
| `-c, --corpus` | Corpus (`.json` array or `.jsonl`); default built-in sample |
| `-m, --method` | `bm25` (default, offline) or `splade` (learned sparse; needs model) |
| `-k, --top-k` | Top-k (default 5) |
| `-o, --output` | Write results/metrics JSON |
| `--eval` | Evaluate recall@k / precision@k / MRR on labels |
| `--labels` | Custom labels `{query: [doc_id,...]}` |
| `--explain` | Per-term TF / IDF / BM25 on hits |
| `--k1` / `-b` | BM25 k1 and b |
| `-v, --verbose` | Engine DEBUG logs |

#### Retrieval quality (`--eval`)

Built-in labels cover exact keywords, error codes, proper names, and synonym-only queries. Real `python cli.py --eval` output (k=5):

```
查询 'model distillation'  recall@5=1.00  precision@5=1.00  RR=1.00
查询 'HTTP 404 error'       recall@5=1.00  precision@5=0.50  RR=1.00
查询 'XK9-2B4-7Q1'          recall@5=1.00  precision@5=1.00  RR=1.00
查询 'BM25 ranking function' recall@5=1.00  precision@5=1.00  RR=1.00
查询 'cat'                  recall@5=0.00  precision@5=0.00  RR=0.00   <- 漏召回(同义词短板)
宏平均  recall@5=0.800  precision@5=0.700  MRR=0.800  漏召回率(1-recall@5)=0.200
```

BM25 excels on exact keywords, codes, and names (recall=1.0) but misses synonyms—query `cat` does not hit docs that only say `kitten` / `feline`. That gap motivates hybrid search (Experiment 3-6 `retrieval-pipeline`).

#### Learned sparse (`--method splade`)

SPLADE weights terms with a masked LM and can expand semantically related terms. Needs pretrained `naver/splade-cocondenser-ensembledistil` (`torch`, `transformers`). Offline without weights, the command fails fast with a clear message (BM25 path needs no model). Online: `huggingface-cli download naver/splade-cocondenser-ensembledistil` then run.

### Server usage

```bash
python server.py
```

Server: `http://localhost:4241`. Web UI: open that URL. API docs: `http://localhost:4241/docs`.

#### API endpoints

```bash
POST /index
{
  "text": "Your document text here",
  "metadata": {"title": "Document Title", "category": "Category"}
}

POST /search
{
  "query": "your search query",
  "top_k": 10
}

GET /stats
GET /index/structure
GET /document/{doc_id}
DELETE /index
```

#### Demo

```bash
python demo.py
```

Demo: clear index → sample CS docs → stats → index structure → sample queries → document get.

### Educational features

Logging covers tokenization, TF, IDF, per-term BM25, query processing, candidates. `/index/structure` returns inverted map, doc stats, BM25 params, global TF distribution. Search results include matched terms, doc length, TFs, per-term score contributions.

### Project structure

```
sparse-embedding/
├── bm25_engine.py     # Core engine
├── cli.py             # Offline CLI: BM25/SPLADE + metrics
├── server.py          # FastAPI server
├── demo.py            # Demo script
├── requirements.txt
└── README.md
```

### Limitations

In-memory only; basic tokenization (no lemmatization); English stopwords; no phrase queries / synonyms / multi-thread.

---

## 中文

### 概述

基于倒排索引与 BM25 的教学型稀疏向量搜索引擎，用详细日志与可视化帮助理解信息检索基本概念。

### 功能特性

- **完整 BM25 实现**
- **高级分词**：数字、编码、技术术语、大小写混合
- **倒排索引**
- **HTTP API**（FastAPI）
- **交互式 Web UI**
- **教学日志**
- **索引结构可视化 API**
- **内存存储**（教学简化）

#### 分词能力

- **数字**：`404`、`3.14`、`2.0.1`
- **编码**：`XK9-2B4-7Q1`、`API_KEY_123`
- **技术术语**：`C++`、`.NET`、`Node.js`
- **大小写混合**：`JavaScript`、`PyTorch`、`iPhone`
- **邮箱**：`user@example.com`
- **十六进制**：`#FF5733`、`0x1234`
- **缩写**：`API`、`HTTP`、`NASA`
- **字母数字**：`Python3`、`ES6`、`HTML5`

### 架构

1. **TextProcessor**：分词  
2. **InvertedIndex**：词频 / 文档频率  
3. **BM25**：相关性打分  
4. **SparseSearchEngine**：总控  
5. **HTTP Server**：FastAPI  

BM25 使用 TF、IDF 与文档长度归一化。关键参数：`k1`（默认 1.5）、`b`（默认 0.75）。

### 安装

```bash
pip install -r requirements.txt
```

`cli.py` 只依赖 Python 标准库，无需第三方包即可离线运行；`server.py` / `demo.py` 才需要 FastAPI 等依赖。

### 命令行工具 cli.py（实验 3-5，推荐入口）

完全离线：在内置 10 篇小语料上跑 BM25、复现书中「逐词 IDF/TF/BM25 贡献」日志，并在标注集上算 recall/precision/MRR。参数均有中文 `--help`。

```bash
python cli.py --help                          # 查看全部参数（中文）
python cli.py                                 # 默认演示：查询 "model distillation"
python cli.py -q "model distillation" --explain   # 逐词展示 TF/IDF/BM25 贡献
python cli.py --eval                          # recall@k / precision@k / MRR
python cli.py -q "cat"                        # 观察同义词短板（kitten/feline 漏召回）
python cli.py --corpus my.json -q "查询" -o out.json
python cli.py --k1 2.0 -b 0.5 -q "..."
python cli.py --method splade -q "..."        # SPLADE（需预先下载模型）
```

| 参数 | 说明 |
| --- | --- |
| `-q, --query` | 查询字符串（默认 `model distillation`） |
| `-c, --corpus` | 语料（`.json` 数组或 `.jsonl`）；缺省用内置示例 |
| `-m, --method` | `bm25`（默认，离线）或 `splade`（学习型稀疏，需模型） |
| `-k, --top-k` | 返回前 k 条（默认 5） |
| `-o, --output` | 结果 / 指标写入 JSON |
| `--eval` | 在标注集上评测 |
| `--labels` | 自定义标注 `{query: [doc_id,...]}` |
| `--explain` | 逐词 TF / IDF / BM25 |
| `--k1` / `-b` | BM25 参数 |
| `-v, --verbose` | DEBUG 日志 |

#### 检索质量评测（`--eval`）

内置标注覆盖精确关键词、错误码、专有名称与「只有同义表达」的查询。真实输出（k=5）：

```
查询 'model distillation'  recall@5=1.00  precision@5=1.00  RR=1.00
查询 'HTTP 404 error'       recall@5=1.00  precision@5=0.50  RR=1.00
查询 'XK9-2B4-7Q1'          recall@5=1.00  precision@5=1.00  RR=1.00
查询 'BM25 ranking function' recall@5=1.00  precision@5=1.00  RR=1.00
查询 'cat'                  recall@5=0.00  precision@5=0.00  RR=0.00   <- 漏召回(同义词短板)
宏平均  recall@5=0.800  precision@5=0.700  MRR=0.800  漏召回率(1-recall@5)=0.200
```

BM25 在精确关键词、错误码、专有名称上极佳，但读不懂同义词——查询 `cat` 无法命中只写 `kitten` / `feline` 的文档。这正是引入混合检索（实验 3-6 `retrieval-pipeline`）的动机。

#### 学习型稀疏检索（`--method splade`）

用掩码语言模型为词项打权，并可为语义相关词项补权。需下载 `naver/splade-cocondenser-ensembledistil`（依赖 `torch`、`transformers`）。离线无权重时会快速给出清晰提示。联网可先 `huggingface-cli download naver/splade-cocondenser-ensembledistil`。

### 服务端用法

```bash
python server.py
```

服务地址：`http://localhost:4241`。Web UI 打开该地址。API 文档：`http://localhost:4241/docs`。

#### API 端点

```bash
POST /index
{
  "text": "Your document text here",
  "metadata": {"title": "Document Title", "category": "Category"}
}

POST /search
{
  "query": "your search query",
  "top_k": 10
}

GET /stats
GET /index/structure
GET /document/{doc_id}
DELETE /index
```

#### 运行演示

```bash
python demo.py
```

演示：清空索引 → 示例文档 → 统计 → 索引结构 → 查询 → 按 ID 取文档。

### 教学特性

日志覆盖分词、TF、IDF、逐词 BM25、查询处理、候选文档。`/index/structure` 返回倒排映射、文档统计、BM25 参数、全局词频分布。检索结果含匹配词、文档长度、词频与分项得分。

### 项目结构

```
sparse-embedding/
├── bm25_engine.py     # 核心检索引擎
├── cli.py             # 离线 CLI：BM25/SPLADE + 指标
├── server.py          # FastAPI 服务
├── demo.py            # 演示脚本
├── requirements.txt
└── README.md
```

### 局限

仅内存存储；分词较基础（无词形还原）；英文停用词；不支持短语查询 / 同义扩展 / 多线程。

---

## Notes / 说明

- Related next step / 相关后续：[`../retrieval-pipeline/`](../retrieval-pipeline/) hybrid dense+sparse pipeline (Exp. 3-6).  
- 相关后续：[`../retrieval-pipeline/`](../retrieval-pipeline/) 混合稠密+稀疏流水线（实验 3-6）。
