# Contextual Retrieval System / 上下文感知检索系统

> Companion material for *AI Agents in Depth*, Chapter 3 — **Experiment 3-11**: Anthropic-style contextual prefixes before indexing; offline BM25 recall@k compare.  
> 配套《深入理解 AI Agent》第 3 章 **实验 3-11**：索引前为分块生成上下文前缀；离线 BM25 recall@k 对比。

← [Chapter 3 index / 返回第 3 章目录](../README.md)

---

## English

### Overview

Educational implementation of Anthropic’s Contextual Retrieval: prepend chunk-specific context before embedding/indexing to fix the “orphaned chunk” problem.

### Key insight

**Problem:** Traditional RAG loses context when chunking. “The company’s revenue grew by 3%” is meaningless without which company / which period.

**Solution:** Generate short explanatory context per chunk and prepend it before indexing so BM25 and embeddings keep identity signals.

### Core offline experiment (Experiment 3-11)

`compare_retrieval.py` quantifies the claim **fully offline**: same chunks indexed two ways—plain (raw text only) vs contextual (LLM-generated prefix + text)—then compares `recall@k` on `evaluation/retrieval_eval.json` (15 queries + human gold chunks). **No API or retrieval service** (BM25 + jieba).

```bash
python compare_retrieval.py
python compare_retrieval.py --per-query
python compare_retrieval.py --query "国家主席有哪些职权？" --top-k 5
python compare_retrieval.py --mode plain
python compare_retrieval.py --output result.json
python compare_retrieval.py --help   # Chinese help
```

Real run (22 Constitution / Prosecutor Law chunks, 15 queries, jieba):

```
检索召回对比：无上下文分块  vs.  上下文感知检索（BM25）
====================================================================
方法                  recall@1    recall@3    recall@5
----------------------------------------------------
无上下文 (plain)          60.0%      86.7%      93.3%
有上下文 (ctx)            86.7%      86.7%      93.3%
----------------------------------------------------
提升 (Δpp)             +26.7pp      +0.0pp      +0.0pp
----------------------------------------------------
失败率下降                    67%          0%          0%
```

Conclusion (matches the book): context prefixes lift top-1 recall (60% → 86.7%; failure rate 1−recall@1 down 67%). Gain is strongest at recall@1; `--query` shows how the prefix re-ranks the correct section first.

> `--method embedding` / `--method hybrid` need embedding APIs (not offline); the script falls back to BM25 offline results. Full dense + rerank lives in `contextual_tools.py`.  
> Same logic is also in `ContextualChunker.compare_retrieval_methods()`.

### Educational features

1. Watch LLM context generation per chunk  
2. Dual indexing (BM25 + embeddings) benefits from context  
3. Compare with `use_contextual=False`  
4. Metrics and token/cost awareness  

### Architecture

```
Document → Basic Chunking → Context Generation (optional LLM)
  → Enhanced chunks (context+text vs text only)
  → Retrieval pipeline (sparse BM25 + dense embeddings)
  → Hybrid search + reranking
```

### Quick start

```bash
pip install -r requirements.txt
cp env.example .env
# MOONSHOT_API_KEY / ARK_API_KEY / OPENAI_API_KEY / etc.

# Separate terminal for full e2e with pipeline:
cd ../retrieval-pipeline
python main.py
# http://localhost:4242

# Back in this project directory (or a second terminal):
cd ../contextual-retrieval

# Index with contextual enhancement
python index_local_laws_contextual.py
python index_local_laws_contextual.py --no-contextual

# Queries
python main.py
python main.py --query "宪法第一条是什么" --mode agentic
python main.py --query "宪法第一条是什么" --mode compare
```

### Context generation process

1. Provide full document (or surrounding context) to the LLM  
2. Show the specific chunk  
3. Ask for 2–3 sentence situating context  

Template sketch:

```
<document>
[Full document or surrounding context]
</document>

Here is the chunk we want to situate:
<chunk>
[Specific chunk text]
</chunk>

Please give a short, succinct context to situate this chunk within the overall document...
```

### References / license

- [Anthropic Contextual Retrieval](https://www.anthropic.com/engineering/contextual-retrieval)  
- Educational project for learning purposes. Acknowledgments: Anthropic engineering research.

---

## 中文

### 概述

Anthropic 上下文感知检索的教学实现：在嵌入/建索引前为每个分块附加专属上下文，缓解「孤儿分块」问题。

### 核心洞察

**问题：** 传统 RAG 分块后丢失语境。「公司收入增长 3%」不知是哪家公司、哪个时期。  
**方案：** 为每块生成简短解释性上下文并前置，使 BM25 与向量都能保留身份信号。

### 核心实验：离线量化召回提升（实验 3-11）

`compare_retrieval.py` **完全离线**量化：同一批文本块分别以无上下文 / 有上下文前缀两种方式建 BM25 索引，在 `evaluation/retrieval_eval.json`（15 查询 + 人工 gold 块）上比较 `recall@k`。**无需 API 或检索服务**（BM25 + jieba）。

```bash
python compare_retrieval.py
python compare_retrieval.py --per-query
python compare_retrieval.py --query "国家主席有哪些职权？" --top-k 5
python compare_retrieval.py --mode plain
python compare_retrieval.py --output result.json
python compare_retrieval.py --help
```

真实输出（22 个《宪法》《检察官法》文本块，15 查询）：

```
检索召回对比：无上下文分块  vs.  上下文感知检索（BM25）
====================================================================
方法                  recall@1    recall@3    recall@5
----------------------------------------------------
无上下文 (plain)          60.0%      86.7%      93.3%
有上下文 (ctx)            86.7%      86.7%      93.3%
----------------------------------------------------
提升 (Δpp)             +26.7pp      +0.0pp      +0.0pp
----------------------------------------------------
失败率下降                    67%          0%          0%
```

结论与书中一致：上下文前缀显著提升 top-1 召回（60% → 86.7%，失败率下降 67%）。`--method embedding` / `hybrid` 需 embedding API，脚本会提示并回退 BM25 离线结果。完整稠密+重排见 `contextual_tools.py`。

### 教学特性

观察上下文生成、双索引策略、`use_contextual=False` 对照、指标与成本。

### 架构

文档 → 基础分块 → 可选 LLM 上下文生成 → 增强块 → 检索流水线（稀疏+稠密）→ 混合检索+重排。

### 快速开始

```bash
pip install -r requirements.txt
cp env.example .env

# 另开一个终端运行完整检索流水线：
cd ../retrieval-pipeline
python main.py
# http://localhost:4242

# 回到本项目目录（或新开一个终端）：
cd ../contextual-retrieval

python index_local_laws_contextual.py
python index_local_laws_contextual.py --no-contextual

python main.py
python main.py --query "宪法第一条是什么" --mode agentic
python main.py --query "宪法第一条是什么" --mode compare
```

### 上下文生成流程

向 LLM 提供全文（或周边）+ 目标块，请求 2–3 句定位上下文。提示模板见 English 节。

### 参考与许可

[Anthropic 博客](https://www.anthropic.com/engineering/contextual-retrieval) · 教学项目。

---

## Notes / 说明

### OpenRouter 通用回退 / Universal OpenRouter fallback

Chat LLM falls back to OpenRouter when primary keys are missing and `OPENROUTER_API_KEY` is set. See `env.example`. Related: [`../contextual-retrieval-for-user-memory/`](../contextual-retrieval-for-user-memory/) (Exp. 3-12).
