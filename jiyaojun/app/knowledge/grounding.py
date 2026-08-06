"""Answer grounding — Faithfulness 工程近似（与 rag.GroundedAnswer 互补）。

rag.GroundedAnswer：检索→摘录式回答
本模块：对任意答案做句子级 faithfulness / claim 支撑检测
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from app.knowledge.embedding import _tokenize_zh
from app.knowledge.rag import RagHit


@dataclass
class GroundedClaim:
    claim: str
    supported: bool
    evidence_chunk_ids: list[str] = field(default_factory=list)
    overlap_score: float = 0.0


@dataclass
class FaithfulnessReport:
    """答案相对召回上下文的忠实度报告。"""

    faithfulness: float
    claims: list[GroundedClaim]
    unsupported: list[str] = field(default_factory=list)


# 兼容旧名（Dialog / plane 曾用 GroundedAnswer 指 faithfulness 结果）
@dataclass
class GroundedAnswer:
    answer: str
    citations: list[dict[str, Any]]
    faithfulness: float
    claims: list[GroundedClaim]
    unsupported: list[str] = field(default_factory=list)
    empty_reason: str | None = None

    @property
    def abstained(self) -> bool:
        return self.empty_reason is not None


def _claim_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[。！？；!?;\n])\s*", text.strip())
    return [p.strip() for p in parts if p and len(p.strip()) >= 4]


def _overlap(a_tokens: set[str], b_tokens: set[str]) -> float:
    if not a_tokens or not b_tokens:
        return 0.0
    inter = len(a_tokens & b_tokens)
    return inter / max(1, len(a_tokens))


def score_faithfulness(
    answer: str,
    hits: Iterable[RagHit],
    *,
    min_overlap: float = 0.18,
) -> tuple[float, list[GroundedClaim], list[str]]:
    hit_list = list(hits)
    if not answer.strip():
        return 0.0, [], ["empty_answer"]
    if not hit_list:
        claims = [
            GroundedClaim(claim=c, supported=False, overlap_score=0.0)
            for c in _claim_sentences(answer) or [answer.strip()]
        ]
        return 0.0, claims, [c.claim for c in claims]

    corpus_toks = [(h, set(_tokenize_zh(h.text))) for h in hit_list]
    claims: list[GroundedClaim] = []
    unsupported: list[str] = []
    for sent in _claim_sentences(answer) or [answer.strip()]:
        stoks = set(_tokenize_zh(sent))
        best_ids: list[str] = []
        best = 0.0
        for h, toks in corpus_toks:
            sc = _overlap(stoks, toks)
            if sc > best:
                best = sc
                best_ids = [h.chunk_id]
            elif sc == best and sc >= min_overlap:
                best_ids.append(h.chunk_id)
        supported = best >= min_overlap
        claims.append(
            GroundedClaim(
                claim=sent,
                supported=supported,
                evidence_chunk_ids=best_ids if supported else [],
                overlap_score=round(best, 4),
            )
        )
        if not supported:
            unsupported.append(sent)

    faith = sum(1 for c in claims if c.supported) / max(1, len(claims))
    return round(faith, 4), claims, unsupported


def build_grounded_answer(
    *,
    query: str,
    hits: list[RagHit],
    max_evidence: int = 3,
) -> GroundedAnswer:
    if not hits:
        return GroundedAnswer(
            answer="未在可访问知识库中找到相关依据，请换个问法或确认权限。",
            citations=[],
            faithfulness=1.0,
            claims=[],
            unsupported=[],
            empty_reason="no_hits",
        )

    top = hits[:max_evidence]
    lines = [f"针对「{query}」，依据如下："]
    citations: list[dict[str, Any]] = []
    for i, h in enumerate(top, 1):
        excerpt = h.text.strip().replace("\n", " ")
        if len(excerpt) > 220:
            excerpt = excerpt[:220] + "…"
        lines.append(f"{i}. {excerpt}")
        citations.append(
            {
                **h.citation,
                "score": h.score,
                "corpus": h.corpus,
                "source_id": h.source_id,
                "text_preview": excerpt[:120],
            }
        )
    answer = "\n".join(lines)
    faith, claims, unsupported = score_faithfulness(answer, top)
    return GroundedAnswer(
        answer=answer,
        citations=citations,
        faithfulness=faith,
        claims=claims,
        unsupported=unsupported,
        empty_reason=None,
    )
