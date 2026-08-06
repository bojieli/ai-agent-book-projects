"""离线对比：上下文化记忆块 vs 原始记忆块对『用户事实召回』的影响（实验 3-11）。

本模块是一个**完全离线、无需 API/外部服务**的对照实验，用于量化本章核心论点：
在把对话记忆块送入索引/嵌入之前，先为每个块生成一段『上下文前缀』（情境锚定），
能显著提升脱离上下文的孤立片段（如『好的，就订这个吧』）被正确召回的概率。

方法说明（诚实边界）：
- 生产管线用 LLM 逐块生成 context、并用神经嵌入 + 检索服务做稠密/混合检索（需 API Key）。
- 这里用**确定性的 BM25 词法检索**作为无需 API 的代理：对同一份 context，
  分别度量『不拼接（plain）』与『拼接后再索引（contextual）』两种方式的召回。
  变量只有『索引文本是否含 context 前缀』，因此结果直接反映上下文化本身的贡献。
- 指标：Recall@1、Recall@3、MRR（口径同书中 recall@k：前 k 个结果命中即算召回）。

数据集见同目录 memory_qa_eval.json（受控教学集，可自行替换 --dataset）。
"""

import argparse
import json
import math
import re
from pathlib import Path
from typing import Dict, List, Tuple

DEFAULT_DATASET = str(Path(__file__).parent / "memory_qa_eval.json")

_CJK = r"一-鿿"


def tokenize(text: str) -> List[str]:
    """CJK 感知的轻量分词：英文/数字按词，中文按『单字 + 相邻双字』。

    对相邻双字（bigram）保留位置邻接关系，避免跨片段产生虚假二元组。
    """
    text = text.lower()
    tokens: List[str] = []
    tokens.extend(re.findall(r"[a-z0-9]+", text))
    for run in re.findall(f"[{_CJK}]+", text):
        chars = list(run)
        tokens.extend(chars)
        for i in range(len(chars) - 1):
            tokens.append(chars[i] + chars[i + 1])
    return tokens


class BM25:
    """标准 BM25，纯 Python 实现，无第三方依赖。"""

    def __init__(self, corpus_tokens: List[List[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus = corpus_tokens
        self.N = len(corpus_tokens)
        self.doc_len = [len(d) for d in corpus_tokens]
        self.avgdl = sum(self.doc_len) / self.N if self.N else 0.0
        self.tf: List[Dict[str, int]] = []
        df: Dict[str, int] = {}
        for doc in corpus_tokens:
            counts: Dict[str, int] = {}
            for t in doc:
                counts[t] = counts.get(t, 0) + 1
            self.tf.append(counts)
            for t in counts:
                df[t] = df.get(t, 0) + 1
        self.idf = {
            t: math.log(1 + (self.N - n + 0.5) / (n + 0.5)) for t, n in df.items()
        }

    def score(self, query_tokens: List[str], idx: int) -> float:
        counts = self.tf[idx]
        dl = self.doc_len[idx]
        s = 0.0
        for t in query_tokens:
            if t not in counts:
                continue
            idf = self.idf.get(t, 0.0)
            freq = counts[t]
            denom = freq + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
            s += idf * (freq * (self.k1 + 1)) / denom
        return s

    def rank(self, query_tokens: List[str]) -> List[int]:
        scored = [(self.score(query_tokens, i), i) for i in range(self.N)]
        # 稳定排序：分数降序，平局按原始下标升序
        scored.sort(key=lambda x: (-x[0], x[1]))
        return [i for _, i in scored]


def _gold_rank(ranked_ids: List[str], gold_id: str) -> int:
    """返回 gold 在排序结果中的名次（1-based）；未找到返回 0。"""
    for pos, cid in enumerate(ranked_ids, start=1):
        if cid == gold_id:
            return pos
    return 0


def evaluate(chunks: List[dict], queries: List[dict], mode: str) -> Tuple[dict, List[dict]]:
    """按指定模式索引并检索，返回聚合指标与逐条明细。

    mode='plain'      索引文本 = chunk['text']
    mode='contextual' 索引文本 = chunk['context'] + '\n' + chunk['text']
    """
    ids = [c["id"] for c in chunks]
    if mode == "plain":
        docs = [c["text"] for c in chunks]
    elif mode == "contextual":
        docs = [f"{c.get('context','')}\n{c['text']}" for c in chunks]
    else:
        raise ValueError(f"unknown mode: {mode}")

    bm25 = BM25([tokenize(d) for d in docs])

    r1 = r3 = 0
    mrr = 0.0
    details = []
    for q in queries:
        ranked = [ids[i] for i in bm25.rank(tokenize(q["q"]))]
        rank = _gold_rank(ranked, q["gold"])
        hit1 = 1 if rank == 1 else 0
        hit3 = 1 if 1 <= rank <= 3 else 0
        r1 += hit1
        r3 += hit3
        mrr += (1.0 / rank) if rank else 0.0
        details.append({"q": q["q"], "gold": q["gold"], "rank": rank,
                        "hit@1": hit1, "hit@3": hit3, "top": ranked[:3]})

    n = len(queries)
    metrics = {
        "recall@1": r1 / n,
        "recall@3": r3 / n,
        "mrr": mrr / n,
        "n_queries": n,
    }
    return metrics, details


def run_comparison(dataset_path: str, output_path: str = None, verbose: bool = True) -> dict:
    data = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    chunks, queries = data["chunks"], data["queries"]

    plain_m, plain_d = evaluate(chunks, queries, "plain")
    ctx_m, ctx_d = evaluate(chunks, queries, "contextual")

    if verbose:
        print("=" * 68)
        print("实验 3-11 · 上下文化记忆块对用户事实召回的影响（离线 BM25 代理）")
        print(f"数据集: {dataset_path}")
        print(f"记忆块: {len(chunks)}  查询: {len(queries)}")
        print("=" * 68)
        print(f"{'方法':<28}{'Recall@1':>10}{'Recall@3':>10}{'MRR':>10}")
        print("-" * 68)
        print(f"{'Plain（直接索引原始块）':<24}{plain_m['recall@1']:>10.3f}"
              f"{plain_m['recall@3']:>10.3f}{plain_m['mrr']:>10.3f}")
        print(f"{'Contextual（上下文化后索引）':<22}{ctx_m['recall@1']:>10.3f}"
              f"{ctx_m['recall@3']:>10.3f}{ctx_m['mrr']:>10.3f}")
        print("-" * 68)
        d1 = ctx_m["recall@1"] - plain_m["recall@1"]
        d3 = ctx_m["recall@3"] - plain_m["recall@3"]
        dm = ctx_m["mrr"] - plain_m["mrr"]
        print(f"{'提升（Δ）':<26}{d1:>+10.3f}{d3:>+10.3f}{dm:>+10.3f}")
        print("=" * 68)
        print("\n逐查询名次（gold 在检索结果中的位次，越小越好；0 表示未召回）：")
        print(f"{'查询':<38}{'Plain':>8}{'Ctx':>8}")
        print("-" * 68)
        pd = {x["q"]: x["rank"] for x in plain_d}
        for x in ctx_d:
            q = x["q"][:36]
            print(f"{q:<38}{pd[x['q']]:>8}{x['rank']:>8}")
        print("=" * 68)
        print("说明：孤立片段（如『好的，就订这个吧』）在 Plain 下缺乏可检索信号，")
        print("上下文化后被『锚定』回其情境，因而召回名次明显提升。")

    result = {
        "dataset": dataset_path,
        "n_chunks": len(chunks),
        "plain": plain_m,
        "contextual": ctx_m,
        "delta": {
            "recall@1": ctx_m["recall@1"] - plain_m["recall@1"],
            "recall@3": ctx_m["recall@3"] - plain_m["recall@3"],
            "mrr": ctx_m["mrr"] - plain_m["mrr"],
        },
        "plain_details": plain_d,
        "contextual_details": ctx_d,
    }

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(json.dumps(result, ensure_ascii=False, indent=2),
                                     encoding="utf-8")
        if verbose:
            print(f"\n结果已保存至: {output_path}")

    return result


def single_query(dataset_path: str, query: str, top_k: int = 3, verbose: bool = True) -> dict:
    """针对单条查询，离线对比 plain 与 contextual 两种索引下的 Top-K 检索结果。"""
    data = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    chunks = data["chunks"]
    ids = [c["id"] for c in chunks]
    qt = tokenize(query)

    out = {"query": query}
    for mode in ("plain", "contextual"):
        if mode == "plain":
            docs = [c["text"] for c in chunks]
        else:
            docs = [f"{c.get('context','')}\n{c['text']}" for c in chunks]
        bm25 = BM25([tokenize(d) for d in docs])
        ranked = bm25.rank(qt)
        out[mode] = [{"id": ids[i], "score": round(bm25.score(qt, i), 4)}
                     for i in ranked[:top_k]]

    if verbose:
        print("=" * 60)
        print(f"查询: {query}")
        print("=" * 60)
        for mode in ("plain", "contextual"):
            label = "Plain（原始块）" if mode == "plain" else "Contextual（上下文化）"
            print(f"\n[{label}] Top-{top_k}:")
            for rank, item in enumerate(out[mode], 1):
                print(f"  {rank}. {item['id']:<18} score={item['score']}")
        print("=" * 60)
    return out


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="离线对比上下文化记忆块 vs 原始记忆块的用户事实召回（实验 3-11，无需 API）",
    )
    p.add_argument("--dataset", default=DEFAULT_DATASET,
                   help="记忆问答对照集 JSON 路径（默认：memory_qa_eval.json）")
    p.add_argument("--output", default=None,
                   help="将对比结果（含逐查询明细）保存为 JSON 的路径（默认不保存）")
    p.add_argument("--quiet", action="store_true", help="仅输出结果 JSON，不打印表格")
    return p


def main():
    args = build_arg_parser().parse_args()
    run_comparison(args.dataset, output_path=args.output, verbose=not args.quiet)


if __name__ == "__main__":
    main()
