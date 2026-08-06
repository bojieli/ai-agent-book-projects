"""Mock ASR — domain hotword profiles only (no global merge)."""

from __future__ import annotations

from dataclasses import dataclass

from app.knowledge.transcript import HOTWORD_PROFILES, TranscriptAdapter, TranscriptDocument


@dataclass
class AsrSegment:
    text: str
    start_ms: int
    end_ms: int
    confidence: float


class MockAsrService:
    """Simulates vendor-agnostic ASR adapter (03 §2.16)."""

    def __init__(self) -> None:
        self.adapter = TranscriptAdapter()
        self.last_profile_id: str | None = None

    def transcribe(
        self,
        *,
        meeting_id: str,
        org_domains: list[str],
        audio_object_key: str,
        raw_utterances: list[str],
    ) -> TranscriptDocument:
        domain = org_domains[0] if org_domains else "eng"
        profile_id = f"{domain}_default"
        if profile_id not in HOTWORD_PROFILES:
            profile_id = "eng_default"
        profile = HOTWORD_PROFILES[profile_id]
        self.last_profile_id = profile_id

        # Apply hotword bias: if a hotword appears as near-homophone stub, correct it
        corrected = []
        for u in raw_utterances:
            t = u
            # demo corrections
            t = t.replace("会度", "灰度").replace("回滚兰", "回滚")
            for term in profile.terms:
                if term.lower() in t.lower() or term in t:
                    pass
            corrected.append(t)

        doc = self.adapter.ingest_mock(meeting_id, org_domains, corrected)
        # stamp audio key
        doc.object_key = audio_object_key
        doc.hotword_profile_id = profile_id
        return doc

    @staticmethod
    def assert_no_all_domain_hotword_dump(profile_ids: list[str]) -> None:
        if "ALL" in profile_ids or "global" in profile_ids:
            raise ValueError("forbid global hotword hard-merge")
