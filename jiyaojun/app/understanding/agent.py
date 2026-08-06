"""Understanding agent — domain glossary + unknown terms; wrong domain blocks embed."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.knowledge.glossary import DEFAULT_GLOSSARY, GlossaryStore
from app.knowledge.transcript import TranscriptAdapter, TranscriptDocument


@dataclass
class UnderstandingResult:
    quality: str  # ok | low | blocked
    unknown_terms: list[str] = field(default_factory=list)
    applied_glosses: list[dict[str, str]] = field(default_factory=list)
    wrong_domain_hits: list[str] = field(default_factory=list)
    blocks_embed: bool = False
    blocks_decision: bool = False


class UnderstandingAgent:
    def __init__(self, glossary: GlossaryStore | None = None) -> None:
        self.glossary = glossary or GlossaryStore()
        self.transcript = TranscriptAdapter()

    def understand(
        self,
        *,
        meeting_id: str,
        org_domains: list[str],
        segments: list[str],
        min_known_ratio: float = 0.3,
    ) -> tuple[TranscriptDocument, UnderstandingResult]:
        doc = self.transcript.ingest_mock(meeting_id, org_domains, segments)
        text = " ".join(segments)
        known = 0
        applied = []
        wrong = []
        terms = {e.term for e in DEFAULT_GLOSSARY if e.term in text}
        for term in terms:
            in_scope = [e for e in DEFAULT_GLOSSARY if e.term == term and e.org_domain in org_domains]
            out_scope = [
                e for e in DEFAULT_GLOSSARY if e.term == term and e.org_domain not in org_domains
            ]
            if in_scope:
                known += 1
                for e in in_scope:
                    applied.append(
                        {"term": e.term, "org_domain": e.org_domain, "gloss": e.gloss}
                    )
            elif out_scope:
                wrong.append(f"{term}@{out_scope[0].org_domain}")

        # unknown: tokens that look like jargon but not in scopes
        unknown: list[str] = []
        for token in ["WIP", "HC", "PSI", "canary"]:
            if token in text or token.lower() in text.lower():
                # eng meeting saying HC is unknown/wrong
                if token == "HC" and "hr" not in org_domains:
                    unknown.append(token)
                elif token == "PSI" and "risk" not in org_domains:
                    unknown.append(token)

        blocks = bool(wrong) or (len(unknown) >= 2)
        low = len(segments) == 0 or (known == 0 and len(text) < 8)
        quality = "blocked" if blocks else ("low" if low else "ok")
        return doc, UnderstandingResult(
            quality=quality,
            unknown_terms=unknown,
            applied_glosses=applied,
            wrong_domain_hits=wrong,
            blocks_embed=blocks or quality == "low",
            blocks_decision=blocks or quality != "ok",
        )
