"""混合检索流水线离线评测 CLI。

本脚本把整条检索流水线——分块(chunk) → 嵌入(embed) → 检索(retrieve) →
融合(fuse) → 重排(rerank)——完整地跑在**单进程、可离线**的环境里，并在一个带
标注答案的小型评测集上，逐阶段对比各方法的检索质量。它不依赖 dense/sparse 微服务
（4240/4241/4242 端口），因此可以脱离服务、直接用本地模型复现「每加一个阶段、指标如何
提升」这一核心结论。

各阶段使用的本地组件：
  - 稀疏检索(sparse)  : BM25（纯 Python，rank_bm25，无需下载模型）
  - 稠密检索(dense)   : 本地句向量模型（默认 Qwen3-Embedding-0.6B，多语言，
                        通过 transformers 加载；也可换成 BGE-M3 等）
  - 融合(fuse)        : 见 fusion.py，RRF 与加权归一化两种策略
  - 重排(rerank)      : 交叉编码器（默认 cross-encoder/ms-marco-MiniLM-L-6-v2）

默认行为（不带任何参数）：在内置评测集上评测
  BM25 / Dense / Hybrid-RRF / Hybrid-Weighted / Hybrid-RRF+Rerank 五种配置，
  打印 Recall@k、MRR、nDCG@k 对比表。

示例：
  python evaluate.py                         # 内置评测集，完整对比表
  python evaluate.py --top-k 10 --rerank-top-k 5
  python evaluate.py --no-rerank             # 跳过重排阶段
  python evaluate.py --embed-model BAAI/bge-m3 --pooling cls
  python evaluate.py --query "怎样提升检索精度"  # 单条查询、逐阶段排名追踪
  python evaluate.py --corpus my_corpus.json --queries my_queries.json --output result.json
"""

import argparse
import json
import math
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

from fusion import fuse

# ---------------------------------------------------------------------------
# 内置评测集：直接复用 test_client.py 中的教育性测试案例（语义相似 / 精确名称 /
# 多语言 / 技术代码四类），其 expected 字段即人工标注的相关文档，作为评测金标准。
# 另加两篇较长文档用于演示分块(chunk)阶段。
# ---------------------------------------------------------------------------
DEFAULT_CORPUS: List[Dict[str, Any]] = [
    # --- 近似重复的代码簇（稀疏占优、稠密翻车）---
    # 各条文本几乎完全相同，只有型号代码不同；稠密向量几乎无法区分同一簇内的成员，
    # 稀疏检索靠精确词项匹配却能一击命中。簇越大，稠密选错的概率越高。
    {"doc_id": "xr_7001", "text": "Product model XR-7001 is a smartphone available now."},
    {"doc_id": "xr_7002", "text": "Product model XR-7002 is a smartphone available now."},
    {"doc_id": "xr_7003", "text": "Product model XR-7003 is a smartphone available now."},
    {"doc_id": "xr_7004", "text": "Product model XR-7004 is a smartphone available now."},
    {"doc_id": "xr_7005", "text": "Product model XR-7005 is a smartphone available now."},
    {"doc_id": "xr_7006", "text": "Product model XR-7006 is a smartphone available now."},
    # 近似重复的 HTTP 错误码簇（稀疏占优、稠密翻车）
    {"doc_id": "http_400", "text": "The HTTP-400 response is a client error status code."},
    {"doc_id": "http_401", "text": "The HTTP-401 response is a client error status code."},
    {"doc_id": "http_403", "text": "The HTTP-403 response is a client error status code."},
    {"doc_id": "http_404", "text": "The HTTP-404 response is a client error status code."},
    {"doc_id": "http_500", "text": "The HTTP-500 response is a server error status code."},
    # --- 语义改写簇（稠密占优、稀疏翻车）---
    # 查询与文档几乎没有共同词，稀疏 BM25 无从匹配，稠密靠语义命中。
    {"doc_id": "sem_readable", "text": "The language emphasizes clean, readable code that newcomers can pick up quickly."},
    {"doc_id": "sem_gc", "text": "Automatic memory management frees developers from manually releasing objects."},
    {"doc_id": "sem_photo", "text": "Green plants convert sunlight into chemical energy stored as sugars."},
    {"doc_id": "sem_crypto", "text": "Encryption scrambles a message so that only the intended recipient can read it."},
    # Exact proper-name cluster: sparse matching should preserve the complete
    # name while dense retrieval sees several near-duplicates.
    {"doc_id": "name_alexander_humphrey", "text": "Alexander Humphrey designed the Aurora scheduling protocol in 2019."},
    {"doc_id": "name_alexander_hughes", "text": "Alexander Hughes designed the Borealis scheduling protocol in 2019."},
    {"doc_id": "name_amelia_humphrey", "text": "Amelia Humphrey designed the Celeste scheduling protocol in 2020."},
    # 较长文档：话题彼此独立，用于演示分块阶段（会被切成多个 chunk 后再检索）
    {"doc_id": "doc_watercycle", "text": (
        "The water cycle describes how water moves continuously between the ocean, the atmosphere and the land. "
        "Heat from the sun evaporates water from the sea surface into vapor that rises high into the sky. "
        "As the vapor cools it condenses into tiny droplets that gather to form clouds. "
        "When the droplets grow heavy enough they fall back to the ground as rain or snow, "
        "and rivers eventually carry that water back to the ocean, closing the loop."
    )},
    {"doc_id": "doc_volcano", "text": (
        "A volcano forms where molten rock called magma rises from deep inside the planet toward the surface. "
        "Magma collects in a chamber beneath the crust, and mounting pressure forces it upward through cracks. "
        "During an eruption the magma bursts out as lava, ash and gas, which pile up around the vent. "
        "Layer after layer of cooled lava slowly builds the cone-shaped mountain we recognize as a volcano."
    )},
]

DEFAULT_QUERIES: List[Dict[str, Any]] = [
    # 精确代码查询：稀疏一击命中，稠密难辨近似型号（expected 为唯一正确答案）
    {"query": "XR-7003", "expected": ["xr_7003"], "category": "technical-code"},
    {"query": "XR-7005", "expected": ["xr_7005"], "category": "technical-code"},
    {"query": "HTTP-403", "expected": ["http_403"], "category": "technical-code"},
    {"query": "HTTP-400", "expected": ["http_400"], "category": "technical-code"},
    {"query": "Alexander Humphrey", "expected": ["name_alexander_humphrey"], "category": "exact-name"},
    # 语义改写查询：与文档几乎无共同词，稠密靠语义命中，稀疏无从匹配
    {"query": "a beginner friendly language with tidy syntax", "expected": ["sem_readable"], "category": "semantic"},
    {"query": "reclaiming unused heap space without programmer effort", "expected": ["sem_gc"], "category": "semantic"},
    {"query": "how vegetation turns light into food", "expected": ["sem_photo"], "category": "semantic"},
    {"query": "hiding a note so eavesdroppers cannot understand it", "expected": ["sem_crypto"], "category": "semantic"},
    # Cross-lingual query with no shared lexical terms; the answer remains the
    # same English photosynthesis passage used by the semantic query above.
    {"query": "植物如何把阳光转化为食物", "expected": ["sem_photo"], "category": "multilingual"},
    # 长文档语义查询：命中的长文档会先被分块，再由某个 chunk 召回、重排
    {"query": "how does water move between the ocean and the sky", "expected": ["doc_watercycle"], "category": "semantic"},
    {"query": "how are volcanoes formed from molten rock", "expected": ["doc_volcano"], "category": "semantic"},
]


# ---------------------------------------------------------------------------
# 分块(chunk)
# ---------------------------------------------------------------------------
def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """按字符窗口把文档切成带重叠的 chunk。

    短文档（长度 <= chunk_size）原样返回单个 chunk。真实场景中 chunk 是检索的最小
    单元；这里用字符级滑窗保持实现简单、语言无关。

    Args:
        text: 原始文档文本。
        chunk_size: 每个 chunk 的最大字符数。
        overlap: 相邻 chunk 的重叠字符数。

    Returns:
        chunk 文本列表（至少一个）。
    """
    text = text.strip()
    if chunk_size <= 0 or len(text) <= chunk_size:
        return [text]

    step = max(1, chunk_size - overlap)
    chunks = []
    for start in range(0, len(text), step):
        piece = text[start:start + chunk_size].strip()
        if piece:
            chunks.append(piece)
        if start + chunk_size >= len(text):
            break
    return chunks or [text]


# ---------------------------------------------------------------------------
# 分词（BM25 用）：保留英文词/数字/带连字符或下划线的代码，CJK 走 jieba + 单字
# ---------------------------------------------------------------------------
_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[-_][a-z0-9]+)*|[一-鿿]+")


def tokenize(text: str) -> List[str]:
    """把文本切成 BM25 词项。

    - 英文单词、纯数字、以及像 ``http-403`` / ``max_buffer_size`` / ``xr-7000``
      这样的技术代码会被整体保留（连字符、下划线不切开），保证精确匹配。
    - 连续 CJK 片段同时产出 jieba 分词结果与单字，增强中文召回鲁棒性。
    """
    tokens: List[str] = []
    for match in _TOKEN_RE.finditer(text.lower()):
        span = match.group()
        if "一" <= span[0] <= "鿿":
            try:
                import jieba
                tokens.extend(w for w in jieba.cut(span) if w.strip())
            except Exception:
                pass
            tokens.extend(list(span))
        else:
            tokens.append(span)
    return tokens


# ---------------------------------------------------------------------------
# 稀疏检索：BM25
# ---------------------------------------------------------------------------
class BM25Retriever:
    """基于 rank_bm25 的 BM25 检索器（chunk 级）。"""

    def __init__(self, chunk_ids: List[str], chunk_texts: List[str]):
        from rank_bm25 import BM25Okapi

        self.chunk_ids = chunk_ids
        self.tokenized = [tokenize(t) for t in chunk_texts]
        self.bm25 = BM25Okapi(self.tokenized)

    def search(self, query: str, top_k: int) -> List[Tuple[str, float]]:
        """返回 (chunk_id, score) 列表，按分数降序，只保留正分。"""
        scores = self.bm25.get_scores(tokenize(query))
        ranked = sorted(zip(self.chunk_ids, scores), key=lambda kv: kv[1], reverse=True)
        return [(cid, float(s)) for cid, s in ranked[:top_k] if s > 0]


# ---------------------------------------------------------------------------
# 稠密检索：本地句向量模型（transformers）
# ---------------------------------------------------------------------------
class DenseEncoder:
    """用 transformers 加载本地句向量模型，做稠密检索。"""

    def __init__(self, model_name: str, pooling: str, device: str,
                 query_instruct: str = "", max_length: int = 256):
        import torch
        from transformers import AutoModel, AutoTokenizer

        self.torch = torch
        self.device = device
        self.max_length = max_length
        self.pooling = self._resolve_pooling(pooling, model_name)
        # 指令式检索模型（如 Qwen3-Embedding，last-token 池化）要求查询侧带任务指令；
        # mean/cls 池化的模型（MiniLM / BGE-M3）不需要，自动关闭。
        self.query_instruct = query_instruct if (query_instruct and self.pooling == "last") else ""
        # last-token pooling 需要左侧 padding，才能让最后一个位置对齐真实末词
        padding_side = "left" if self.pooling == "last" else "right"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, padding_side=padding_side)
        self.model = AutoModel.from_pretrained(model_name).to(device).eval()

    @staticmethod
    def _resolve_pooling(pooling: str, model_name: str) -> str:
        if pooling != "auto":
            return pooling
        name = model_name.lower()
        if "qwen" in name:
            return "last"
        if "bge-m3" in name or "bge-large" in name or "bge-base" in name:
            return "cls"
        return "mean"

    def _pool(self, last_hidden, attention_mask):
        torch = self.torch
        if self.pooling == "cls":
            return last_hidden[:, 0]
        if self.pooling == "last":
            return last_hidden[:, -1]
        # mean pooling
        mask = attention_mask.unsqueeze(-1).float()
        return (last_hidden * mask).sum(1) / mask.sum(1).clamp(min=1e-9)

    def encode(self, texts: Sequence[str], is_query: bool = False, batch_size: int = 16):
        torch = self.torch
        if is_query and self.query_instruct:
            texts = [f"Instruct: {self.query_instruct}\nQuery:{t}" for t in texts]
        vectors = []
        for start in range(0, len(texts), batch_size):
            batch = list(texts[start:start + batch_size])
            pooled = self._forward(batch)
            # 某些模型在 mps 上前向会出 NaN（transformers 5.x + 某些权重）；
            # 检测到后永久退回 CPU 重算，保证向量有限、结果可复现。
            if self.device != "cpu" and torch.isnan(pooled).any():
                self.device = "cpu"
                self.model = self.model.to("cpu")
                pooled = self._forward(batch)
            pooled = torch.nn.functional.normalize(pooled.float(), p=2, dim=1)
            vectors.append(pooled.cpu())
        return torch.cat(vectors, dim=0)

    def _forward(self, batch: List[str]):
        torch = self.torch
        enc = self.tokenizer(
            batch, padding=True, truncation=True,
            max_length=self.max_length, return_tensors="pt",
        ).to(self.device)
        with torch.no_grad():
            out = self.model(**enc)
        return self._pool(out.last_hidden_state, enc["attention_mask"])


class DenseRetriever:
    """基于稠密向量余弦相似度的 chunk 级检索器。"""

    def __init__(self, encoder: DenseEncoder, chunk_ids: List[str], chunk_texts: List[str]):
        self.encoder = encoder
        self.chunk_ids = chunk_ids
        self.matrix = encoder.encode(chunk_texts)  # [N, D], 已归一化

    def search(self, query: str, top_k: int) -> List[Tuple[str, float]]:
        q = self.encoder.encode([query], is_query=True)[0]
        sims = (self.matrix @ q).tolist()
        ranked = sorted(zip(self.chunk_ids, sims), key=lambda kv: kv[1], reverse=True)
        return [(cid, float(s)) for cid, s in ranked[:top_k]]


# ---------------------------------------------------------------------------
# 重排：交叉编码器（cross-encoder）
# ---------------------------------------------------------------------------
class CrossEncoderReranker:
    """用交叉编码器对候选做精排。

    在 transformers 5.x + 部分 BERT 权重上，fp32 前向可能出现 NaN；本类检测到 NaN 后
    自动回退到 CPU + float64 重算，保证输出有限、可复现。
    """

    def __init__(self, model_name: str, device: str, max_length: int = 512):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self.torch = torch
        self.device = device
        self.max_length = max_length
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name).to(device).eval()

    def score(self, query: str, docs: Sequence[str]) -> List[float]:
        torch = self.torch
        if not docs:
            return []
        enc = self.tokenizer(
            [query] * len(docs), list(docs),
            padding=True, truncation=True, max_length=self.max_length, return_tensors="pt",
        ).to(self.device)
        with torch.no_grad():
            logits = self.model(**enc).logits.squeeze(-1).float()
        if torch.isnan(logits).any():
            # 回退：CPU + float64 重算
            enc_cpu = {k: v.to("cpu") for k, v in enc.items()}
            model64 = self.model.to("cpu").double()
            with torch.no_grad():
                logits = model64(**enc_cpu).logits.squeeze(-1)
            self.model = self.model.to(self.device).float()
        return [float(x) for x in logits.reshape(-1).tolist()]

    def rerank(self, query: str, candidates: List[Tuple[str, str]], top_k: int) -> List[Tuple[str, float]]:
        """candidates: [(doc_id, text)] -> [(doc_id, rerank_score)] 降序，取 top_k。"""
        scores = self.score(query, [text for _, text in candidates])
        ranked = sorted(
            ((doc_id, s) for (doc_id, _), s in zip(candidates, scores)),
            key=lambda kv: kv[1], reverse=True,
        )
        return ranked[:top_k]


# ---------------------------------------------------------------------------
# chunk 级结果 -> doc 级结果（同一文档取最高分的 chunk）
# ---------------------------------------------------------------------------
def chunks_to_docs(ranked_chunks: List[Tuple[str, float]], chunk_to_doc: Dict[str, str]) -> List[Tuple[str, float]]:
    best: Dict[str, float] = {}
    for chunk_id, score in ranked_chunks:
        doc_id = chunk_to_doc[chunk_id]
        if doc_id not in best or score > best[doc_id]:
            best[doc_id] = score
    return sorted(best.items(), key=lambda kv: kv[1], reverse=True)


# ---------------------------------------------------------------------------
# 评测指标
# ---------------------------------------------------------------------------
def recall_at_k(ranked_ids: List[str], gold: Sequence[str], k: int) -> float:
    if not gold:
        return 0.0
    topk = set(ranked_ids[:k])
    return len(topk & set(gold)) / len(gold)


def reciprocal_rank(ranked_ids: List[str], gold: Sequence[str]) -> float:
    gold_set = set(gold)
    for idx, doc_id in enumerate(ranked_ids, start=1):
        if doc_id in gold_set:
            return 1.0 / idx
    return 0.0


def ndcg_at_k(ranked_ids: List[str], gold: Sequence[str], k: int) -> float:
    gold_set = set(gold)
    dcg = 0.0
    for idx, doc_id in enumerate(ranked_ids[:k], start=1):
        if doc_id in gold_set:
            dcg += 1.0 / math.log2(idx + 1)
    ideal_hits = min(len(gold_set), k)
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_hits + 1))
    return dcg / idcg if idcg > 0 else 0.0


def aggregate_metrics(per_query_ranked: List[Tuple[List[str], Sequence[str]]], k: int) -> Dict[str, float]:
    n = len(per_query_ranked)
    if n == 0:
        return {"recall@k": 0.0, "mrr": 0.0, "ndcg@k": 0.0}
    recall = sum(recall_at_k(r, g, k) for r, g in per_query_ranked) / n
    mrr = sum(reciprocal_rank(r, g) for r, g in per_query_ranked) / n
    ndcg = sum(ndcg_at_k(r, g, k) for r, g in per_query_ranked) / n
    return {"recall@k": recall, "mrr": mrr, "ndcg@k": ndcg}


# ---------------------------------------------------------------------------
# 流水线：为一条查询产出各方法的文档级排名
# ---------------------------------------------------------------------------
class Pipeline:
    def __init__(self, corpus, args):
        self.args = args
        self.chunk_ids: List[str] = []
        self.chunk_texts: List[str] = []
        self.chunk_to_doc: Dict[str, str] = {}
        self.doc_text: Dict[str, str] = {}

        # 分块
        for doc in corpus:
            self.doc_text[doc["doc_id"]] = doc["text"]
            chunks = chunk_text(doc["text"], args.chunk_size, args.chunk_overlap)
            for i, chunk in enumerate(chunks):
                cid = f"{doc['doc_id']}::c{i}" if len(chunks) > 1 else doc["doc_id"]
                self.chunk_ids.append(cid)
                self.chunk_texts.append(chunk)
                self.chunk_to_doc[cid] = doc["doc_id"]

        self.n_docs = len(corpus)
        self.n_chunks = len(self.chunk_ids)

        # 稀疏索引
        self.bm25 = BM25Retriever(self.chunk_ids, self.chunk_texts)

        # 稠密索引（可选）
        self.dense: Optional[DenseRetriever] = None
        if args.use_dense:
            encoder = DenseEncoder(args.embed_model, args.pooling, args.device,
                                   query_instruct=args.query_instruct)
            self.dense = DenseRetriever(encoder, self.chunk_ids, self.chunk_texts)

        # 重排器（可选）
        self.reranker: Optional[CrossEncoderReranker] = None
        if args.use_rerank:
            self.reranker = CrossEncoderReranker(args.reranker_model, args.device)

    def run_query(self, query: str) -> Dict[str, List[Tuple[str, float]]]:
        """返回各方法的 doc 级排名 {method: [(doc_id, score)]}。"""
        top_k = self.args.top_k
        sparse_started = time.perf_counter()
        sparse_chunks = self.bm25.search(query, top_k)
        sparse_docs = chunks_to_docs(sparse_chunks, self.chunk_to_doc)
        sparse_ms = (time.perf_counter() - sparse_started) * 1000

        out: Dict[str, List[Tuple[str, float]]] = {"sparse": sparse_docs}
        component_ms = {"sparse": sparse_ms}

        if self.dense is not None:
            dense_started = time.perf_counter()
            dense_chunks = self.dense.search(query, top_k)
            dense_docs = chunks_to_docs(dense_chunks, self.chunk_to_doc)
            dense_ms = (time.perf_counter() - dense_started) * 1000
            component_ms["dense"] = dense_ms
            out["dense"] = dense_docs

            ranked_lists = {"dense": dense_docs, "sparse": sparse_docs}
            weights = {"dense": self.args.dense_weight, "sparse": self.args.sparse_weight}
            rrf_started = time.perf_counter()
            rrf = fuse(ranked_lists, method="rrf", k=self.args.k_rrf, weights=weights)
            rrf_ms = (time.perf_counter() - rrf_started) * 1000
            weighted_started = time.perf_counter()
            weighted = fuse(ranked_lists, method="weighted", weights=weights)
            weighted_ms = (time.perf_counter() - weighted_started) * 1000
            component_ms.update({"rrf_fusion": rrf_ms, "weighted_fusion": weighted_ms})
            out["rrf"] = rrf
            out["weighted"] = weighted

            if self.reranker is not None:
                # 对 RRF 融合的候选池 top-N 精排
                pool = [doc_id for doc_id, _ in rrf[: self.args.rerank_pool]]
                candidates = [(doc_id, self.doc_text[doc_id]) for doc_id in pool]
                rerank_started = time.perf_counter()
                reranked = self.reranker.rerank(query, candidates, self.args.rerank_top_k)
                component_ms["rerank"] = (time.perf_counter() - rerank_started) * 1000
                out["rerank"] = reranked

        end_to_end_ms = {"sparse": sparse_ms}
        if "dense" in component_ms:
            retrieval_ms = sparse_ms + component_ms["dense"]
            end_to_end_ms.update(
                {
                    "dense": component_ms["dense"],
                    "rrf": retrieval_ms + component_ms["rrf_fusion"],
                    "weighted": retrieval_ms + component_ms["weighted_fusion"],
                }
            )
            if "rerank" in component_ms:
                end_to_end_ms["rerank"] = (
                    retrieval_ms + component_ms["rrf_fusion"] + component_ms["rerank"]
                )
        rank_changes = []
        if "rerank" in out:
            before = {doc_id: rank for rank, (doc_id, _) in enumerate(out["rrf"], 1)}
            after = {doc_id: rank for rank, (doc_id, _) in enumerate(out["rerank"], 1)}
            for doc_id in sorted(set(before) | set(after)):
                rank_changes.append(
                    {
                        "doc_id": doc_id,
                        "rrf_rank": before.get(doc_id),
                        "rerank_rank": after.get(doc_id),
                        "delta": (
                            before[doc_id] - after[doc_id]
                            if doc_id in before and doc_id in after
                            else None
                        ),
                    }
                )
        self.last_trace = {
            "component_latency_ms": component_ms,
            "end_to_end_latency_ms": end_to_end_ms,
            "rank_changes": rank_changes,
        }

        return out


# ---------------------------------------------------------------------------
# 输出：对比表 / 单条查询追踪
# ---------------------------------------------------------------------------
METHOD_LABELS = [
    ("sparse", "BM25 (sparse)"),
    ("dense", "Dense"),
    ("rrf", "Hybrid-RRF"),
    ("weighted", "Hybrid-Weighted"),
    ("rerank", "Hybrid-RRF+Rerank"),
]


def run_evaluation(pipeline: Pipeline, queries, args) -> Dict[str, Any]:
    k = args.eval_k
    per_method: Dict[str, List[Tuple[List[str], Sequence[str]]]] = {m: [] for m, _ in METHOD_LABELS}
    per_query_records = []
    latency_by_method: Dict[str, List[float]] = {m: [] for m, _ in METHOD_LABELS}

    t0 = time.time()
    for spec in queries:
        query = spec["query"]
        gold = spec.get("expected", [])
        results = pipeline.run_query(query)
        record = {
            "query": query,
            "expected": gold,
            "category": spec.get("category", "unspecified"),
            "methods": {},
            "trace": pipeline.last_trace,
        }
        for method, _ in METHOD_LABELS:
            if method not in results:
                continue
            ranked_ids = [doc_id for doc_id, _ in results[method]]
            per_method[method].append((ranked_ids, gold))
            latency_by_method[method].append(pipeline.last_trace["end_to_end_latency_ms"][method])
            record["methods"][method] = {
                "top": [{"doc_id": d, "score": round(s, 4)} for d, s in results[method][:5]],
                "recall@k": round(recall_at_k(ranked_ids, gold, k), 4),
                "mrr": round(reciprocal_rank(ranked_ids, gold), 4),
                "ndcg@k": round(ndcg_at_k(ranked_ids, gold, k), 4),
            }
        per_query_records.append(record)
    elapsed = time.time() - t0

    summary = {}
    for method, _ in METHOD_LABELS:
        if per_method[method]:
            summary[method] = aggregate_metrics(per_method[method], k)
            values = sorted(latency_by_method[method])
            p95_index = min(len(values) - 1, math.ceil(0.95 * len(values)) - 1)
            summary[method]["latency_ms"] = {
                "mean": sum(values) / len(values),
                "p50": values[len(values) // 2],
                "p95": values[p95_index],
            }

    return {
        "summary": summary,
        "per_query": per_query_records,
        "elapsed_sec": round(elapsed, 2),
        "eval_k": k,
    }


def print_table(report: Dict[str, Any], pipeline: Pipeline, args) -> None:
    k = report["eval_k"]
    print("=" * 78)
    print("混合检索流水线 · 逐阶段评测对比")
    print("=" * 78)
    print(f"语料: {pipeline.n_docs} 篇文档 → {pipeline.n_chunks} 个 chunk "
          f"(chunk_size={args.chunk_size}, overlap={args.chunk_overlap})")
    print(f"查询: {len(report['per_query'])} 条   "
          f"稠密模型: {args.embed_model if args.use_dense else '(禁用)'}   "
          f"重排模型: {args.reranker_model if args.use_rerank else '(禁用)'}")
    print(f"检索 top_k={args.top_k}  融合 k(RRF)={args.k_rrf}  "
          f"重排候选池={args.rerank_pool}  评测截断 k={k}  设备={args.device}")
    print(f"耗时: {report['elapsed_sec']}s")
    print("-" * 78)
    header = f"{'Stage / Method':<22}{'Recall@'+str(k):>12}{'MRR':>12}{'nDCG@'+str(k):>12}"
    print(header)
    print("-" * 78)
    for method, label in METHOD_LABELS:
        if method not in report["summary"]:
            continue
        m = report["summary"][method]
        print(f"{label:<22}{m['recall@k']:>12.4f}{m['mrr']:>12.4f}{m['ndcg@k']:>12.4f}")
    print("-" * 78)
    print("读表：从上到下逐步加入 稠密检索 / 融合 / 重排 阶段，观察指标的变化。")
    print("=" * 78)


def print_per_query(report: Dict[str, Any]) -> None:
    """逐条查询打印各方法的 MRR，直观展示「单路会翻车、融合来兜底」。"""
    methods = [m for m, _ in METHOD_LABELS]
    short = {"sparse": "BM25", "dense": "Dense", "rrf": "RRF",
             "weighted": "Wgt", "rerank": "Rerank"}
    print("\n逐条查询 MRR 明细（1.00=正确文档排在第 1 位；粗看哪一路在哪类查询上翻车）")
    print("-" * 78)
    header = f"{'Query':<42}" + "".join(f"{short[m]:>7}" for m in methods)
    print(header)
    print("-" * 78)
    for rec in report["per_query"]:
        cells = ""
        for m in methods:
            if m in rec["methods"]:
                cells += f"{rec['methods'][m]['mrr']:>7.2f}"
            else:
                cells += f"{'-':>7}"
        q = rec["query"]
        q = q if len(q) <= 41 else q[:38] + "..."
        print(f"{q:<42}{cells}")
    print("=" * 78)


def print_query_trace(pipeline: Pipeline, query: str, args) -> None:
    results = pipeline.run_query(query)
    print("=" * 78)
    print(f"单条查询逐阶段排名追踪   query = {query!r}")
    print(f"语料 {pipeline.n_docs} 篇 → {pipeline.n_chunks} chunk   设备={args.device}")
    print("=" * 78)
    for method, label in METHOD_LABELS:
        if method not in results:
            continue
        print(f"\n[{label}]")
        for rank, (doc_id, score) in enumerate(results[method][:5], start=1):
            snippet = pipeline.doc_text.get(doc_id, "")[:60].replace("\n", " ")
            print(f"  {rank}. {doc_id:<14} score={score:8.4f}  {snippet}")
    print("=" * 78)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def detect_device(requested: str) -> str:
    if requested != "auto":
        return requested
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        if torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="混合检索流水线离线评测 CLI（chunk→embed→retrieve→fuse→rerank，逐阶段对比）。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  python evaluate.py                       # 内置评测集，完整对比表\n"
            "  python evaluate.py --no-rerank           # 跳过重排阶段\n"
            "  python evaluate.py --no-dense            # 仅 BM25（纯离线、无需模型）\n"
            "  python evaluate.py --query '怎样提升检索精度'  # 单条查询逐阶段排名\n"
            "  python evaluate.py --embed-model BAAI/bge-m3 --pooling cls\n"
            "  python evaluate.py --output result.json  # 结果同时写入 JSON\n"
        ),
    )
    data = parser.add_argument_group("数据")
    data.add_argument("--corpus", help="语料 JSON 文件，格式 [{'doc_id','text'}...]；缺省用内置语料")
    data.add_argument("--queries", help="查询 JSON 文件，格式 [{'query','expected':[...]}...]；缺省用内置查询")
    data.add_argument("--query", help="单条查询模式：只对该查询做逐阶段排名追踪，不跑评测")
    data.add_argument("--limit-queries", type=int, default=0, help="只评测前 N 条查询（0=全部）")

    stages = parser.add_argument_group("流水线阶段")
    stages.add_argument("--no-dense", dest="use_dense", action="store_false",
                        help="禁用稠密检索（连带禁用融合与重排；退化为纯 BM25，完全离线无需模型）")
    stages.add_argument("--no-rerank", dest="use_rerank", action="store_false",
                        help="禁用神经重排阶段")
    stages.set_defaults(use_dense=True, use_rerank=True)

    chunk = parser.add_argument_group("分块")
    chunk.add_argument("--chunk-size", type=int, default=280, help="每个 chunk 的最大字符数（默认 280）")
    chunk.add_argument("--chunk-overlap", type=int, default=40, help="相邻 chunk 的重叠字符数（默认 40）")

    retr = parser.add_argument_group("检索与融合")
    retr.add_argument("--top-k", type=int, default=10, help="每路检索召回的候选数（默认 10）")
    retr.add_argument("--k-rrf", type=int, default=60, help="RRF 平滑常数 k（默认 60）")
    retr.add_argument("--dense-weight", type=float, default=1.0, help="融合时稠密路权重（默认 1.0）")
    retr.add_argument("--sparse-weight", type=float, default=1.0, help="融合时稀疏路权重（默认 1.0）")

    rer = parser.add_argument_group("重排")
    rer.add_argument("--rerank-pool", type=int, default=10, help="送入重排的候选池大小（取 RRF 融合的 top-N，默认 10）")
    rer.add_argument("--rerank-top-k", type=int, default=10, help="重排后返回的结果数（默认 10）")

    model = parser.add_argument_group("模型")
    model.add_argument("--embed-model", default="sentence-transformers/all-MiniLM-L6-v2",
                       help="稠密句向量模型（默认 sentence-transformers/all-MiniLM-L6-v2，约 90MB、英文为主；"
                            "多语言语料请换 Qwen/Qwen3-Embedding-0.6B 或 BAAI/bge-m3）")
    model.add_argument("--pooling", default="auto", choices=["auto", "mean", "cls", "last"],
                       help="句向量池化方式（auto 会按模型名自动选择：qwen→last, bge-m3→cls, 其余→mean）")
    model.add_argument("--query-instruct",
                       default="Given a search query, retrieve relevant passages that answer the query",
                       help="指令式检索模型的查询侧任务指令（仅对 last-token 池化的模型如 Qwen3-Embedding 生效）")
    model.add_argument("--reranker-model", default="BAAI/bge-reranker-base",
                       help="交叉编码器重排模型（默认 BAAI/bge-reranker-base，多语言、首次运行约 1.1GB；"
                            "生产可换更强的 BAAI/bge-reranker-v2-m3，轻量可换 cross-encoder/ms-marco-MiniLM-L-6-v2）")
    model.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda", "mps"],
                       help="推理设备（默认 auto）")

    out = parser.add_argument_group("评测与输出")
    out.add_argument("--eval-k", type=int, default=3, help="指标截断位置 k（Recall@k / nDCG@k，默认 3）")
    out.add_argument("--no-per-query", dest="show_per_query", action="store_false",
                     help="不打印逐条查询的 MRR 明细矩阵")
    out.set_defaults(show_per_query=True)
    out.add_argument("--output", help="把完整结果（含每条查询明细）写入该 JSON 文件")
    out.add_argument("--offline", action="store_true", help="设置 HF_HUB_OFFLINE=1，强制只用本地缓存模型")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.offline:
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"

    args.device = detect_device(args.device)
    # 单查询追踪模式不影响 use_dense/use_rerank 语义，但重排依赖稠密融合池
    if not args.use_dense:
        args.use_rerank = False

    corpus = load_json(args.corpus) if args.corpus else DEFAULT_CORPUS
    queries = load_json(args.queries) if args.queries else DEFAULT_QUERIES

    try:
        pipeline = Pipeline(corpus, args)
    except Exception as exc:  # noqa: BLE001
        print(f"[错误] 流水线初始化失败: {exc}", file=sys.stderr)
        print("提示：稠密/重排阶段需要本地句向量与交叉编码器模型；"
              "可用 --no-dense 退化为纯 BM25（完全离线），或用 --embed-model 指定已缓存模型。",
              file=sys.stderr)
        return 1

    if args.query:
        print_query_trace(pipeline, args.query, args)
        return 0

    if args.limit_queries > 0:
        queries = queries[: args.limit_queries]

    report = run_evaluation(pipeline, queries, args)
    print_table(report, pipeline, args)
    if args.show_per_query:
        print_per_query(report)

    if args.output:
        payload = {
            "config": {
                "embed_model": args.embed_model if args.use_dense else None,
                "reranker_model": args.reranker_model if args.use_rerank else None,
                "top_k": args.top_k, "k_rrf": args.k_rrf, "eval_k": args.eval_k,
                "chunk_size": args.chunk_size, "chunk_overlap": args.chunk_overlap,
                "device": args.device,
            },
            **report,
        }
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"\n结果已写入 {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
