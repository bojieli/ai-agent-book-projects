"""TranscriptDocument adapter mock + domain-scoped hotwords (03 §2.16)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class HotwordProfile:
    profile_id: str
    org_domains: list[str]
    terms: list[str]


@dataclass
class TranscriptDocument:
    transcript_document_id: str
    meeting_id: str
    object_key: str
    hotword_profile_id: str
    segments: list[dict[str, Any]] = field(default_factory=list)

    @property
    def segment_count(self) -> int:
        return len(self.segments)


# Per-domain profiles — NEVER merge into one global forced list
HOTWORD_PROFILES = {
    "eng_default": HotwordProfile("eng_default", ["eng"], ["灰度", "回滚", "canary", "WIP"]),
    "business_default": HotwordProfile("business_default", ["business"], ["灰度", "漏斗", "客群"]),
    "hr_default": HotwordProfile("hr_default", ["hr"], ["校准", "HC", "编制"]),
    "risk_default": HotwordProfile("risk_default", ["risk"], ["Shadow", "误杀", "PSI"]),
    "compliance_default": HotwordProfile(
        "compliance_default", ["compliance"], ["整改项", "口径", "迎检"]
    ),
}


class TranscriptAdapter:
    def __init__(self) -> None:
        self._docs: dict[str, TranscriptDocument] = {}

    def ingest_mock(
        self,
        meeting_id: str,
        org_domains: list[str],
        text_segments: list[str] | list[dict[str, Any]],
        *,
        transcript_document_id: str | None = None,
        object_key: str | None = None,
    ) -> TranscriptDocument:
        """支持纯字符串或带 speaker/时间戳的 dict 片段。"""
        domain = org_domains[0] if org_domains else "eng"
        profile_id = f"{domain}_default"
        if profile_id not in HOTWORD_PROFILES:
            profile_id = "eng_default"
        # isolation: only inject this profile's terms
        profile = HOTWORD_PROFILES[profile_id]
        segments: list[dict[str, Any]] = []
        for i, t in enumerate(text_segments):
            if isinstance(t, dict):
                seg = {
                    "idx": t.get("idx", i),
                    "text": str(t.get("text", "")),
                    "start_ms": t.get("start_ms", i * 1000),
                    "end_ms": t.get("end_ms", i * 1000 + 800),
                }
                if t.get("speaker"):
                    seg["speaker"] = t["speaker"]
                if t.get("section"):
                    seg["section"] = t["section"]
                segments.append(seg)
            else:
                segments.append(
                    {
                        "idx": i,
                        "text": str(t),
                        "start_ms": i * 1000,
                        "end_ms": i * 1000 + 800,
                    }
                )
        td_id = transcript_document_id or f"td_{meeting_id}"
        doc = TranscriptDocument(
            transcript_document_id=td_id,
            meeting_id=meeting_id,
            object_key=object_key or f"s3://mock/{meeting_id}/transcript.json",
            hotword_profile_id=profile.profile_id,
            segments=segments,
        )
        self._docs[doc.transcript_document_id] = doc
        return doc

    def from_callback(
        self,
        *,
        meeting_id: str,
        org_domains: list[str],
        transcript_document_id: str,
        object_key: str,
        segments: list[dict[str, Any]] | list[str],
    ) -> TranscriptDocument:
        """内部回调 transcript.ready → 可索引的 TranscriptDocument。"""
        return self.ingest_mock(
            meeting_id,
            org_domains,
            segments,
            transcript_document_id=transcript_document_id,
            object_key=object_key,
        )

    @staticmethod
    def forbid_global_hotword_merge(profiles: list[HotwordProfile]) -> bool:
        """Return True if caller attempts illegal all-domain hard-merge."""
        domains = set()
        for p in profiles:
            domains.update(p.org_domains)
        return len(domains) > 1 and len(profiles) == 1 and profiles[0].profile_id == "ALL"
