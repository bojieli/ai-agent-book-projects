"""Meeting-aware chunking for Knowledge Plane RAG.

- Speaker-turn boundaries for transcripts (never split mid-turn).
- Heading/paragraph split + overlap windows for docs.
- Metadata: speaker / timestamps / section for citation & light rerank.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Sequence


_HEADING_RE = re.compile(
    r"^(#{1,3}\s+\S+|[一二三四五六七八九十]+[、.．]\s*\S+|"
    r"第[一二三四五六七八九十\d]+[章节条]\s*\S+|决议|待办|行动项)"
)
_SPEAKER_LINE_RE = re.compile(
    r"^(?:(?P<room>[^#\n]+)#)?(?P<speaker>说话人\d+|Speaker\s*\d+|[\u4e00-\u9fffA-Za-z_.]{1,24})"
    r"(?:\((?P<ts>\d{1,2}:\d{2}:\d{2})\))?\s*[:：]\s*(?P<body>.*)$"
)


class ContentKind(str, Enum):
    PLAIN_DOC = "plain_doc"
    TRANSCRIPT = "transcript"


class ChunkConfig:
    """Chunk size knobs — accepts max_chars or legacy chunk_size/chunk_overlap."""

    def __init__(
        self,
        max_chars: int | None = None,
        overlap_chars: int | None = None,
        min_chars: int = 40,
        *,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> None:
        self.max_chars = int(
            chunk_size if chunk_size is not None else (max_chars if max_chars is not None else 700)
        )
        self.overlap_chars = int(
            chunk_overlap
            if chunk_overlap is not None
            else (overlap_chars if overlap_chars is not None else 80)
        )
        self.min_chars = int(min_chars)

    @property
    def chunk_size(self) -> int:
        return self.max_chars

    @property
    def chunk_overlap(self) -> int:
        return self.overlap_chars

    @classmethod
    def from_env(cls) -> ChunkConfig:
        return cls(
            max_chars=int(os.getenv("JIYAOJUN_CHUNK_MAX_CHARS", "700")),
            overlap_chars=int(os.getenv("JIYAOJUN_CHUNK_OVERLAP", "80")),
            min_chars=int(os.getenv("JIYAOJUN_CHUNK_MIN_CHARS", "40")),
        )


ChunkingConfig = ChunkConfig


@dataclass
class TextChunk:
    index: int
    body: str
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def text(self) -> str:
        return self.body

    @property
    def speaker(self) -> str:
        return str(self.meta.get("speaker") or "")

    @property
    def speakers(self) -> list[str]:
        sp = self.meta.get("speakers")
        if isinstance(sp, list):
            return [str(x) for x in sp]
        s = self.speaker
        return [s] if s else []

    @property
    def section(self) -> str:
        return str(self.meta.get("section") or "")

    @property
    def start_ms(self) -> int | None:
        v = self.meta.get("start_ms")
        return int(v) if v is not None else None

    @property
    def end_ms(self) -> int | None:
        v = self.meta.get("end_ms")
        return int(v) if v is not None else None

    @property
    def kind(self) -> str:
        return str(self.meta.get("kind") or "doc")


def detect_content_kind(text: str) -> ContentKind:
    lines = [ln for ln in (text or "").splitlines() if ln.strip()]
    if not lines:
        return ContentKind.PLAIN_DOC
    heading_hits = sum(
        1
        for ln in lines
        if ln.strip().startswith("#") or _HEADING_RE.match(ln.strip())
    )
    hits = sum(1 for ln in lines if _SPEAKER_LINE_RE.match(ln.strip()))
    # Docs with markdown/numbered headings stay PLAIN even if a few dialogue lines appear
    if heading_hits >= 1 and hits < max(3, int(0.6 * len(lines))):
        return ContentKind.PLAIN_DOC
    if hits >= max(2, len(lines) // 3):
        return ContentKind.TRANSCRIPT
    return ContentKind.PLAIN_DOC


def parse_speaker_segments(text: str) -> list[dict[str, Any]]:
    segs: list[dict[str, Any]] = []
    for i, line in enumerate((text or "").splitlines()):
        line = line.strip()
        if not line:
            continue
        m = _SPEAKER_LINE_RE.match(line)
        if m:
            segs.append(
                {
                    "idx": i,
                    "speaker": m.group("speaker"),
                    "ts": m.group("ts") or "",
                    "text": (m.group("body") or "").strip(),
                    "start_ms": i * 1000,
                    "end_ms": i * 1000 + 800,
                }
            )
        else:
            segs.append(
                {
                    "idx": i,
                    "speaker": "unknown",
                    "ts": "",
                    "text": line,
                    "start_ms": i * 1000,
                    "end_ms": i * 1000 + 800,
                }
            )
    return segs


def _soft_windows(text: str, *, max_chars: int, overlap: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    out: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + max_chars)
        if end < n:
            window = text[start:end]
            br = max(
                window.rfind("\n"),
                window.rfind("。"),
                window.rfind("；"),
                window.rfind(". "),
            )
            if br >= max_chars // 3:
                end = start + br + 1
        piece = text[start:end].strip()
        if piece:
            out.append(piece)
        if end >= n:
            break
        start = max(0, end - overlap)
    return out


def _chunk_plain_document(raw: str, cfg: ChunkConfig) -> list[TextChunk]:
    blocks: list[tuple[str, str]] = []
    buf: list[str] = []
    section = ""
    for line in raw.splitlines():
        s = line.strip()
        if _HEADING_RE.match(s):
            if buf:
                blocks.append((section, "\n".join(buf).strip()))
                buf = []
            section = s.lstrip("#").strip()
            buf.append(s)
        else:
            buf.append(line)
    if buf:
        blocks.append((section, "\n".join(buf).strip()))
    if not blocks:
        blocks = [("", raw)]

    # Keep distinct heading sections separate (better retrieval for "决议/灰度/超时")
    merged: list[tuple[str, str]] = []
    acc_sec, acc = "", ""
    for sec, b in blocks:
        if not acc:
            acc_sec, acc = sec, b
            continue
        same_section = (sec == acc_sec) or not sec
        if same_section and len(acc) + 1 + len(b) <= cfg.max_chars:
            acc = f"{acc}\n{b}"
            if sec and not acc_sec:
                acc_sec = sec
        else:
            merged.append((acc_sec, acc))
            acc_sec, acc = sec, b
    if acc:
        merged.append((acc_sec, acc))

    chunks: list[TextChunk] = []
    idx = 0
    for sec, block in merged:
        for piece in _soft_windows(
            block, max_chars=cfg.max_chars, overlap=cfg.overlap_chars
        ):
            if len(piece) < cfg.min_chars and chunks:
                prev = chunks[-1]
                chunks[-1] = TextChunk(
                    index=prev.index,
                    body=f"{prev.body}\n{piece}".strip(),
                    meta={**prev.meta, "merged_tail": True},
                )
                continue
            chunks.append(
                TextChunk(
                    index=idx,
                    body=piece,
                    meta={"kind": ContentKind.PLAIN_DOC.value, "section": sec, "part": idx},
                )
            )
            idx += 1
    return chunks


def _chunk_transcript_segments(
    segments: Sequence[dict[str, Any]], cfg: ChunkConfig
) -> list[TextChunk]:
    chunks: list[TextChunk] = []
    buf_lines: list[str] = []
    speakers: set[str] = set()
    primary = ""
    start_ms: int | None = None
    end_ms: int | None = None
    section = "discussion"
    part = 0

    def flush() -> None:
        nonlocal buf_lines, speakers, primary, start_ms, end_ms, part
        if not buf_lines:
            return
        body = "\n".join(buf_lines).strip()
        if not body:
            buf_lines, speakers, primary, start_ms, end_ms = [], set(), "", None, None
            return
        sp_list = sorted(speakers)
        chunks.append(
            TextChunk(
                index=part,
                body=body,
                meta={
                    "kind": ContentKind.TRANSCRIPT.value,
                    "speaker": primary or (sp_list[0] if sp_list else ""),
                    "speakers": sp_list,
                    "start_ms": start_ms or 0,
                    "end_ms": end_ms or 0,
                    "section": section,
                    "part": part,
                },
            )
        )
        part += 1
        buf_lines, speakers, primary, start_ms, end_ms = [], set(), "", None, None

    for seg in segments:
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        speaker = str(seg.get("speaker") or "unknown")
        ts = seg.get("ts") or ""
        line = f"{speaker}" + (f"({ts})" if ts else "") + f"：{text}"
        if any(k in text for k in ("决议", "决定", "同意")):
            section = "决议"
        elif any(k in text for k in ("待办", "行动项", "跟进", "负责人")):
            section = "待办"

        tentative = ("\n".join(buf_lines + [line])).strip()
        if buf_lines and len(tentative) > cfg.max_chars:
            flush()
            tentative = line
        buf_lines.append(line)
        speakers.add(speaker)
        if not primary:
            primary = speaker
        sm = int(seg.get("start_ms") or 0)
        em = int(seg.get("end_ms") or sm)
        start_ms = sm if start_ms is None else min(start_ms, sm)
        end_ms = em if end_ms is None else max(end_ms, em)
        if len(tentative) >= cfg.max_chars:
            flush()
    flush()
    return chunks


def chunk_by_kind(
    *,
    kind: ContentKind,
    text: str = "",
    segments: Sequence[dict[str, Any]] | None = None,
    config: ChunkConfig | None = None,
) -> list[TextChunk]:
    cfg = config or ChunkConfig()
    if kind == ContentKind.TRANSCRIPT:
        segs = list(segments or [])
        if not segs and text.strip():
            segs = parse_speaker_segments(text)
        if not segs and text.strip():
            segs = [
                {
                    "speaker": "unknown",
                    "text": text.strip(),
                    "start_ms": 0,
                    "end_ms": 0,
                }
            ]
        return _chunk_transcript_segments(segs, cfg)
    return _chunk_plain_document((text or "").strip(), cfg) if (text or "").strip() else []


def chunk_document(
    *,
    body: str | None = None,
    segments: Sequence[dict[str, Any]] | None = None,
    cfg: ChunkConfig | None = None,
    text: str | None = None,
    **_legacy: Any,
) -> list[TextChunk]:
    raw = body if body is not None else (text or "")
    if segments:
        return chunk_by_kind(
            kind=ContentKind.TRANSCRIPT, text=raw, segments=segments, config=cfg
        )
    kind = detect_content_kind(raw)
    return chunk_by_kind(kind=kind, text=raw, config=cfg)


def chunk_transcript(
    segments: Sequence[dict[str, Any]],
    *,
    cfg: ChunkConfig | None = None,
    **_legacy: Any,
) -> list[TextChunk]:
    return chunk_by_kind(
        kind=ContentKind.TRANSCRIPT, segments=segments, config=cfg
    )



def chunk_text(text: str, cfg: ChunkConfig | None = None) -> list[TextChunk]:
    """纯文本便捷入口（兼容测试 / KnowledgePlane）。"""
    return chunk_document(body=text, cfg=cfg)


def chunk_segments(
    segments: Sequence[dict[str, Any]],
    cfg: ChunkConfig | None = None,
) -> list[TextChunk]:
    return chunk_transcript(segments, cfg=cfg)


def parse_plain_transcript(text: str) -> list[dict[str, Any]]:
    """Parse speaker-labeled lines; returns dicts (`.get` friendly for tests)."""
    units: list[dict[str, Any]] = []
    for seg in parse_speaker_segments(text):
        sp = str(seg.get("speaker") or "")
        units.append(
            {
                "kind": "speaker" if sp and sp != "unknown" else "plain",
                "speaker": sp,
                "text": str(seg.get("text") or ""),
                "start_ms": int(seg.get("start_ms") or 0),
                "end_ms": int(seg.get("end_ms") or 0),
            }
        )
    return units
