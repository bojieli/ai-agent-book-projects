"""Knowledge plane: RAG-backed Docs + Continuum + Transcript（ACL-first Hybrid）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.knowledge.chunking import ChunkConfig
from app.knowledge.grounding import GroundedAnswer, build_grounded_answer
from app.knowledge.rag import RagPipeline, RagSearchResult
from app.knowledge.series_bridge import SeriesContinuumBridge
from app.knowledge.transcript import TranscriptDocument


@dataclass
class DocChunk:
    id: str
    org_domain: str
    classification: str
    acl_principals: list[str]
    text: str
    write_class: str = "domain"
    title: str = ""


@dataclass
class ContinuumItem:
    id: str
    org_domain: str
    classification: str
    write_class: str
    acl_principals: list[str]
    summary: str
    open: bool = False
    meeting_id: str = ""
    series_id: str | None = None


@dataclass
class RetrievalHit:
    corpus: str
    id: str
    span: str
    text: str
    score: float = 0.0
    vector_ref: str = ""
    speaker: str = ""
    start_ms: str = ""
    section: str = ""


@dataclass
class WriteDecision:
    write_class: str
    accepted: bool
    rejected_reason: str | None = None
    index_alias: str | None = None


class KnowledgePlane:
    def __init__(
        self,
        rag: RagPipeline | None = None,
        chunk_config: ChunkConfig | None = None,
    ) -> None:
        self.rag = rag or RagPipeline(chunk_config=chunk_config)
        self.docs: list[DocChunk] = []
        self.continuum: list[ContinuumItem] = []
        self.transcripts: list[TranscriptDocument] = []
        self.receipts: list[WriteDecision] = []
        self.last_search: RagSearchResult | None = None
        self.last_answer: GroundedAnswer | None = None
        self.series_bridge = SeriesContinuumBridge(self)

    def seed_demo(self) -> None:
        self.docs = [
            DocChunk(
                "doc_api_timeout",
                "eng",
                "internal",
                ["u_dev_a", "u_pm"],
                (
                    "## 接口超时规范\n"
                    "### 超时与重试\n"
                    "接口超时与重试约定：超时 3s，最多重试 2 次，半成功需补偿任务。\n"
                    "### 网关容量\n"
                    "网关容量评估未完成前，禁止扩大支付切流比例。\n"
                    "### 灰度\n"
                    "灰度发布采用 canary：先 1% 观察错误率，再放量到 10%。"
                ),
                title="接口超时规范",
            ),
            DocChunk(
                "doc_policy_fraud",
                "risk",
                "confidential",
                ["u_risk_pm"],
                (
                    "【策略上线说明】\n"
                    "一、Shadow 观察\n"
                    "策略上线须先 Shadow，禁止未确认生产热切换。\n"
                    "二、误杀治理\n"
                    "误杀率超过阈值必须回滚，并保留 PSI 监控。"
                ),
                title="策略上线说明",
                write_class="domain",
            ),
        ]
        self.continuum = [
            ContinuumItem(
                "mtg_r5_prev_blocker",
                "eng",
                "internal",
                "wide",
                ["u_dev_a", "u_pm"],
                "网关容量未关闭，支付切流红灯。",
                open=True,
                meeting_id="mtg_r5_prev",
                series_id="series_pay",
            ),
            ContinuumItem(
                "mtg_h5_sealed",
                "hr",
                "critical",
                "sealed",
                ["u_hrbp"],
                "组织调整分析摘要（密封）。",
                open=True,
                meeting_id="mtg_h5_prev",
            ),
        ]
        self.reindex_all()
        # 将 demo Continuum open 项同步到 SeriesStore（跨会 briefing 统一语义）
        from app.knowledge.series import SeriesOpenItem

        for c in self.continuum:
            if c.open and c.series_id:
                self.series_bridge.series.add_open(
                    c.series_id,
                    SeriesOpenItem(
                        item_id=c.id,
                        title=c.summary,
                        source_meeting_id=c.meeting_id,
                        org_domain=c.org_domain,
                        classification=c.classification,
                        write_class=c.write_class,
                        acl_principals=list(c.acl_principals),
                    ),
                )
        # 示例转写：带说话人与时间戳
        self.ingest_transcript(
            TranscriptDocument(
                transcript_document_id="td_mtg_demo",
                meeting_id="mtg_demo_r5",
                object_key="s3://mock/mtg_demo_r5/transcript.json",
                hotword_profile_id="eng_default",
                segments=[
                    {
                        "idx": 0,
                        "speaker": "PM",
                        "text": "今天先对齐接口超时和重试策略。",
                        "start_ms": 0,
                        "end_ms": 4000,
                        "section": "议题",
                    },
                    {
                        "idx": 1,
                        "speaker": "DEV",
                        "text": "超时建议保持 3 秒，最多重试两次，半成功走补偿。",
                        "start_ms": 4500,
                        "end_ms": 12000,
                        "section": "讨论",
                    },
                    {
                        "idx": 2,
                        "speaker": "PM",
                        "text": "决议：按规范执行，网关容量未完成前不扩切流。",
                        "start_ms": 13000,
                        "end_ms": 20000,
                        "section": "决议",
                    },
                ],
            ),
            org_domain="eng",
            classification="internal",
            acl_principals=["u_dev_a", "u_pm"],
            title="支付 R5 对齐会",
            series_id="series_pay",
        )

    def reindex_all(self) -> None:
        self.rag = RagPipeline(self.rag.index.embedder, self.rag.chunk_config)
        for d in self.docs:
            self.rag.index_doc(
                doc_id=d.id,
                org_domain=d.org_domain,
                classification=d.classification,
                acl_principals=d.acl_principals,
                title=d.title or d.id,
                body=d.text,
                write_class=d.write_class,
            )
        for c in self.continuum:
            self.rag.index_continuum(
                item_id=c.id,
                org_domain=c.org_domain,
                classification=c.classification,
                acl_principals=c.acl_principals,
                summary=c.summary,
                write_class=c.write_class,
                meeting_id=c.meeting_id or c.id,
                series_id=c.series_id,
                open_item=c.open,
            )
        for t in self.transcripts:
            # org/acl 存在 meta 侧车；缺失时跳过（seed 走 ingest）
            meta = getattr(t, "_index_meta", None) or {}
            if not meta:
                continue
            self.rag.index_transcript(
                meeting_id=t.meeting_id,
                org_domain=meta["org_domain"],
                classification=meta.get("classification", "internal"),
                acl_principals=list(meta["acl_principals"]),
                title=meta.get("title", t.meeting_id),
                segments=t.segments,
                write_class=meta.get("write_class", "domain"),
                series_id=meta.get("series_id"),
            )

    def ingest_transcript(
        self,
        doc: TranscriptDocument,
        *,
        org_domain: str,
        classification: str,
        acl_principals: list[str],
        title: str,
        write_class: str = "domain",
        series_id: str | None = None,
    ) -> list[Any]:
        """转写 → 分块 → 索引（ingestion → chunk → index）。"""
        meta = {
            "org_domain": org_domain,
            "classification": classification,
            "acl_principals": acl_principals,
            "title": title,
            "write_class": write_class,
            "series_id": series_id,
        }
        setattr(doc, "_index_meta", meta)
        # replace same meeting
        self.transcripts = [t for t in self.transcripts if t.meeting_id != doc.meeting_id]
        self.transcripts.append(doc)
        return self.rag.index_transcript(
            meeting_id=doc.meeting_id,
            org_domain=org_domain,
            classification=classification,
            acl_principals=acl_principals,
            title=title,
            segments=doc.segments,
            write_class=write_class,
            series_id=series_id,
        )

    def retrieve(
        self,
        *,
        user_id: str,
        org_domains: list[str],
        query: str,
        max_hops: int = 3,
        budget_hops_used: int = 0,
    ) -> tuple[list[RetrievalHit], int]:
        remaining = max(1, max_hops - budget_hops_used)
        result = self.rag.retrieve(
            query=query,
            user_id=user_id,
            org_domains=org_domains,
            max_hops=remaining,
        )
        self.last_search = result
        hits = [
            RetrievalHit(
                corpus=h.corpus,
                id=h.source_id,
                span=h.citation.get("span", h.chunk_id),
                text=h.text,
                score=h.score,
                vector_ref=h.citation.get("vector_ref", ""),
                speaker=h.citation.get("speaker", ""),
                start_ms=h.citation.get("start_ms", ""),
                section=h.citation.get("section", ""),
            )
            for h in result.hits
        ]
        return hits, result.hops

    def answer(
        self,
        *,
        user_id: str,
        org_domains: list[str],
        query: str,
        max_hops: int = 3,
    ) -> GroundedAnswer:
        """检索 + 依据 grounding（含 faithfulness）。"""
        self.retrieve(
            user_id=user_id,
            org_domains=org_domains,
            query=query,
            max_hops=max_hops,
        )
        hits = self.last_search.hits if self.last_search else []
        ans = build_grounded_answer(query=query, hits=hits)
        self.last_answer = ans
        return ans

    def decide_continuum_write(
        self,
        *,
        classification: str,
        requested_write_class: str,
    ) -> WriteDecision:
        write_class = requested_write_class
        if classification == "critical" and write_class == "wide":
            dec = WriteDecision(
                write_class=write_class,
                accepted=False,
                rejected_reason="critical_cannot_wide",
            )
            self.receipts.append(dec)
            return dec
        if classification == "critical" and write_class not in {"sealed", "none"}:
            dec = WriteDecision(
                write_class=write_class,
                accepted=False,
                rejected_reason="critical_requires_sealed_or_none",
            )
            self.receipts.append(dec)
            return dec
        alias = {
            "wide": "continuum_wide",
            "domain": "continuum_domain",
            "sealed": "continuum_sealed",
            "none": None,
        }[write_class]
        dec = WriteDecision(
            write_class=write_class,
            accepted=write_class != "none",
            index_alias=alias,
            rejected_reason=None if write_class != "none" else "write_class_none",
        )
        self.receipts.append(dec)
        return dec

    def write_continuum_and_index(
        self,
        item: ContinuumItem,
        *,
        classification: str,
    ) -> WriteDecision:
        dec = self.decide_continuum_write(
            classification=classification,
            requested_write_class=item.write_class,
        )
        if not dec.accepted:
            return dec
        self.continuum.append(item)
        self.rag.index_continuum(
            item_id=item.id,
            org_domain=item.org_domain,
            classification=item.classification,
            acl_principals=item.acl_principals,
            summary=item.summary,
            write_class=item.write_class,
            meeting_id=item.meeting_id or item.id,
            series_id=item.series_id,
            open_item=item.open,
        )
        return dec

    def close_continuum_item(self, item_id: str) -> bool:
        """将 Continuum 项标为已关闭，并更新向量索引 open 元数据。"""
        for item in self.continuum:
            if item.id != item_id:
                continue
            item.open = False
            self.rag.index_continuum(
                item_id=item.id,
                org_domain=item.org_domain,
                classification=item.classification,
                acl_principals=item.acl_principals,
                summary=item.summary,
                write_class=item.write_class,
                meeting_id=item.meeting_id or item.id,
                series_id=item.series_id,
                open_item=False,
            )
            return True
        return False
