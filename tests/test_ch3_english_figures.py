import re
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "book-en" / "chapter3.md"
IMAGE_DIR = ROOT / "book-en" / "images"

EXPECTED_ANCHORS = {
    1: ("User Memory (Individual Scale)", "Knowledge Base (Group Scale)"),
    2: ("Simple Notes", "Advanced JSON Cards"),
    3: ("v2 (2025 paper)", "v3 (April 2026)"),
    4: ("Working Memory", "Procedural"),
    5: ("① User Query", "④ Generate"),
    6: ("Word2Vec", "BGE-M3"),
    7: ("Layer 2 (sparse · long-range connections)", "O(log N) query complexity"),
    8: ("Term frequency saturation (TF)", "Length normalization (b)"),
    9: ("Dense retrieval", "Sparse retrieval (BM25)", "Neural\nRe-ranking"),
    10: ("Global Summary", "Bottom-up Recursive Abstraction"),
    11: ("My Dentist", "Multi-hop reasoning"),
    12: ("Non-agentic RAG", "Agentic RAG"),
    13: ("Agent (ReAct Loop)", "Knowledge Base Backend (Switchable)"),
    14: ("Traditional chunking (no context)", "Context-aware chunking"),
    15: ("Phase 1: Knowledge Extraction and Structuring", "Phase 2: Factor Analysis and Knowledge Modeling"),
}


def svg_text(path: Path) -> str:
    root = ElementTree.parse(path).getroot()
    return "\n".join(text.strip() for text in root.itertext() if text.strip())


def test_chapter_3_references_each_numbered_figure_once():
    markdown = CHAPTER.read_text(encoding="utf-8")
    references = [
        int(number)
        for number in re.findall(r"images/fig3-(\d+)\.svg", markdown)
    ]

    assert references == list(range(1, 16))


def test_chapter_3_english_figures_match_their_captions():
    for number, anchors in EXPECTED_ANCHORS.items():
        text = svg_text(IMAGE_DIR / f"fig3-{number}.svg")
        for anchor in anchors:
            assert anchor in text, f"Figure 3-{number} is missing {anchor!r}"
