"""RAG 检索质量测评：Hit@k / Recall@k / MRR / Faithfulness。

用法（在 jiyaojun/ 下）：
  python -m app.eval.retrieval_quality
  python -m app.eval.retrieval_quality --golden fixtures/eval/rag_golden.yaml

失败阈值见 GOLDEN 文件 thresholds；不达标 exit 1（门禁可见）。
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from app.knowledge.embedding import BgeM3ShimProvider
from app.knowledge.grounding import build_grounded_answer, score_faithfulness
from app.knowledge.rag import RagPipeline

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GOLDEN = ROOT / "fixtures" / "eval" / "rag_golden.yaml"


@dataclass
class CaseResult:
    case_id: str
    hit_at_k: bool
    recall_at_k: float
    mrr: float
    ndcg_at_k: float
    faithfulness: float
    retrieved_ids: list[str]
    notes: str = ""


@dataclass
class EvalReport:
    results: list[CaseResult] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)
    thresholds: dict[str, float] = field(default_factory=dict)
    failures: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.failures


def _load_golden(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _acl_list(doc: dict[str, Any]) -> list[str]:
    if "acl" in doc:
        return list(doc["acl"])
    if "acl_principals" in doc:
        return list(doc["acl_principals"])
    return []


def _index_corpus(rag: RagPipeline, corpus: list[dict[str, Any]]) -> None:
    for doc in corpus:
        kind = doc.get("kind", "doc")
        acl = _acl_list(doc)
        if kind == "transcript":
            rag.index_transcript(
                meeting_id=doc.get("meeting_id", doc["id"]),
                transcript_id=doc["id"],
                org_domain=doc["org_domain"],
                classification=doc.get("classification", "internal"),
                acl_principals=acl,
                title=doc.get("title", doc["id"]),
                segments=list(doc.get("segments") or []),
                body=doc.get("body"),
                write_class=doc.get("write_class", "domain"),
                series_id=doc.get("series_id"),
            )
        elif kind == "continuum":
            rag.index_continuum(
                item_id=doc["id"],
                org_domain=doc["org_domain"],
                classification=doc.get("classification", "internal"),
                acl_principals=acl,
                summary=doc["body"],
                write_class=doc["write_class"],
                meeting_id=doc.get("meeting_id", doc["id"]),
                series_id=doc.get("series_id"),
                open_item=bool(doc.get("open", False)),
            )
        else:
            rag.index_doc(
                doc_id=doc["id"],
                org_domain=doc["org_domain"],
                classification=doc.get("classification", "internal"),
                acl_principals=acl,
                title=doc.get("title", doc["id"]),
                body=doc["body"],
                write_class=doc.get("write_class", "domain"),
                project_id=doc.get("project_id"),
            )


def hit_at_k(retrieved: list[str], relevant: set[str], k: int) -> bool:
    return any(r in relevant for r in retrieved[:k])


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    got = set(retrieved[:k]) & relevant
    return len(got) / len(relevant)


def mrr_score(retrieved: list[str], relevant: set[str]) -> float:
    for i, r in enumerate(retrieved, start=1):
        if r in relevant:
            return 1.0 / i
    return 0.0


def ndcg_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """按 source 级二元相关性计算 nDCG，重复 chunk 不重复计分。"""

    seen: set[str] = set()
    ranked_unique: list[str] = []
    for doc_id in retrieved:
        if doc_id in seen:
            continue
        seen.add(doc_id)
        ranked_unique.append(doc_id)

    def dcg(ids: list[str]) -> float:
        return sum(
            (1.0 if doc_id in relevant else 0.0) / math.log2(i + 1)
            for i, doc_id in enumerate(ids[:k], start=1)
        )

    ideal = sum(1.0 / math.log2(i + 1) for i in range(1, min(len(relevant), k) + 1))
    if ideal <= 0:
        return 0.0
    return dcg(ranked_unique) / ideal


def _match_ids(hit_source_ids: list[str], hit_chunk_ids: list[str], relevant: set[str]) -> list[str]:
    """相关标注可以是 source_id 或 chunk_id 前缀。"""
    keys: list[str] = []
    for sid, cid in zip(hit_source_ids, hit_chunk_ids):
        key = sid
        for r in relevant:
            if r == cid or cid.startswith(r) or r in cid:
                key = r
                break
            if r == sid or sid.startswith(r) or r in sid:
                key = r
                break
        keys.append(key)
    return keys


def run_eval(golden_path: Path | None = None) -> EvalReport:
    path = golden_path or DEFAULT_GOLDEN
    data = _load_golden(path)
    # 默认阈值：黄金集可覆盖
    thresholds = {
        "hit_rate": 0.75,
        "recall_at_k": 0.65,
        "mrr": 0.50,
        "ndcg_at_k": 0.50,
        "faithfulness": 0.50,
    }
    thresholds.update(dict(data.get("thresholds") or {}))
    k = int(data.get("k", 5))
    rag = RagPipeline(BgeM3ShimProvider())
    _index_corpus(rag, list(data.get("corpus") or []))

    report = EvalReport(thresholds=thresholds)
    for case in data.get("cases") or []:
        cid = case["id"]
        relevant = set(
            case.get("relevant_ids")
            or case.get("expected_source_ids")
            or []
        )
        res = rag.retrieve(
            query=case["query"],
            user_id=case["user_id"],
            org_domains=list(case["org_domains"]),
            top_k=k,
            max_hops=int(case.get("max_hops", 3)),
            min_score=float(case.get("min_score", 0.0)),
        )
        source_ids = [h.source_id for h in res.hits]
        chunk_ids = [h.chunk_id for h in res.hits]
        # 黄金集以 source_id 标注相关性；同一来源的多个 chunk 只占一个排名位。
        ranked_keys = list(dict.fromkeys(_match_ids(source_ids, chunk_ids, relevant)))

        # ACL 负例：期望空召回（relevant 为空 / expect_empty）
        expect_empty = bool(case.get("expect_empty")) or (
            "expected_source_ids" in case and not case.get("expected_source_ids")
        )
        if expect_empty and not relevant:
            ok_empty = len(res.hits) == 0
            cr = CaseResult(
                case_id=cid,
                hit_at_k=ok_empty,
                recall_at_k=1.0 if ok_empty else 0.0,
                mrr=1.0 if ok_empty else 0.0,
                ndcg_at_k=1.0 if ok_empty else 0.0,
                faithfulness=1.0,
                retrieved_ids=chunk_ids,
                notes="acl_negative" if ok_empty else "acl_leak",
            )
            report.results.append(cr)
            if not ok_empty:
                report.failures.append(
                    f"{cid}: expected empty retrieval (ACL), got {source_ids}"
                )
            continue

        hit = hit_at_k(ranked_keys, relevant, k)
        rec = recall_at_k(ranked_keys, relevant, k)
        mrr = mrr_score(ranked_keys, relevant)
        ndcg = ndcg_at_k(ranked_keys, relevant, k)

        gold_answer = case.get("gold_answer")
        if gold_answer:
            faith, _, _ = score_faithfulness(gold_answer, res.hits)
        else:
            grounded = build_grounded_answer(query=case["query"], hits=res.hits)
            faith = grounded.faithfulness

        cr = CaseResult(
            case_id=cid,
            hit_at_k=hit,
            recall_at_k=round(rec, 4),
            mrr=round(mrr, 4),
            ndcg_at_k=round(ndcg, 4),
            faithfulness=round(faith, 4),
            retrieved_ids=chunk_ids,
        )
        report.results.append(cr)
        # must_hit 默认：有 expected/relevant 就要求命中
        must_hit = case.get("must_hit")
        if must_hit is None:
            must_hit = bool(relevant)
        if must_hit and not hit:
            report.failures.append(
                f"{cid}: miss relevant={sorted(relevant)} retrieved={source_ids}"
            )

    n = max(1, len([r for r in report.results if r.notes != "acl_leak"]))
    positives = [r for r in report.results if not r.notes.startswith("acl")]
    if not positives:
        positives = report.results

    def avg(attr: str) -> float:
        vals = [getattr(r, attr) for r in positives]
        if attr == "hit_at_k":
            return sum(1.0 if v else 0.0 for v in vals) / max(1, len(vals))
        return sum(float(v) for v in vals) / max(1, len(vals))

    report.metrics = {
        "hit_rate": round(avg("hit_at_k"), 4),
        "recall_at_k": round(avg("recall_at_k"), 4),
        "mrr": round(avg("mrr"), 4),
        "ndcg_at_k": round(avg("ndcg_at_k"), 4),
        "faithfulness": round(avg("faithfulness"), 4),
        "n_cases": float(len(report.results)),
        "k": float(k),
    }

    # 阈值检查
    mapping = {
        "hit_rate": "hit_rate",
        "recall_at_k": "recall_at_k",
        "mrr": "mrr",
        "ndcg_at_k": "ndcg_at_k",
        "faithfulness": "faithfulness",
    }
    for key, metric_key in mapping.items():
        if key in thresholds:
            if report.metrics.get(metric_key, 0.0) + 1e-9 < float(thresholds[key]):
                report.failures.append(
                    f"threshold {key}: {report.metrics.get(metric_key)} < {thresholds[key]}"
                )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="纪要君 RAG retrieval quality eval")
    parser.add_argument("--golden", type=Path, default=DEFAULT_GOLDEN)
    args = parser.parse_args(argv)

    if not args.golden.exists():
        print(f"FAIL golden missing: {args.golden}")
        return 2

    report = run_eval(args.golden)
    print("=== RAG Retrieval Quality ===")
    print(f"golden: {args.golden}")
    for r in report.results:
        flag = "OK" if (r.hit_at_k or r.notes == "acl_negative") else "MISS"
        print(
            f"  [{flag}] {r.case_id} hit={r.hit_at_k} recall={r.recall_at_k} "
            f"mrr={r.mrr} ndcg={r.ndcg_at_k} faith={r.faithfulness} "
            f"ids={r.retrieved_ids[:3]}"
        )
    print("metrics:", report.metrics)
    print("thresholds:", report.thresholds)
    if report.failures:
        print("FAILURES:")
        for f in report.failures:
            print(" -", f)
        print("RAG_EVAL_FAILED")
        return 1
    print("RAG_EVAL_PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
