"""Dialog plane — briefing + grounded Q&A via Knowledge（ACL first）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.knowledge import KnowledgePlane
from app.knowledge.grounding import GroundedAnswer


@dataclass
class Briefing:
    hits: list[dict[str, Any]]
    retrieve_hops: int
    series_open_count: int = 0
    series_open_items: list[dict[str, Any]] | None = None


@dataclass
class DialogReply:
    """会前/会中问答：带 citation 与 faithfulness。"""

    text: str
    citations: list[dict[str, Any]] = field(default_factory=list)
    faithfulness: float = 0.0
    retrieve_hops: int = 0
    briefing: Briefing | None = None


class DialogPlane:
    def __init__(self, knowledge: KnowledgePlane) -> None:
        self.knowledge = knowledge

    def briefing(
        self,
        *,
        user_id: str,
        org_domains: list[str],
        query: str,
        max_hops: int = 3,
        series_id: str | None = None,
        classification: str = "internal",
        continuum_write_class: str = "wide",
    ) -> Briefing:
        hits, hops = self.knowledge.retrieve(
            user_id=user_id,
            org_domains=org_domains,
            query=query,
            max_hops=max_hops,
        )
        series_open: list[dict[str, Any]] = []
        if series_id and hasattr(self.knowledge, "series_bridge"):
            bridge = self.knowledge.series_bridge
            # `none` 禁止任何 Continuum 索引；其余使用场景级 classification/write_class
            if continuum_write_class != "none":
                bridge.sync_open_items_to_continuum(
                    series_id,
                    org_domain=org_domains[0],
                    classification=classification,
                    write_class=continuum_write_class,
                    acl_principals=[user_id],
                )
                hits2, hops2 = self.knowledge.retrieve(
                    user_id=user_id,
                    org_domains=org_domains,
                    query=f"{query} 阻塞 open",
                    max_hops=max_hops,
                )
                if hops2 > hops:
                    hops = hops2
                seen = {h.id for h in hits}
                for h in hits2:
                    if h.id not in seen:
                        hits.append(h)
                        seen.add(h.id)
            series_open = bridge.briefing_open_items(
                series_id,
                user_id=user_id,
                org_domains=org_domains,
            )
        return Briefing(
            hits=[h.__dict__ for h in hits],
            retrieve_hops=hops,
            series_open_count=len(series_open),
            series_open_items=series_open or None,
        )

    def ask(
        self,
        *,
        user_id: str,
        org_domains: list[str],
        query: str,
        max_hops: int = 3,
    ) -> DialogReply:
        """检索 → grounding 回答（可用）。"""
        ans: GroundedAnswer = self.knowledge.answer(
            user_id=user_id,
            org_domains=org_domains,
            query=query,
            max_hops=max_hops,
        )
        hops = self.knowledge.last_search.hops if self.knowledge.last_search else 0
        brief = Briefing(
            hits=[
                {
                    "corpus": c.get("corpus"),
                    "id": c.get("source_id") or c.get("id"),
                    "span": c.get("span"),
                    "text": c.get("text_preview"),
                    "score": c.get("score", 0.0),
                    "vector_ref": c.get("vector_ref", ""),
                }
                for c in ans.citations
            ],
            retrieve_hops=hops,
        )
        return DialogReply(
            text=ans.answer,
            citations=ans.citations,
            faithfulness=ans.faithfulness,
            retrieve_hops=hops,
            briefing=brief,
        )
