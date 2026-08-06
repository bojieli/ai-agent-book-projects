#!/usr/bin/env python3
"""上下文感知检索对比评测（实验 3-10）

本脚本用可控的对比实验量化“上下文感知检索”相较传统分块的检索召回提升：
同一批文本块分别以两种方式建立 BM25 索引——

  * 无上下文（plain）  ：只索引原始文本块 metadata.original_text
  * 有上下文（contextual）：索引 LLM 生成的前缀 + 原始文本块（content 字段）

然后在同一评测集上比较 recall@k（命中率：前 k 个结果中是否含有相关文本块）。
这正是 Anthropic “Contextual Retrieval” 的核心主张：为文本块补上上下文前缀，
能同时增强 BM25（稀疏）与向量（稠密）检索的召回率。

BM25 检索完全离线，无需任何 API 或检索服务；embedding / hybrid 方法需要
调用 embedding API（见 --method 说明）。

用法示例：
  python compare_retrieval.py                       # 用默认评测集跑对比表
  python compare_retrieval.py --query "国家主席有哪些职权？"   # 单条查询并排对比
  python compare_retrieval.py --mode plain          # 只看无上下文基线
  python compare_retrieval.py --output result.json  # 另存机器可读结果
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from rank_bm25 import BM25Okapi

try:
    import jieba
    if hasattr(jieba, "setLogLevel"):
        jieba.setLogLevel(60)  # 关闭 jieba 的加载日志
    _HAS_JIEBA = True
except Exception:  # pragma: no cover - jieba 一般随 requirements 安装
    _HAS_JIEBA = False


# ---------------------------------------------------------------------------
# 分词：中文没有空格，直接 .split() 会把整段当成一个 token，BM25 完全失效。
# 默认用 jieba 分词；--no-jieba 时退化为字符二元组（bigram），同样可离线运行。
# ---------------------------------------------------------------------------
def tokenize(text: str, use_jieba: bool = True) -> List[str]:
    """把文本切成 token 列表，供 BM25 使用。"""
    text = (text or "").lower()
    if use_jieba and _HAS_JIEBA:
        return [t for t in jieba.cut(text) if t.strip()]
    # 退化方案：中文字符二元组 + 连续 ASCII 词
    tokens: List[str] = []
    buf = ""
    chars = list(text)
    for ch in chars:
        if ch.isascii() and (ch.isalnum()):
            buf += ch
            continue
        if buf:
            tokens.append(buf)
            buf = ""
        if not ch.isspace():
            tokens.append(ch)
    if buf:
        tokens.append(buf)
    # 追加中文 bigram，提升匹配粒度
    cjk = [c for c in text if "一" <= c <= "鿿"]
    tokens.extend(cjk[i] + cjk[i + 1] for i in range(len(cjk) - 1))
    return tokens


# ---------------------------------------------------------------------------
# 语料加载
# ---------------------------------------------------------------------------
def load_corpus(path: str) -> List[Dict]:
    """从 document_store.json 载入分块，返回 [{chunk_id, contextual, plain, context}]。

    每个分块的 content 字段是“上下文前缀 + 原始文本”，metadata.original_text
    是不带上下文的原始文本，正好用于两种索引方式的对照。
    """
    with open(path, "r", encoding="utf-8") as f:
        store = json.load(f)

    chunks: List[Dict] = []
    for chunk_id, entry in store.items():
        if "_chunk_" not in chunk_id:
            continue  # 跳过整篇文档条目
        if not isinstance(entry, dict):
            continue
        meta = entry.get("metadata", {}) or {}
        contextual_text = entry.get("content", "") or ""
        plain_text = meta.get("original_text") or contextual_text
        # 上下文前缀 = contextual 去掉结尾的 original_text
        context = contextual_text
        if plain_text and contextual_text.endswith(plain_text):
            context = contextual_text[: len(contextual_text) - len(plain_text)].strip()
        chunks.append({
            "chunk_id": chunk_id,
            "contextual": contextual_text,
            "plain": plain_text,
            "context": context,
        })
    return chunks


def load_eval(path: str) -> List[Dict]:
    """载入评测集，返回 [{id, query, gold_chunk_id, ...}]。"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("queries", data if isinstance(data, list) else [])


# ---------------------------------------------------------------------------
# BM25 检索器
# ---------------------------------------------------------------------------
class BM25Retriever:
    """对给定文本字段建立 BM25 索引的简单检索器。"""

    def __init__(self, chunks: List[Dict], field: str, use_jieba: bool = True):
        self.chunk_ids = [c["chunk_id"] for c in chunks]
        self.use_jieba = use_jieba
        corpus_tokens = [tokenize(c[field], use_jieba) for c in chunks]
        self.index = BM25Okapi(corpus_tokens)

    def rank(self, query: str) -> List[str]:
        """返回按相关性从高到低排序的 chunk_id 列表。"""
        scores = self.index.get_scores(tokenize(query, self.use_jieba))
        order = np.argsort(scores)[::-1]
        return [self.chunk_ids[i] for i in order]

    def scored(self, query: str, top_k: int) -> List[Dict]:
        """返回前 top_k 个结果及其分数。"""
        scores = self.index.get_scores(tokenize(query, self.use_jieba))
        order = np.argsort(scores)[::-1][:top_k]
        return [{"chunk_id": self.chunk_ids[i], "score": float(scores[i])} for i in order]


# ---------------------------------------------------------------------------
# 评测
# ---------------------------------------------------------------------------
def recall_at_k(retriever: BM25Retriever, queries: List[Dict], ks: List[int]) -> Dict:
    """计算一批查询在各 k 值下的 recall@k（命中率）。"""
    per_query = []
    hits = {k: 0 for k in ks}
    for q in queries:
        ranking = retriever.rank(q["query"])
        gold = q["gold_chunk_id"]
        rank_pos = ranking.index(gold) + 1 if gold in ranking else None
        row = {"id": q.get("id"), "query": q["query"], "gold": gold, "rank": rank_pos}
        for k in ks:
            hit = rank_pos is not None and rank_pos <= k
            row[f"hit@{k}"] = hit
            if hit:
                hits[k] += 1
        per_query.append(row)
    n = len(queries)
    recall = {k: (hits[k] / n if n else 0.0) for k in ks}
    return {"recall": recall, "per_query": per_query, "n": n}


def print_comparison_table(plain: Optional[Dict], contextual: Optional[Dict], ks: List[int]):
    """打印 recall@k 对比表。"""
    print("\n" + "=" * 68)
    print("检索召回对比：无上下文分块  vs.  上下文感知检索（BM25）")
    print("=" * 68)
    header = "  k  | " + " | ".join(f"{'无上下文':>10}" if False else f"recall@{k:<3}" for k in ks)
    # 逐行打印每个方法
    col_w = 12
    line = f"{'方法':<16}" + "".join(f"recall@{k}".rjust(col_w) for k in ks)
    print(line)
    print("-" * len(line))
    if plain:
        print(f"{'无上下文 (plain)':<16}" + "".join(f"{plain['recall'][k]*100:>10.1f}%" for k in ks))
    if contextual:
        print(f"{'有上下文 (ctx)':<16}" + "".join(f"{contextual['recall'][k]*100:>10.1f}%" for k in ks))
    if plain and contextual:
        print("-" * len(line))
        deltas = []
        for k in ks:
            d = (contextual["recall"][k] - plain["recall"][k]) * 100
            deltas.append(f"{d:>+9.1f}pp")
        print(f"{'提升 (Δpp)':<16}" + "".join(s.rjust(col_w) for s in deltas))
        # 检索失败率下降（对应书中“1 - recall@k”口径）
        print("-" * len(line))
        fails = []
        for k in ks:
            p_fail = 1 - plain["recall"][k]
            c_fail = 1 - contextual["recall"][k]
            if p_fail > 0:
                red = (p_fail - c_fail) / p_fail * 100
                fails.append(f"{red:>9.0f}%")
            else:
                fails.append(f"{'-':>10}")
        print(f"{'失败率下降':<16}" + "".join(s.rjust(col_w) for s in fails))
    print("=" * 68)


def print_per_query(result: Dict, label: str):
    print(f"\n[{label}] 每条查询命中排名（rank=gold 文本块在结果中的名次，— 表示未召回）")
    for row in result["per_query"]:
        print(f"  {row['id']}  rank={str(row['rank']):>3}  gold={row['gold']:<28} {row['query'][:32]}")


# ---------------------------------------------------------------------------
# 单条查询并排对比
# ---------------------------------------------------------------------------
def single_query_compare(chunks: List[Dict], query: str, top_k: int, use_jieba: bool,
                         mode: str):
    id2chunk = {c["chunk_id"]: c for c in chunks}

    def show(field_label, field):
        retr = BM25Retriever(chunks, field, use_jieba)
        print(f"\n[{field_label}] Top-{top_k}")
        print("-" * 60)
        for i, r in enumerate(retr.scored(query, top_k), 1):
            c = id2chunk[r["chunk_id"]]
            snippet = c["plain"].replace("<!-- FORCE BREAK -->", "").replace("\n", " ").strip()[:48]
            ctx = c["context"].replace("\n", " ").strip()[:40]
            print(f"  {i}. score={r['score']:6.2f}  {r['chunk_id']}")
            if field == "contextual" and ctx:
                print(f"       上下文前缀: {ctx}")
            print(f"       原文: {snippet}")

    print("\n" + "=" * 60)
    print(f"查询: {query}")
    print("=" * 60)
    if mode in ("plain", "both"):
        show("无上下文 (plain)", "plain")
    if mode in ("contextual", "both"):
        show("有上下文 (contextual)", "contextual")


# ---------------------------------------------------------------------------
# 可选：embedding / hybrid（需要 API）
# ---------------------------------------------------------------------------
def embedding_unavailable_notice(method: str):
    print(f"\n[提示] --method {method} 需要调用 embedding API（稠密向量），无法离线运行。")
    print("       请在 .env 中配置 OPENAI_API_KEY / SILICONFLOW_API_KEY 等，")
    print("       并使用 contextual_tools.ContextualKnowledgeBaseTools 的 embedding/hybrid 检索。")
    print("       本脚本的默认 --method bm25 已可完整复现书中“上下文增强 BM25”的召回提升结论。")


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="上下文感知检索对比评测：量化上下文前缀对检索召回（recall@k）的提升（实验 3-10）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例:\n"
               "  python compare_retrieval.py\n"
               "  python compare_retrieval.py --query \"国家主席有哪些职权？\" --top-k 5\n"
               "  python compare_retrieval.py --mode both --k 1 3 5 --output result.json",
    )
    p.add_argument("--corpus", default="document_store.json",
                   help="语料文件（含 content 与 metadata.original_text 的分块存储），默认 document_store.json")
    p.add_argument("--eval", dest="eval_path", default="evaluation/retrieval_eval.json",
                   help="评测集（query + gold_chunk_id），默认 evaluation/retrieval_eval.json")
    p.add_argument("--query", default=None,
                   help="临时单条查询：并排展示无上下文/有上下文的 Top-K 检索结果（不跑整个评测集）")
    p.add_argument("--mode", choices=["plain", "contextual", "both"], default="both",
                   help="对比哪种索引：plain=仅无上下文，contextual=仅有上下文，both=两者对比（默认）")
    p.add_argument("--method", choices=["bm25", "embedding", "hybrid"], default="bm25",
                   help="检索方法：bm25（离线，默认）；embedding/hybrid 需 embedding API")
    p.add_argument("--k", nargs="+", type=int, default=[1, 3, 5],
                   help="评测的 k 值列表（recall@k），默认 1 3 5")
    p.add_argument("--top-k", type=int, default=5,
                   help="--query 单查询模式下每种方法展示的结果条数，默认 5")
    p.add_argument("--model", default=None,
                   help="embedding 模型名（仅 --method embedding/hybrid 时生效）")
    p.add_argument("--no-jieba", action="store_true",
                   help="禁用 jieba 分词，改用字符二元组分词（无需 jieba 依赖）")
    p.add_argument("--output", default=None,
                   help="将机器可读的评测结果写入该 JSON 文件")
    p.add_argument("--per-query", action="store_true",
                   help="额外打印每条查询的命中排名明细")
    return p


def main():
    args = build_arg_parser().parse_args()
    use_jieba = not args.no_jieba

    corpus_path = Path(args.corpus)
    if not corpus_path.exists():
        print(f"[错误] 找不到语料文件: {corpus_path}", file=sys.stderr)
        sys.exit(1)

    chunks = load_corpus(str(corpus_path))
    if not chunks:
        print(f"[错误] 语料中没有可用分块（缺少 *_chunk_* 条目）: {corpus_path}", file=sys.stderr)
        sys.exit(1)

    print(f"已加载 {len(chunks)} 个文本块 | 分词: {'jieba' if (use_jieba and _HAS_JIEBA) else '字符bigram'} "
          f"| 检索方法: {args.method}")

    if args.method in ("embedding", "hybrid"):
        embedding_unavailable_notice(args.method)
        # 仍继续用 BM25 给出可运行的离线结果
        print("       以下改用 BM25 给出离线对照结果。\n")

    # 单条查询模式
    if args.query:
        single_query_compare(chunks, args.query, args.top_k, use_jieba, args.mode)
        return

    # 评测集模式
    eval_path = Path(args.eval_path)
    if not eval_path.exists():
        print(f"[错误] 找不到评测集: {eval_path}", file=sys.stderr)
        sys.exit(1)
    queries = load_eval(str(eval_path))
    ks = sorted(set(args.k))

    plain_res = contextual_res = None
    if args.mode in ("plain", "both"):
        plain_res = recall_at_k(BM25Retriever(chunks, "plain", use_jieba), queries, ks)
    if args.mode in ("contextual", "both"):
        contextual_res = recall_at_k(BM25Retriever(chunks, "contextual", use_jieba), queries, ks)

    print(f"评测集: {eval_path}  共 {len(queries)} 条查询")
    print_comparison_table(plain_res, contextual_res, ks)

    if args.per_query:
        if plain_res:
            print_per_query(plain_res, "无上下文 plain")
        if contextual_res:
            print_per_query(contextual_res, "有上下文 contextual")

    if args.output:
        out = {
            "corpus": str(corpus_path),
            "eval": str(eval_path),
            "num_chunks": len(chunks),
            "num_queries": len(queries),
            "tokenizer": "jieba" if (use_jieba and _HAS_JIEBA) else "char-bigram",
            "k": ks,
            "plain": plain_res,
            "contextual": contextual_res,
        }
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"\n结果已写入 {args.output}")


if __name__ == "__main__":
    main()
